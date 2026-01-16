# src/clustering/contextualizer.py

from typing import Dict, Any, List

from src.ingestion.signal import Signal
from src.embeddings.embedding_model import EmbeddingModel
from src.memory.qdrant_client import QdrantMemory


def contextualize_signal(
    signal: Signal,
    embedding_model: EmbeddingModel,
    memory: QdrantMemory,
    top_k: int = 10
) -> Dict[str, Any]:
    embedding = embedding_model.embed(signal.text)

    similar_signals = memory.search_similar_signals(
        embedding=embedding,
        top_k=top_k
    )

    return {
        "signal": signal.to_dict(),
        "similar_count": len(similar_signals),
        "similar_signals": similar_signals
    }