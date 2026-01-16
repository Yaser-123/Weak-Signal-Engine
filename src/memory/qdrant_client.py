# src/memory/qdrant_client.py

from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from src.ingestion.signal import Signal


class QdrantMemory:
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