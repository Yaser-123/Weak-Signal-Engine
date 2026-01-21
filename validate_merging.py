# validate_merging.py

"""
Validation test for temporal weak-signal accumulation.
This test uses mock embeddings to demonstrate that the merging logic works.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.clustering.cluster_evolution import evolve_clusters, compute_centroid, cosine_similarity
import numpy as np

def create_mock_cluster(signals, cluster_id="test"):
    """Create a mock cluster with mock embeddings"""
    # Create mock embeddings - similar signals have similar vectors
    embeddings = []
    for i, signal in enumerate(signals):
        # Create embeddings that are similar for similar topics
        base_vector = np.random.rand(10)  # Small dimension for testing
        # Add some topic-specific offset
        if "AI" in signal["text"] or "machine learning" in signal["text"].lower():
            base_vector += np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        elif "power" in signal["text"].lower() or "electricity" in signal["text"].lower():
            base_vector += np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
        elif "GPU" in signal["text"] or "compute" in signal["text"].lower():
            base_vector += np.array([0, 0, 1, 0, 0, 0, 0, 0, 0, 0])

        # Normalize
        base_vector = base_vector / np.linalg.norm(base_vector)
        embeddings.append(base_vector.tolist())

    centroid = compute_centroid(embeddings)

    return {
        "cluster_id": cluster_id,
        "signals": signals,
        "embeddings": embeddings,
        "centroid": centroid,
        "signal_count": len(signals)
    }

def mock_embedding_model():
    """Mock embedding model that returns the mock embeddings"""
    return None  # Not used in this test

def test_temporal_accumulation():
    """Test that simulates Day 1 and Day 2 with similar topics"""

    print("=== Testing Temporal Weak-Signal Accumulation ===\n")

    # Day 1: Initial signals about AI power consumption
    day1_signals = [
        {
            "signal_id": "day1_1",
            "text": "AI data centers consume massive electricity",
            "timestamp": "2026-01-20T10:00:00",
            "source": "test",
            "domain": "test",
            "subdomain": "test",
            "metadata": {}
        },
        {
            "signal_id": "day1_2",
            "text": "Machine learning requires powerful GPUs",
            "timestamp": "2026-01-20T10:00:00",
            "source": "test",
            "domain": "test",
            "subdomain": "test",
            "metadata": {}
        }
    ]

    # Day 2: Similar signals (should merge)
    day2_signals = [
        {
            "signal_id": "day2_1",
            "text": "Deep learning models use enormous power",
            "timestamp": "2026-01-21T10:00:00",
            "source": "test",
            "domain": "test",
            "subdomain": "test",
            "metadata": {}
        },
        {
            "signal_id": "day2_2",
            "text": "Neural networks need high-performance computing",
            "timestamp": "2026-01-21T10:00:00",
            "source": "test",
            "domain": "test",
            "subdomain": "test",
            "metadata": {}
        }
    ]

    # Day 3: More similar signals (should merge into the same cluster)
    day3_signals = [
        {
            "signal_id": "day3_1",
            "text": "Large language models consume electricity like cities",
            "timestamp": "2026-01-22T10:00:00",
            "source": "test",
            "domain": "test",
            "subdomain": "test",
            "metadata": {}
        }
    ]

    # Start with empty candidates
    candidates = []

    print("Day 1: Processing initial signals...")
    day1_cluster = create_mock_cluster(day1_signals, "day1_batch")
    candidates = evolve_clusters(
        existing_candidates=candidates,
        new_batch_clusters=[day1_cluster],
        embedding_model=mock_embedding_model(),
        similarity_threshold=0.40
    )
    print(f"Result: {len(candidates)} candidates, total signals: {sum(c['signal_count'] for c in candidates)}")

    print("\nDay 2: Processing similar signals...")
    day2_cluster = create_mock_cluster(day2_signals, "day2_batch")
    candidates = evolve_clusters(
        existing_candidates=candidates,
        new_batch_clusters=[day2_cluster],
        embedding_model=mock_embedding_model(),
        similarity_threshold=0.40
    )
    print(f"Result: {len(candidates)} candidates, total signals: {sum(c['signal_count'] for c in candidates)}")

    print("\nDay 3: Processing more similar signals...")
    day3_cluster = create_mock_cluster(day3_signals, "day3_batch")
    candidates = evolve_clusters(
        existing_candidates=candidates,
        new_batch_clusters=[day3_cluster],
        embedding_model=mock_embedding_model(),
        similarity_threshold=0.40
    )
    print(f"Result: {len(candidates)} candidates, total signals: {sum(c['signal_count'] for c in candidates)}")

    # Validation
    print("\n=== VALIDATION ===")
    total_signals = sum(c['signal_count'] for c in candidates)
    expected_signals = len(day1_signals) + len(day2_signals) + len(day3_signals)

    print(f"Total signals accumulated: {total_signals}")
    print(f"Expected signals: {expected_signals}")
    print(f"All signals preserved: {'✓' if total_signals == expected_signals else '✗'}")

    print(f"Number of clusters: {len(candidates)}")
    if len(candidates) == 1:
        print("✓ SUCCESS: All signals merged into one cluster (temporal accumulation working)")
        return True
    else:
        print("✗ FAILED: Signals not merged properly")
        return False

if __name__ == "__main__":
    success = test_temporal_accumulation()
    if success:
        print("\n🎉 Temporal accumulation logic is working correctly!")
    else:
        print("\n❌ Need to debug the merging logic further.")