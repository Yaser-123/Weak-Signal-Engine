# test_merging_logic.py

"""
Unit test for the cluster evolution merging logic.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.embeddings.embedding_model import EmbeddingModel
from src.clustering.cluster_evolution import evolve_clusters

def test_merging():
    """Test that similar clusters get merged"""

    embedding_model = EmbeddingModel()

    # Create existing candidate cluster
    existing_signals = [
        {
            "signal_id": "existing_1",
            "text": "AI data centers consume massive electricity",
            "timestamp": "2026-01-20T10:00:00",
            "source": "test",
            "domain": "test",
            "subdomain": "test",
            "metadata": {}
        },
        {
            "signal_id": "existing_2",
            "text": "Machine learning requires powerful GPUs",
            "timestamp": "2026-01-20T10:00:00",
            "source": "test",
            "domain": "test",
            "subdomain": "test",
            "metadata": {}
        }
    ]

    # Compute embeddings and centroid for existing cluster
    existing_embeddings = [embedding_model.embed(s["text"]) for s in existing_signals]
    from src.clustering.cluster_evolution import compute_centroid
    existing_centroid = compute_centroid(existing_embeddings)

    existing_candidates = [{
        "cluster_id": "existing_cluster_1",
        "signals": existing_signals,
        "embeddings": existing_embeddings,
        "centroid": existing_centroid,
        "signal_count": len(existing_signals),
        "created_at": "2026-01-20T10:00:00"
    }]

    # Create new batch clusters (similar topic)
    new_signals = [
        {
            "signal_id": "new_1",
            "text": "Deep learning models use enormous power",
            "timestamp": "2026-01-21T10:00:00",
            "source": "test",
            "domain": "test",
            "subdomain": "test",
            "metadata": {}
        },
        {
            "signal_id": "new_2",
            "text": "Neural networks need high-performance computing",
            "timestamp": "2026-01-21T10:00:00",
            "source": "test",
            "domain": "test",
            "subdomain": "test",
            "metadata": {}
        }
    ]

    new_embeddings = [embedding_model.embed(s["text"]) for s in new_signals]
    new_centroid = compute_centroid(new_embeddings)

    new_batch_clusters = [{
        "signals": new_signals,
        "embeddings": new_embeddings,
        "centroid": new_centroid
    }]

    print(f"Before merging: {len(existing_candidates)} existing candidates")
    print(f"New batch clusters: {len(new_batch_clusters)}")

    # Test merging with different thresholds
    for threshold in [0.3, 0.5, 0.7]:
        print(f"\nTesting with similarity threshold: {threshold}")

        # Make a copy of existing candidates for each test
        test_candidates = [dict(c) for c in existing_candidates]
        for c in test_candidates:
            c["signals"] = list(c["signals"])  # Deep copy signals
            c["embeddings"] = list(c["embeddings"])

        # Debug: Check similarity between centroids
        from src.clustering.cluster_evolution import cosine_similarity
        existing_centroid = test_candidates[0]["centroid"]
        new_centroid = new_batch_clusters[0]["centroid"]
        sim = cosine_similarity(new_centroid, existing_centroid)
        print(f"Centroid similarity: {sim:.3f}")

        result = evolve_clusters(
            existing_candidates=test_candidates,
            new_batch_clusters=new_batch_clusters,
            embedding_model=embedding_model,
            similarity_threshold=threshold
        )

        print(f"After merging: {len(result)} total candidates")
        for i, c in enumerate(result):
            print(f"  Cluster {i+1}: {c['signal_count']} signals")

        total_signals = sum(c['signal_count'] for c in result)
        expected_signals = len(existing_signals) + len(new_signals)
        print(f"Total signals: {total_signals} (expected: {expected_signals})")

        if len(result) == 1 and total_signals == expected_signals:
            print(f"✓ SUCCESS: Merging worked at threshold {threshold}")
            return True
        else:
            print(f"✗ FAILED: Merging did not work at threshold {threshold}")

    return False

if __name__ == "__main__":
    success = test_merging()
    if success:
        print("\n🎉 Merging logic is working!")
    else:
        print("\n❌ Merging logic needs fixing.")