# main.py

from src.ingestion.rss_ingestor import ingest_rss_feed
from src.embeddings.embedding_model import EmbeddingModel
from src.memory.qdrant_client import QdrantMemory
from src.memory.cluster_memory import ClusterMemory
from src.clustering.contextualizer import contextualize_signal
from src.clustering.persistence import check_persistence
from src.clustering.proto_cluster import create_proto_cluster
from src.dashboard.feed import build_emerging_feed

VECTOR_SIZE = 384


def main():
    # 1) Ingest RSS (arXiv AI)
    new_signals = ingest_rss_feed(
        feed_url="https://rss.arxiv.org/rss/cs.AI",
        domain="emerging_technology",
        subdomain="ai"
    )

    print(f"[INFO] New signals ingested: {len(new_signals)}")
    if not new_signals:
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
    embeddings = [embedding_model.embed(s.text) for s in new_signals]
    signal_memory.upsert_signals(new_signals, embeddings)

    # 4) Contextualize, check persistence, build proto-clusters
    proto_clusters = []

    for signal in new_signals:
        context = contextualize_signal(
            signal=signal,
            embedding_model=embedding_model,
            memory=signal_memory,
            top_k=10
        )

        persistence = check_persistence(context, min_similar=2)

        if persistence["is_persistent"]:
            proto_cluster = create_proto_cluster(context)
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