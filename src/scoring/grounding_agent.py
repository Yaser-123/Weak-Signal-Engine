# src/scoring/grounding_agent.py

from typing import Dict, Any, List
import numpy as np


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def compute_cluster_grounding(cluster: Dict[str, Any], recent_days: int = 30) -> Dict[str, Any]:
    """
    Generate evidence-based explanation for why a cluster is meaningful.
    
    Computes:
    1. Signal Count - number of signals in cluster
    2. Recency % - percentage of signals from recent period
    3. Source Diversity - unique RSS sources contributing
    4. Semantic Coherence - how tightly signals belong together
    
    Args:
        cluster: Cluster dict with signals, embeddings, centroid, growth_ratio
        recent_days: Time window for recency calculation (default: 30)
    
    Returns:
        Dict with signal_count, recency_pct, source_diversity, coherence, explanation
    """
    
    # 1. Signal Count
    signal_count = cluster.get("signal_count", len(cluster.get("signals", [])))
    
    # 2. Recency % (from growth_ratio if available)
    # growth_ratio = recent_count / total_count, so multiply by 100 for percentage
    growth_ratio = cluster.get("growth_ratio", 0.0)
    recency_pct = round(growth_ratio * 100, 1)
    
    # 3. Source Diversity - count unique sources
    signals = cluster.get("signals", [])
    unique_sources = set()
    for signal in signals:
        source = signal.get("source", "unknown")
        unique_sources.add(source)
    source_diversity = len(unique_sources)
    
    # 4. Semantic Coherence - average cosine similarity to centroid
    embeddings = cluster.get("embeddings", [])
    centroid = cluster.get("centroid")
    
    # Compute centroid if missing but embeddings are available
    if not centroid and embeddings:
        centroid = np.mean(np.array(embeddings), axis=0).tolist()
    
    coherence = 0.0
    if centroid and embeddings and len(embeddings) > 0:
        try:
            similarities = []
            for embedding in embeddings:
                sim = cosine_similarity(embedding, centroid)
                similarities.append(sim)
            
            # Average similarity to centroid
            coherence = round(np.mean(similarities), 2) if similarities else 0.0
        except Exception as e:
            # If coherence computation fails, log and default to 0.0
            print(f"[WARNING] Coherence computation failed for cluster {cluster.get('cluster_id', 'unknown')}: {e}")
            coherence = 0.0
    
    # Generate compact explanation string
    explanation = f"{signal_count} signals | {recency_pct:.0f}% recent | {source_diversity} sources | coherence {coherence:.2f}"
    
    return {
        "signal_count": signal_count,
        "recency_pct": recency_pct,
        "source_diversity": source_diversity,
        "coherence": coherence,
        "explanation": explanation
    }
