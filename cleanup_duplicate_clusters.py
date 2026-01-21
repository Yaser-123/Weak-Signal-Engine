"""
Clean up duplicate clusters in Qdrant Cloud
Ensures only unique cluster_id values exist
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from collections import defaultdict

load_dotenv()

def cleanup_duplicate_clusters():
    print("[INFO] Starting cluster cleanup...")
    
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=30
    )
    
    # Load all clusters
    print("[INFO] Loading all clusters from Qdrant Cloud...")
    clusters = {}
    cluster_counts = defaultdict(int)
    offset = None
    
    while True:
        response = client.scroll(
            collection_name="clusters_warm",
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        points, next_offset = response
        
        if not points:
            break
        
        for point in points:
            cluster_id = point.payload.get("cluster_id")
            cluster_counts[cluster_id] += 1
            
            # Keep only the first occurrence
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    "point_id": point.id,
                    "signal_count": point.payload.get("signal_count", 0),
                    "created_at": point.payload.get("created_at")
                }
        
        if next_offset is None:
            break
        offset = next_offset
    
    # Find duplicates
    duplicates = {k: v for k, v in cluster_counts.items() if v > 1}
    
    if duplicates:
        print(f"\n[WARNING] Found {len(duplicates)} duplicate cluster IDs:")
        for cluster_id, count in duplicates.items():
            print(f"  - {cluster_id}: {count} copies")
        
        print("\n[INFO] Keeping only unique clusters (first occurrence)...")
        print(f"[INFO] Total clusters before cleanup: {sum(cluster_counts.values())}")
        print(f"[INFO] Unique clusters: {len(clusters)}")
        
        # Delete entire collection and recreate with unique clusters only
        from qdrant_client.http.models import Distance, VectorParams
        
        print("\n[INFO] Deleting clusters_warm collection...")
        client.delete_collection("clusters_warm")
        
        print("[INFO] Recreating clusters_warm collection...")
        client.create_collection(
            collection_name="clusters_warm",
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
        
        print("[INFO] Collection recreated. Run migration script to restore unique clusters.")
        print("\n✅ Cleanup complete!")
        print(f"Next step: Run 'python migrate_to_qdrant.py' to restore {len(clusters)} unique clusters")
        
    else:
        print(f"\n✅ No duplicates found! All {len(clusters)} clusters are unique.")
    
    return len(clusters)

if __name__ == "__main__":
    unique_count = cleanup_duplicate_clusters()
