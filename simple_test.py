# simple_test.py

from src.embeddings.embedding_model import EmbeddingModel
from src.clustering.cluster_evolution import cosine_similarity

embedding_model = EmbeddingModel()

texts1 = [
    "AI data centers consume massive electricity",
    "Machine learning requires powerful GPUs"
]

texts2 = [
    "Deep learning models use enormous power",
    "Neural networks need high-performance computing"
]

emb1 = [embedding_model.embed(t) for t in texts1]
emb2 = [embedding_model.embed(t) for t in texts2]

from src.clustering.cluster_evolution import compute_centroid
centroid1 = compute_centroid(emb1)
centroid2 = compute_centroid(emb2)

sim = cosine_similarity(centroid1, centroid2)
print(f"Similarity between centroids: {sim:.3f}")

# Test individual similarities
for i, e1 in enumerate(emb1):
    for j, e2 in enumerate(emb2):
        sim = cosine_similarity(e1, e2)
        print(f"Similarity between '{texts1[i][:30]}...' and '{texts2[j][:30]}...': {sim:.3f}")