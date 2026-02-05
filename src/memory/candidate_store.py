# src/memory/candidate_store.py

import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

CANDIDATE_STORE_FILE = "candidate_clusters.json"


def get_qdrant_client():
    """Get Qdrant Cloud client if credentials available, otherwise fallback to JSON"""
    if os.getenv("QDRANT_URL") and os.getenv("QDRANT_API_KEY"):
        return QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=30
        )
    return None


def load_candidates_from_qdrant() -> List[Dict[str, Any]]:
    """Load clusters from Qdrant Cloud"""
    client = get_qdrant_client()
    if not client:
        return None
    
    try:
        # First, load all signals into memory (more efficient than individual queries)
        print("[INFO] Loading all signals from Qdrant Cloud...")
        all_signals = {}
        all_embeddings = {}
        offset = None
        
        while True:
            response = client.scroll(
                collection_name="signals_hot",
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True  # Include vectors for graph building
            )
            
            points, next_offset = response
            
            if not points:
                break
            
            for point in points:
                signal_id = point.payload.get("signal_id")
                all_signals[signal_id] = {
                    "signal_id": signal_id,
                    "text": point.payload.get("text"),
                    "timestamp": point.payload.get("timestamp"),
                    "source": point.payload.get("source"),
                    "domain": point.payload.get("domain", ""),
                    "subdomain": point.payload.get("subdomain", ""),
                    "metadata": {}
                }
                all_embeddings[signal_id] = point.vector
            
            if next_offset is None:
                break
            offset = next_offset
        
        print(f"[INFO] Loaded {len(all_signals)} signals from Qdrant Cloud")
        
        # Now load clusters
        print("[INFO] Loading clusters from Qdrant Cloud...")
        clusters = []
        seen_cluster_ids = set()  # Track seen cluster IDs to avoid duplicates
        offset = None
        
        while True:
            response = client.scroll(
                collection_name="clusters_warm",
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True  # Need vectors for centroid
            )
            
            points, next_offset = response
            
            if not points:
                break
            
            # For each cluster, fetch its signals from memory
            for point in points:
                cluster_id = point.payload.get("cluster_id")
                
                # Skip if we've already loaded this cluster (deduplication)
                if cluster_id in seen_cluster_ids:
                    continue
                seen_cluster_ids.add(cluster_id)
                
                member_signal_ids = point.payload.get("member_signal_ids", [])
                
                # Get signals and embeddings from memory
                signals = []
                embeddings = []
                for sid in member_signal_ids:
                    if sid in all_signals:
                        signals.append(all_signals[sid])
                        embeddings.append(all_embeddings[sid])
                
                cluster = {
                    "cluster_id": cluster_id,
                    "signals": signals,
                    "embeddings": embeddings,
                    "signal_count": len(signals),
                    "created_at": point.payload.get("created_at"),
                    "last_updated": point.payload.get("last_updated", point.payload.get("created_at")),
                    "centroid": point.vector,  # Load centroid vector
                    "growth_ratio": point.payload.get("growth_ratio", 1.0),
                    # Load critic and controller evaluation metadata
                    "critic_report": point.payload.get("critic_report"),
                    "controller_decision": point.payload.get("controller_decision")
                }
                clusters.append(cluster)
            
            if next_offset is None:
                break
            offset = next_offset
        
        print(f"[INFO] Loaded {len(clusters)} unique clusters from Qdrant Cloud")
        return clusters
    
    except Exception as e:
        print(f"[WARNING] Failed to load from Qdrant Cloud: {e}")
        return None


def load_candidates() -> List[Dict[str, Any]]:
    """Load clusters from Qdrant Cloud (preferred) or fallback to JSON file"""
    # Try Qdrant Cloud first
    clusters = load_candidates_from_qdrant()
    if clusters is not None:
        print(f"[INFO] Loaded {len(clusters)} clusters from Qdrant Cloud")
        return clusters
    
    # Fallback to JSON file
    if not os.path.exists(CANDIDATE_STORE_FILE):
        return []
    
    print(f"[INFO] Loaded clusters from local JSON file (fallback)")
    with open(CANDIDATE_STORE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_candidates(candidates: List[Dict[str, Any]]):
    with open(CANDIDATE_STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)