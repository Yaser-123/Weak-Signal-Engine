"""
Generate titles for clusters that don't have them yet
"""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from src.dashboard.gemini_explainer import generate_human_cluster_title

load_dotenv()

# Get Qdrant client
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Get all cluster IDs
print("[INFO] Loading clusters...")
clusters = []
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
    for p in points:
        clusters.append({
            "cluster_id": p.id if isinstance(p.id, str) else p.payload.get("cluster_id"),
            "member_signal_ids": p.payload.get("member_signal_ids", [])
        })
    if next_offset is None:
        break
    offset = next_offset

print(f"[INFO] Found {len(clusters)} clusters")

# Get all existing title cluster_ids
print("[INFO] Loading existing titles...")
existing_titles = set()
offset = None
while True:
    response = client.scroll(
        collection_name="cluster_titles",
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False
    )
    points, next_offset = response
    if not points:
        break
    for p in points:
        cid = p.payload.get("cluster_id")
        if cid:
            existing_titles.add(cid)
    if next_offset is None:
        break
    offset = next_offset

print(f"[INFO] Found {len(existing_titles)} existing titles")

# Find clusters without titles
missing_titles = []
for cluster in clusters:
    if cluster["cluster_id"] not in existing_titles:
        missing_titles.append(cluster)

print(f"\n[INFO] {len(missing_titles)} clusters need titles")

if not missing_titles:
    print("✅ All clusters already have titles!")
else:
    # Load signals to get text
    print("[INFO] Loading signals...")
    all_signals = {}
    offset = None
    while True:
        response = client.scroll(
            collection_name="signals_hot",
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        points, next_offset = response
        if not points:
            break
        for p in points:
            all_signals[p.payload["signal_id"]] = p.payload["text"]
        if next_offset is None:
            break
        offset = next_offset
    
    print(f"[INFO] Generating {len(missing_titles)} missing titles...\n")
    
    for i, cluster in enumerate(missing_titles, 1):
        cluster_id = cluster["cluster_id"]
        signal_ids = cluster["member_signal_ids"]
        
        # Get signal texts
        signal_texts = [all_signals[sid] for sid in signal_ids if sid in all_signals]
        
        if signal_texts:
            title = generate_human_cluster_title(signal_texts, cluster_id=cluster_id, use_cache=False)
            print(f"  [{i}/{len(missing_titles)}] {cluster_id[:8]}... → {title}")
        else:
            print(f"  [{i}/{len(missing_titles)}] {cluster_id[:8]}... → [No signals found]")
    
    print(f"\n✅ Generated {len(missing_titles)} missing titles!")
