# Grounding Agent - Architecture Integration

## System Flow with Grounding Agent

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION                              │
│  RSS Feeds → Ingestion Agent → Embedding Agent → Memory Agent      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CLUSTERING PIPELINE                            │
│  Clustering Agent → Temporal Reasoning → Emergence Scoring         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DASHBOARD & PRESENTATION                         │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │   Search     │   │   Active     │   │    Graph     │          │
│  │   Results    │   │  Clusters    │   │ Visualizer   │          │
│  └──────┬───────┘   └──────┬───────┘   └──────────────┘          │
│         │                  │                                       │
│         ▼                  ▼                                       │
│  ┌─────────────────────────────────────────────┐                  │
│  │        🧠 GROUNDING AGENT (NEW)             │                  │
│  │                                             │                  │
│  │  Computes:                                  │                  │
│  │  • Signal Count                             │                  │
│  │  • Recency % (from growth_ratio)           │                  │
│  │  • Source Diversity (unique RSS feeds)     │                  │
│  │  • Semantic Coherence (avg similarity)     │                  │
│  │                                             │                  │
│  │  Output: "9 signals | 78% recent |         │                  │
│  │           3 sources | coherence 0.95"      │                  │
│  └─────────────────────────────────────────────┘                  │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────┐                        │
│  │     Display to User                  │                        │
│  │  🧠 Grounding: [metrics]             │                        │
│  └──────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Multi-Agent System (Updated)

| # | Agent | Role | Output |
|---|-------|------|--------|
| 1 | Ingestion Agent | Fetch RSS data | Signal objects |
| 2 | Embedding Agent | Vectorize text | 384-dim embeddings |
| 3 | Memory Agent | Persist data | Qdrant storage |
| 4 | Clustering Agent | Group signals | Proto-clusters |
| 5 | Temporal Reasoning | Merge historical | Evolved clusters |
| 6 | Emergence Scoring | Classify growth | rapid/stable/dormant |
| 7 | Search Agent | Hybrid retrieval | Ranked results |
| 8 | Explainer Agent | LLM summaries | Human-readable titles |
| **9** | **Grounding Agent** | **Evidence metrics** | **Transparent explanations** |

## Data Flow to Grounding Agent

```
Cluster Object
├── signals: List[Dict]
│   ├── signal_id: str
│   ├── text: str
│   ├── timestamp: str
│   ├── source: str (RSS feed URL)
│   └── ...
├── embeddings: List[List[float]]  ← 384-dim vectors
├── centroid: List[float]          ← Cluster centroid
├── signal_count: int
└── growth_ratio: float            ← From emergence.py
    
    ↓
    
🧠 Grounding Agent
    
    ↓
    
Grounding Metrics
├── signal_count: int
├── recency_pct: float
├── source_diversity: int
├── coherence: float
└── explanation: str
```

## Integration Points

### 1. Search Results (`app.py` line ~103)

```python
for idx, result in enumerate(results):
    # Compute emergence for grounding
    emergence = compute_emergence(result, recent_days=30)
    result["growth_ratio"] = emergence["growth_ratio"]
    
    # ✨ NEW: Compute grounding
    grounding = compute_cluster_grounding(result)
    
    # Display
    st.markdown(f"### {badge_color} {title}")
    st.caption(f"🧠 **Grounding:** {grounding['explanation']}")
```

### 2. Active Clusters Feed (`app.py` line ~202)

```python
for idx, item in enumerate(page_feed):
    cluster_data = next(c for c in active_clusters if c["cluster_id"] == item["cluster_id"])
    
    # Add growth_ratio from feed item
    cluster_data["growth_ratio"] = item["growth_ratio"]
    
    # ✨ NEW: Compute grounding
    grounding = compute_cluster_grounding(cluster_data)
    
    # Display
    st.markdown(f"### 📈 {label}")
    st.caption(f"🧠 **Grounding:** {grounding['explanation']}")
```

## Metric Computation Flow

### 1. Signal Count
```
cluster['signal_count'] → grounding['signal_count']
```

### 2. Recency %
```
emergence.py → growth_ratio (0.0-1.0)
    ↓
grounding_agent.py → recency_pct = growth_ratio × 100
```

### 3. Source Diversity
```
cluster['signals'] → extract unique 'source' values
    ↓
set(['arxiv.org', 'semianalysis.com', 'datacenterdynamics.com'])
    ↓
len(set) → source_diversity (e.g., 3)
```

### 4. Semantic Coherence
```
cluster['embeddings'] + cluster['centroid']
    ↓
for each embedding:
    cosine_similarity(embedding, centroid)
    ↓
np.mean(similarities) → coherence (0.0-1.0)
```

## UI Presentation

### Before Grounding Agent
```
### 📈 AI Energy Independence: Labs Building Private Power Grids

Size: 9 | Emergence: rapid | Growth: 0.78

[Signal list...]
```

### After Grounding Agent
```
### 📈 AI Energy Independence: Labs Building Private Power Grids

🧠 Grounding: 9 signals | 78% recent | 3 sources | coherence 0.82

Size: 9 | Emergence: rapid | Growth: 0.78

[Signal list...]
```

## Advantages of Grounding Agent

### 1. Transparency
- Users see **why** a cluster is shown
- No black-box recommendations

### 2. Trust
- Evidence-based metrics
- Objective calculations

### 3. Quality Control
- Low coherence = potential noise
- High recency = actively emerging
- Multiple sources = cross-validated

### 4. Interpretability
- Compact one-line explanation
- Human-readable format
- No jargon

### 5. Performance
- <10ms computation
- No API calls
- Uses cached embeddings

## Comparison to Existing Components

| Component | Type | Speed | Output |
|-----------|------|-------|--------|
| Emergence Scoring | Temporal | Fast | rapid/stable/dormant |
| Grounding Agent | Evidence | Fast | Metric summary |
| Gemini Explainer | LLM | Slow | Narrative text |
| Hybrid Search | Retrieval | Fast | Ranked results |

**Grounding Agent fills the gap between:**
- ❌ Too abstract: "rapid emergence"
- ✅ Just right: "9 signals | 78% recent | 3 sources"
- ❌ Too verbose: Full LLM explanation

## Testing Coverage

```python
# test_grounding_agent.py validates:

✅ Signal count accuracy
✅ Recency % calculation (from growth_ratio)
✅ Source diversity counting
✅ Coherence range (0.0-1.0)
✅ High coherence for similar vectors
✅ Explanation string format
```

## Future Enhancement Ideas

### 1. Grounding Score
```python
grounding_score = (
    0.3 * (signal_count / max_count) +
    0.3 * (recency_pct / 100) +
    0.2 * (source_diversity / 3) +
    0.2 * coherence
)
```

### 2. Color-Coded Grounding
```python
if coherence > 0.8:
    color = "🟢"  # High quality
elif coherence > 0.6:
    color = "🟡"  # Medium quality
else:
    color = "🔴"  # Low quality

st.caption(f"{color} Grounding: {explanation}")
```

### 3. Filtering by Grounding
```python
# Sidebar filter
min_sources = st.slider("Min Sources", 1, 3, 1)
filtered = [c for c in clusters if compute_cluster_grounding(c)['source_diversity'] >= min_sources]
```

### 4. Grounding Trends
```python
# Track over time
groundings_history = []
for cluster in clusters:
    g = compute_cluster_grounding(cluster)
    groundings_history.append({
        'timestamp': now,
        'cluster_id': cluster['cluster_id'],
        'coherence': g['coherence']
    })
```

## Summary

The **Grounding Agent** enhances SignalWeave by providing:
1. ✅ Evidence-based cluster validation
2. ✅ Transparent metric explanations
3. ✅ Trust through interpretability
4. ✅ Fast, local computation

It's the **9th agent** in the Multi-Agent System, working alongside Emergence Scoring and Gemini Explainer to provide comprehensive cluster insights.
