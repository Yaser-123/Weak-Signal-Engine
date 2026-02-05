# test_grounding_no_centroid.py

"""Test grounding agent when centroid is missing (should compute from embeddings)"""

from src.scoring.grounding_agent import compute_cluster_grounding
from datetime import datetime, timedelta
import numpy as np

def test_grounding_without_centroid():
    print("=" * 60)
    print("Testing Grounding Agent WITHOUT Pre-Computed Centroid")
    print("=" * 60)
    
    # Create a cluster WITHOUT centroid (like clusters from Qdrant)
    np.random.seed(42)
    num_signals = 5
    
    # Create similar embeddings
    base_vector = np.random.randn(384)
    embeddings = []
    for i in range(num_signals):
        noise = np.random.randn(384) * 0.15
        embedding = base_vector + noise
        embedding = embedding / np.linalg.norm(embedding)
        embeddings.append(embedding.tolist())
    
    now = datetime.utcnow()
    signals = []
    sources = [
        "https://rss.arxiv.org/rss/cs.AI",
        "https://semianalysis.substack.com/feed",
    ]
    
    for i in range(num_signals):
        timestamp = now - timedelta(days=i*2)
        signal = {
            "signal_id": f"test_signal_{i}",
            "text": f"Test signal {i}",
            "timestamp": timestamp.isoformat(),
            "source": sources[i % 2],
            "domain": "emerging_technology",
            "subdomain": "ai"
        }
        signals.append(signal)
    
    # Create cluster WITHOUT centroid field (simulating Qdrant load)
    cluster = {
        "cluster_id": "test_cluster_no_centroid",
        "signals": signals,
        "embeddings": embeddings,  # Has embeddings
        # NO centroid field!
        "signal_count": num_signals,
        "growth_ratio": 1.0,
        "created_at": (now - timedelta(days=30)).isoformat()
    }
    
    print(f"\nCluster Info:")
    print(f"  - Has centroid field: {'centroid' in cluster}")
    print(f"  - Has embeddings: {len(cluster.get('embeddings', []))} vectors")
    print(f"  - Signal count: {len(cluster['signals'])}")
    
    # Compute grounding (should auto-compute centroid)
    grounding = compute_cluster_grounding(cluster)
    
    print(f"\n🧠 Grounding Results:")
    print(f"  - Signal Count: {grounding['signal_count']}")
    print(f"  - Recency %: {grounding['recency_pct']:.1f}%")
    print(f"  - Source Diversity: {grounding['source_diversity']}")
    print(f"  - Coherence: {grounding['coherence']:.2f}")
    print(f"\n  📊 Explanation: {grounding['explanation']}")
    
    # Validate
    print("\n" + "=" * 60)
    print("Validation:")
    print("=" * 60)
    
    assert grounding['signal_count'] == 5, "Signal count mismatch"
    assert grounding['recency_pct'] == 100.0, "Recency % mismatch"
    assert grounding['source_diversity'] == 2, "Source diversity mismatch"
    assert grounding['coherence'] > 0.0, f"Coherence should be > 0, got {grounding['coherence']}"
    assert grounding['coherence'] <= 1.0, "Coherence out of range"
    
    print("✅ All validations passed!")
    print(f"✅ Coherence computed successfully: {grounding['coherence']:.2f}")
    print("\nThis confirms the grounding agent can compute centroid from embeddings!")

if __name__ == "__main__":
    test_grounding_without_centroid()
