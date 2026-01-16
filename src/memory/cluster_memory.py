# src/memory/cluster_memory.py

from typing import Dict, Any, List
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from src.embeddings.embedding_model import EmbeddingModel


class ClusterMemory:
    def __init__(self, collection_name: str, vector_size: int):
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name

        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

    def upsert_cluster(
        self,
        proto_cluster: Dict[str, Any],
        embedding_model: EmbeddingModel
    ):
        texts = [s["text"] for s in proto_cluster["signals"]]
        combined_text = " ".join(texts)

        vector = embedding_model.embed(combined_text)

        point = PointStruct(
            id=proto_cluster["cluster_id"],
            vector=vector,
            payload={
                "signal_count": proto_cluster["signal_count"],
                "created_at": proto_cluster["created_at"]
            }
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )