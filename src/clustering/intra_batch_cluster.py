# src/clustering/intra_batch_cluster.py

from typing import List, Dict, Any
import numpy as np


def cosine_similarity(a: List[float], b: List[float]) -> float:
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def cluster_batch(
    signals_with_embeddings: List[Dict[str, Any]],
    similarity_threshold: float = 0.80
) -> List[Dict[str, Any]]:
    """
    signals_with_embeddings = [
        {
            "signal": signal_dict,
            "embedding": embedding_vector
        }
    ]
    """

    clusters = []

    for item in signals_with_embeddings:
        placed = False

        for cluster in clusters:
            sim = cosine_similarity(
                item["embedding"],
                cluster["centroid"]
            )

            if sim >= similarity_threshold:
                cluster["signals"].append(item["signal"])

                # update centroid (mean)
                cluster["embeddings"].append(item["embedding"])
                cluster["centroid"] = np.mean(
                    cluster["embeddings"], axis=0
                ).tolist()

                placed = True
                break

        if not placed:
            clusters.append({
                "signals": [item["signal"]],
                "embeddings": [item["embedding"]],
                "centroid": item["embedding"]
            })

    return clusters
