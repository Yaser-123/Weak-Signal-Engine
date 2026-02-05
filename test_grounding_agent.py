# test_grounding_agent.py

"""Test the grounding agent with sample cluster data"""

from src.scoring.grounding_agent import compute_cluster_grounding
from datetime import datetime, timedelta
import numpy as np

# Create a sample cluster
def create_test_cluster():
    # Generate sample embeddings (384-dim vectors)
    np.random.seed(42)
    num_signals = 9
    embeddings = []
    
    # Create similar embeddings to simulate a coherent cluster
    base_vector = np.random.randn(384)
    for i in range(num_signals):
        # Add small noise to create similar but not identical vectors
        noise = np.random.randn(384) * 0.1
        embedding = base_vector + noise
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        embeddings.append(embedding.tolist())
    
    # Compute centroid
    centroid = np.mean(np.array(embeddings), axis=0).tolist()
    
    # Create signals with different timestamps and sources
    now = datetime.utcnow()
    signals = []
    sources = [
        "https://rss.arxiv.org/rss/cs.AI",
        "https://semianalysis.substack.com/feed",
        "https://www.datacenterdynamics.com/rss/"
    ]
    
    for i in range(num_signals):
        # Make 7 signals recent (within last 30 days)
        if i < 7:
            timestamp = now - timedelta(days=i*3)  # Recent signals
        else:
            timestamp = now - timedelta(days=45 + i*5)  # Old signals
        
        signal = {
            "signal_id": f"test_signal_{i}",
            "text": f"Test signal about emerging AI trend {i}",
            "timestamp": timestamp.isoformat(),
            "source": sources[i % 3],  # Rotate through 3 sources
            "domain": "emerging_technology",
            "subdomain": "ai"
        }
        signals.append(signal)
    
    # Create cluster
    cluster = {
        "cluster_id": "test_cluster_123",
        "signals": signals,
        "embeddings": embeddings,
        "centroid": centroid,
        "signal_count": num_signals,
        "growth_ratio": 7/9,  # 7 out of 9 signals are recent
        "created_at": (now - timedelta(days=60)).isoformat()
    }
    
    return cluster


def test_grounding_agent():
    print("=" * 60)
    print("Testing Grounding Agent")
    print("=" * 60)
    
    # Create test cluster
    cluster = create_test_cluster()
    
    print(f"\nTest Cluster:")
    print(f"  - Signals: {len(cluster['signals'])}")
    print(f"  - Growth Ratio: {cluster['growth_ratio']:.2f}")
    print(f"  - Expected Recency: {cluster['growth_ratio'] * 100:.1f}%")
    print(f"  - Sources: {len(set(s['source'] for s in cluster['signals']))}")
    
    # Compute grounding
    grounding = compute_cluster_grounding(cluster)
    
    print(f"\n🧠 Grounding Results:")
    print(f"  - Signal Count: {grounding['signal_count']}")
    print(f"  - Recency %: {grounding['recency_pct']:.1f}%")
    print(f"  - Source Diversity: {grounding['source_diversity']}")
    print(f"  - Coherence: {grounding['coherence']:.2f}")
    print(f"\n  📊 Explanation: {grounding['explanation']}")
    
    # Validate results
    print("\n" + "=" * 60)
    print("Validation:")
    print("=" * 60)
    
    assert grounding['signal_count'] == 9, "Signal count mismatch"
    assert abs(grounding['recency_pct'] - 77.8) < 1.0, "Recency % mismatch"
    assert grounding['source_diversity'] == 3, "Source diversity mismatch"
    assert 0.0 <= grounding['coherence'] <= 1.0, "Coherence out of range"
    assert grounding['coherence'] > 0.8, "Coherence should be high for similar vectors"
    
    print("✅ All validations passed!")
    print("\nExpected format:")
    print(f"  🧠 Grounding: {grounding['explanation']}")
    

if __name__ == "__main__":
    test_grounding_agent()
