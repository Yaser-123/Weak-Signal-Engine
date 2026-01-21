# src/memory/cluster_memory.py

import os
from typing import Dict, Any, List
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from src.embeddings.embedding_model import EmbeddingModel


class ClusterMemory:
    def __init__(self, collection_name: str, vector_size: int, use_cloud: bool = True):
        # Use Qdrant Cloud if credentials available, otherwise fallback to in-memory
        if use_cloud and os.getenv("QDRANT_URL") and os.getenv("QDRANT_API_KEY"):
            self.client = QdrantClient(
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY"),
            )
            print(f"[INFO] ClusterMemory connected to Qdrant Cloud")
        else:
            self.client = QdrantClient(":memory:")
            print("[INFO] ClusterMemory using in-memory mode")
        
        self.collection_name = collection_name

        # Check if collection exists, create only if needed (don't recreate!)
        try:
            self.client.get_collection(collection_name)
            print(f"[INFO] Collection '{collection_name}' already exists")
        except Exception:
            print(f"[INFO] Creating collection '{collection_name}'")
            self.client.create_collection(
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

        # Convert UUID string to integer ID for Qdrant
        import hashlib
        cluster_id_str = proto_cluster["cluster_id"]
        cluster_id_int = int(hashlib.md5(cluster_id_str.encode()).hexdigest()[:8], 16)

        point = PointStruct(
            id=cluster_id_int,  # Use hash of UUID as integer ID
            vector=vector,
            payload={
                "cluster_id": cluster_id_str,  # Keep original UUID in payload
                "signal_count": proto_cluster["signal_count"],
                "created_at": proto_cluster["created_at"],
                "member_signal_ids": [s["signal_id"] for s in proto_cluster["signals"]]
            }
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )