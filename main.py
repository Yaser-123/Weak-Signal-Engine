# main.py

import uuid
from datetime import datetime, UTC
import argparse

from src.ingestion.rss_ingestor import ingest_rss_feed
from src.ingestion.signal import Signal
from src.embeddings.embedding_model import EmbeddingModel
from src.memory.qdrant_client import QdrantMemory
from src.memory.cluster_memory import ClusterMemory
from src.memory.candidate_store import load_candidates, save_candidates
from src.clustering.contextualizer import contextualize_signal
from src.clustering.persistence import check_persistence
from src.clustering.proto_cluster import create_proto_cluster
from src.clustering.intra_batch_cluster import cluster_batch
from src.clustering.cluster_evolution import evolve_clusters
from src.dashboard.feed import build_emerging_feed

VECTOR_SIZE = 384

RSS_FEEDS = [
    {
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "domain": "emerging_technology",
        "subdomain": "ai"
    },
    {
        "url": "https://semianalysis.substack.com/feed",
        "domain": "emerging_technology",
        "subdomain": "compute"
    },
    {
        "url": "https://www.datacenterdynamics.com/rss/",
        "domain": "emerging_technology",
        "subdomain": "energy"
    }
]


def main(reset_seen_ids=False):
    # Reset seen IDs if requested
    if reset_seen_ids:
        import os
        seen_ids_file = "seen_ids.json"
        if os.path.exists(seen_ids_file):
            os.remove(seen_ids_file)
            print("[INFO] Reset seen IDs - starting fresh ingestion")
        else:
            print("[INFO] No seen IDs file to reset")

    # Initialize persistent candidate clusters (load from disk)
    candidate_clusters = load_candidates()
    print(f"[INFO] Loaded candidate clusters from disk: {len(candidate_clusters)}")
    # 1) Ingest RSS from all feeds
    all_new_signals = []

    for feed in RSS_FEEDS:
        signals = ingest_rss_feed(
            feed_url=feed["url"],
            domain=feed["domain"],
            subdomain=feed["subdomain"]
        )
        all_new_signals.extend(signals)

    print(f"[INFO] Total new signals ingested: {len(all_new_signals)}")
    if not all_new_signals:
        print("[INFO] No new data. Exiting.")
        return

    # 2) Initialize models & memory
    embedding_model = EmbeddingModel()
    signal_memory = QdrantMemory(
        collection_name="signals_hot",
        vector_size=VECTOR_SIZE
    )
    cluster_memory = ClusterMemory(
        collection_name="clusters_warm",
        vector_size=VECTOR_SIZE
    )

    # 3) Collect embeddings with signals
    signals_with_embeddings = []

    for signal in all_new_signals:
        embedding = embedding_model.embed(signal.text)
        signals_with_embeddings.append({
            "signal": signal.to_dict(),
            "embedding": embedding
        })

    # 4) Store signals in memory
    embeddings = [item["embedding"] for item in signals_with_embeddings]
    signal_memory.upsert_signals(all_new_signals, embeddings)

    # 5) Run intra-batch clustering (STAGE 1: Loose semantic grouping)
    batch_clusters = cluster_batch(
        signals_with_embeddings,
        similarity_threshold=0.45
    )

    # 6) Evolve candidate clusters (merge new batch clusters into existing candidates)
    candidate_clusters = evolve_clusters(
        existing_candidates=candidate_clusters,
        new_batch_clusters=batch_clusters,
        embedding_model=embedding_model,
        similarity_threshold=0.70
    )

    print(f"[INFO] Total candidate clusters: {len(candidate_clusters)}")

    # 7) Split candidate vs active (same logic as before)
    ACTIVE_MIN = 3

    quiet_candidates = [
        c for c in candidate_clusters if c["signal_count"] < ACTIVE_MIN
    ]

    active_clusters = [
        c for c in candidate_clusters if c["signal_count"] >= ACTIVE_MIN
    ]

    print(f"[INFO] Quiet candidates (1-2 signals, stored quietly): {len(quiet_candidates)}")
    print(f"[INFO] Active clusters (≥3 signals, shown in feed): {len(active_clusters)}")

    # Store active clusters in warm memory
    for active_cluster in active_clusters:
        cluster_memory.upsert_cluster(
            proto_cluster=active_cluster,
            embedding_model=embedding_model
        )

    # Save candidate clusters to disk (cold memory)
    save_candidates(candidate_clusters)
    print(f"[INFO] Saved candidate clusters to disk: {len(candidate_clusters)}")

    if not active_clusters:
        print("[INFO] No active clusters yet (all are embryonic with <3 signals).")
        return

    # 8) Build Emerging Feed (only from active clusters)
    feed = build_emerging_feed(active_clusters, recent_days=30)

    print("\n=== EMERGING CLUSTERS FEED ===")
    for item in feed:
        print(f"📈 {item['representative_title']}...")
        print(f"   Size: {item['signal_count']} | Level: {item['emergence_level']} | Growth: {item['growth_ratio']:.2f}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weak Signal Engine - Emerging Technology Feed")
    parser.add_argument("--reset", action="store_true", help="Reset seen IDs and start fresh ingestion")
    args = parser.parse_args()

    main(reset_seen_ids=args.reset)