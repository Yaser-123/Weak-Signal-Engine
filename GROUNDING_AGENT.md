# Grounding Agent Implementation

## Overview

The **Grounding Agent** provides evidence-based explanations for why each cluster is considered meaningful in the SignalWeave system. It computes objective metrics that justify the emergence of each cluster.

---

## Architecture

**Location:** `src/scoring/grounding_agent.py`

**Purpose:** Generate transparent, explainable metrics for cluster quality and significance.

---

## Metrics Computed

### 1. **Signal Count**
- **What**: Total number of signals in the cluster
- **Why**: Larger clusters indicate broader evidence
- **Source**: `cluster['signal_count']`

### 2. **Recency Percentage**
- **What**: Percentage of signals from the last N days (default: 30)
- **Formula**: `growth_ratio × 100`
- **Why**: High recency indicates actively emerging trends
- **Range**: 0-100%
- **Interpretation**:
  - 60-100%: Rapid emergence
  - 30-59%: Stable growth
  - 0-29%: Dormant/declining

### 3. **Source Diversity**
- **What**: Number of unique RSS feeds contributing signals
- **Why**: Multiple sources indicate cross-domain validation
- **Calculation**: Count unique `signal['source']` values
- **Range**: 1-N (where N = total RSS feeds configured)
- **Interpretation**:
  - 1 source: Single-domain signal (may be noise)
  - 2+ sources: Cross-validated trend
  - 3 sources: Strong multi-domain emergence

### 4. **Semantic Coherence**
- **What**: How tightly signals belong together semantically
- **Formula**: Average cosine similarity of all signal embeddings to cluster centroid
- **Why**: High coherence means signals are truly related
- **Range**: 0.0-1.0
- **Interpretation**:
  - 0.8-1.0: Highly coherent (tight cluster)
  - 0.6-0.79: Moderately coherent
  - 0.0-0.59: Loose cluster (may need refinement)

---

## Output Format

```python
{
    "signal_count": int,
    "recency_pct": float,
    "source_diversity": int,
    "coherence": float,
    "explanation": str
}
```

### Example Output

```python
{
    "signal_count": 9,
    "recency_pct": 77.8,
    "source_diversity": 3,
    "coherence": 0.95,
    "explanation": "9 signals | 78% recent | 3 sources | coherence 0.95"
}
```

---

## Integration

### Dashboard Display

**Location:** `app.py`

**UI Format:**
```
🧠 Grounding: 9 signals | 78% recent | 3 sources | coherence 0.95
```

**Displayed in:**
1. Search results (below cluster title)
2. Active clusters feed (below cluster title)

---

## Implementation Details

### Function Signature

```python
def compute_cluster_grounding(
    cluster: Dict[str, Any], 
    recent_days: int = 30
) -> Dict[str, Any]:
```

### Requirements

**Input cluster must contain:**
- `signals`: List of signal dictionaries
- `embeddings`: List of 384-dim vectors
- `centroid`: Cluster centroid vector (384-dim)
- `signal_count`: Integer
- `growth_ratio`: Float (0.0-1.0)

**Note:** The function does NOT re-embed signals - it uses pre-computed embeddings from cluster objects.

### Dependencies

```python
import numpy as np
```

### No External API Calls

The grounding agent runs entirely locally using:
- Pre-computed embeddings
- Basic statistical calculations
- Cosine similarity computations

**Performance:** <10ms per cluster

---

## Use Cases

### 1. **Cluster Quality Assessment**
Filter low-quality clusters:
```python
grounding = compute_cluster_grounding(cluster)
if grounding['coherence'] < 0.6:
    print("Low coherence - may be noise cluster")
```

### 2. **Multi-Source Validation**
Identify cross-validated trends:
```python
if grounding['source_diversity'] >= 2:
    print("Cross-domain validation confirmed")
```

### 3. **Emergence Velocity**
Detect rapid vs dormant trends:
```python
if grounding['recency_pct'] > 60:
    print("Rapidly emerging trend")
elif grounding['recency_pct'] < 30:
    print("Dormant or declining trend")
```

### 4. **Explainable AI**
Provide transparent explanations to users:
```
Why is this cluster shown?
→ "9 signals | 78% recent | 3 sources | coherence 0.95"
```

---

## Testing

**Test File:** `test_grounding_agent.py`

**Run Tests:**
```bash
python test_grounding_agent.py
```

**Expected Output:**
```
✅ All validations passed!

Expected format:
  🧠 Grounding: 9 signals | 78% recent | 3 sources | coherence 1.00
```

---

## Design Principles

### 1. **No Hallucination**
- All metrics computed from actual data
- No LLM-generated explanations
- Deterministic calculations

### 2. **Lightweight**
- Uses pre-computed embeddings
- No re-embedding required
- Fast execution (<10ms)

### 3. **Explainable**
- Clear metric definitions
- Human-readable output
- Transparent calculations

### 4. **Grounded**
- Evidence-based (signal count, sources)
- Time-aware (recency %)
- Semantics-aware (coherence)

---

## Future Enhancements

### Potential Metrics
1. **Geographic Diversity**: Unique countries/regions
2. **Temporal Spread**: Date range of signals
3. **Domain Authority**: Source credibility scores
4. **Keyword Stability**: Consistent terminology usage
5. **Cross-Cluster Links**: Relationships to other clusters

### Configurable Thresholds
```python
GROUNDING_CONFIG = {
    "recent_days": 30,
    "min_coherence": 0.6,
    "min_sources": 2,
    "min_signals": 3
}
```

---

## Comparison to Other Components

| Component | Purpose | Type |
|-----------|---------|------|
| **Emergence Scoring** | Classify growth velocity | Temporal |
| **Grounding Agent** | Explain cluster validity | Evidence-based |
| **Gemini Explainer** | Human-readable summaries | LLM-generated |
| **Hybrid Search** | Retrieve relevant clusters | Semantic + Lexical |

**Key Difference:** Grounding Agent provides **objective, computable metrics** while Gemini Explainer provides **subjective, narrative explanations**.

---

## Production Deployment

### Performance
- ✅ No external API calls
- ✅ Uses cached embeddings
- ✅ O(n) complexity (n = signals per cluster)
- ✅ Suitable for real-time dashboard

### Monitoring
Track grounding metrics distribution:
```python
coherence_avg = np.mean([g['coherence'] for g in groundings])
source_diversity_avg = np.mean([g['source_diversity'] for g in groundings])
```

### Error Handling
```python
if not cluster.get('embeddings') or not cluster.get('centroid'):
    return {
        "signal_count": cluster.get('signal_count', 0),
        "recency_pct": 0.0,
        "source_diversity": 0,
        "coherence": 0.0,
        "explanation": "Insufficient data for grounding"
    }
```

---

## Summary

The **Grounding Agent** ensures that SignalWeave's cluster recommendations are:
1. ✅ **Evidence-based** (signal count, sources)
2. ✅ **Temporally aware** (recency %)
3. ✅ **Semantically validated** (coherence)
4. ✅ **Transparent** (explainable metrics)

This makes SignalWeave a **trustworthy weak signal detection system** rather than a black-box recommendation engine.
