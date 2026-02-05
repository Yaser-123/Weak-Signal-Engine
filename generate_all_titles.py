"""
Generate titles for all clusters in Qdrant Cloud
Run this after main.py to pre-populate the title cache
"""
from src.memory.candidate_store import load_candidates_from_qdrant
from src.dashboard.gemini_explainer import generate_human_cluster_title

def main():
    print("[INFO] Loading clusters from Qdrant...")
    clusters = load_candidates_from_qdrant()
    
    print(f"[INFO] Found {len(clusters)} clusters")
    print("[INFO] Generating titles (this may take a minute)...\n")
    
    for i, cluster in enumerate(clusters, 1):
        cluster_id = cluster["cluster_id"]
        signals = cluster["signals"]
        
        # Extract signal texts (limit to 1-5 signals)
        signal_texts = [s["text"] for s in signals][:5]
        
        # Generate title (will use cache if exists, otherwise calls Gemini)
        title = generate_human_cluster_title(signal_texts, cluster_id=cluster_id, use_cache=True)
        
        print(f"  [{i}/{len(clusters)}] {cluster_id[:8]}... → {title}")
    
    print("\n✅ All titles generated and cached!")

if __name__ == "__main__":
    main()
