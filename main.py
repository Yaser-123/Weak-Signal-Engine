# main.py

import uuid
from datetime import datetime, UTC

from src.ingestion.rss_ingestor import ingest_rss_feed
from src.ingestion.signal import Signal
from src.embeddings.embedding_model import EmbeddingModel
from src.memory.qdrant_client import QdrantMemory
from src.memory.cluster_memory import ClusterMemory
from src.clustering.contextualizer import contextualize_signal
from src.clustering.persistence import check_persistence
from src.clustering.proto_cluster import create_proto_cluster
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


def main():
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

    # 3) Embed & store signals
    embeddings = [embedding_model.embed(s.text) for s in all_new_signals]
    signal_memory.upsert_signals(all_new_signals, embeddings)

    # 4) Contextualize, check persistence, build proto-clusters
    proto_clusters = []
    batch_contexts = []

    for signal in all_new_signals:
        context = contextualize_signal(
            signal=signal,
            embedding_model=embedding_model,
            memory=signal_memory,
            top_k=10
        )

        persistence = check_persistence(context, min_similar=2)

        if persistence["is_persistent"]:
            batch_contexts.append(context)

    if batch_contexts:
        # Merge all contexts into ONE proto-cluster
        merged_signals = []
        seen_ids = set()
        for ctx in batch_contexts:
            signal = Signal.from_dict(ctx["signal"])
            similar_signals = [Signal.from_dict(s) for s in ctx["similar_signals"]]
            all_sigs = [signal] + similar_signals
            for sig in all_sigs:
                if sig.signal_id not in seen_ids:
                    merged_signals.append(sig)
                    seen_ids.add(sig.signal_id)

        proto_cluster = {
            "cluster_id": str(uuid.uuid4()),
            "signals": [s.to_dict() for s in merged_signals],
            "signal_count": len(merged_signals),
            "created_at": datetime.now(UTC).isoformat()
        }
        proto_clusters.append(proto_cluster)

        # 5) Store proto-cluster in warm memory
        cluster_memory.upsert_cluster(
            proto_cluster=proto_cluster,
            embedding_model=embedding_model
        )

    print(f"[INFO] Proto-clusters created: {len(proto_clusters)}")

    if not proto_clusters:
        print("[INFO] No persistent patterns yet.")
        return

    # 6) Build Emerging Feed
    feed = build_emerging_feed(proto_clusters, recent_days=30)

    print("\n=== EMERGING CLUSTERS FEED ===")
    for item in feed:
        print(item)


if __name__ == "__main__":
    main()