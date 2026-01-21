"""
Migrate existing JSON data to Qdrant Cloud
Uploads all signals and clusters from candidate_clusters.json to Qdrant Cloud
"""

import json
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from src.embeddings.embedding_model import EmbeddingModel

# Load environment variables
load_dotenv()

def migrate_data():
    print("[INFO] Starting migration to Qdrant Cloud...")
    
    # Initialize Qdrant Cloud client
    if not os.getenv("QDRANT_URL") or not os.getenv("QDRANT_API_KEY"):
        print("[ERROR] Qdrant Cloud credentials not found in .env file")
        return
    
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=60  # Increase timeout to 60 seconds
    )
    print(f"[INFO] Connected to Qdrant Cloud: {os.getenv('QDRANT_URL')}")
    
    # Initialize embedding model
    embedding_model = EmbeddingModel()
    vector_size = 384  # all-MiniLM-L6-v2 dimension
    
    # Create collections if they don't exist
    for collection_name in ["signals_hot", "clusters_warm"]:
        try:
            existing = client.get_collection(collection_name)
            print(f"[INFO] Collection '{collection_name}' already exists with {existing.points_count} points")
        except Exception as e:
            if "Not Found" in str(e) or "not found" in str(e):
                print(f"[INFO] Creating collection '{collection_name}'")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
            else:
                print(f"[WARNING] Error checking collection '{collection_name}': {e}")
    
    # Load clusters from JSON
    print("[INFO] Loading candidate_clusters.json...")
    with open("candidate_clusters.json", "r", encoding="utf-8") as f:
        clusters = json.load(f)
    print(f"[INFO] Loaded {len(clusters)} clusters")
    
    # Migrate signals to signals_hot
    print("[INFO] Migrating signals to 'signals_hot' collection...")
    signal_batch = []
    signal_id_counter = 1
    
    for cluster in clusters:
        for signal in cluster["signals"]:
            # Generate embedding for signal text
            vector = embedding_model.embed(signal["text"])
            
            point = PointStruct(
                id=signal_id_counter,
                vector=vector,
                payload={
                    "signal_id": signal["signal_id"],
                    "text": signal["text"],
                    "timestamp": signal["timestamp"],
                    "source": signal["source"],
                    "domain": signal.get("domain", ""),
                    "subdomain": signal.get("subdomain", ""),
                    "cluster_id": cluster["cluster_id"]
                }
            )
            signal_batch.append(point)
            signal_id_counter += 1
            
            # Upload in batches of 100
            if len(signal_batch) >= 100:
                client.upsert(collection_name="signals_hot", points=signal_batch)
                print(f"[INFO] Uploaded {signal_id_counter - 1} signals...")
                signal_batch = []
    
    # Upload remaining signals
    if signal_batch:
        client.upsert(collection_name="signals_hot", points=signal_batch)
    print(f"[INFO] ✅ Migrated {signal_id_counter - 1} signals to 'signals_hot'")
    
    # Migrate clusters to clusters_warm
    print("[INFO] Migrating clusters to 'clusters_warm' collection...")
    cluster_batch = []
    
    for idx, cluster in enumerate(clusters):
        # Generate cluster centroid from all signal texts
        texts = [s["text"] for s in cluster["signals"]]
        combined_text = " ".join(texts)
        vector = embedding_model.embed(combined_text)
        
        point = PointStruct(
            id=idx + 1,
            vector=vector,
            payload={
                "cluster_id": cluster["cluster_id"],
                "signal_count": cluster["signal_count"],
                "created_at": cluster["created_at"],
                "last_updated": cluster.get("last_updated", cluster["created_at"]),
                "member_signal_ids": [s["signal_id"] for s in cluster["signals"]]
            }
        )
        cluster_batch.append(point)
    
    client.upsert(collection_name="clusters_warm", points=cluster_batch)
    print(f"[INFO] ✅ Migrated {len(clusters)} clusters to 'clusters_warm'")
    
    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETE!")
    print("="*60)
    print(f"Signals migrated: {signal_id_counter - 1}")
    print(f"Clusters migrated: {len(clusters)}")
    print("\nRefresh your Qdrant Cloud dashboard to see the data!")
    print("="*60)

if __name__ == "__main__":
    migrate_data()
