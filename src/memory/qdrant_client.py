# src/memory/qdrant_client.py

import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from src.ingestion.signal import Signal


class QdrantMemory:
    def __init__(self, collection_name: str, vector_size: int, use_cloud: bool = True):
        # Use Qdrant Cloud if credentials available, otherwise fallback to in-memory
        if use_cloud and os.getenv("QDRANT_URL") and os.getenv("QDRANT_API_KEY"):
            self.client = QdrantClient(
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY"),
            )
            print(f"[INFO] Connected to Qdrant Cloud: {os.getenv('QDRANT_URL')}")
        else:
            self.client = QdrantClient(":memory:")
            print("[INFO] Using Qdrant in-memory mode")
        
        self.collection_name = collection_name

        # Check if collection exists, create only if needed
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

    def upsert_signals(self, signals: List[Signal], embeddings: List[List[float]]):
        points = []

        for i, (signal, vector) in enumerate(zip(signals, embeddings)):
            point = PointStruct(
                id=i + 1,  # Use integer ID starting from 1
                vector=vector,
                payload=signal.to_dict()
            )
            points.append(point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search_similar_signals(
        self,
        embedding: List[float],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=top_k,
            with_payload=True
        )

        return [res.payload for res in results.points]