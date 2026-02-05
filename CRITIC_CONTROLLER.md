# Critic + Controller Agents - Autonomous Cluster Evaluation

## Overview

The **Critic Agent + Controller Agent** system provides autonomous evaluation and promotion of clusters based on evidence quality. This creates a self-regulating pipeline that only promotes high-confidence clusters while allowing lower-quality clusters to evolve over time.

---

## Architecture

```
Candidate Clusters
       ↓
   🧪 CRITIC AGENT
   (Evaluates Quality)
       ↓
   Confidence Level + Flags
       ↓
   🤖 CONTROLLER AGENT
   (Makes Decision)
       ↓
   ┌─────────────┬──────────────────┬────────────────┐
   ↓             ↓                  ↓                ↓
PROMOTE      KEEP CANDIDATE    DEMOTE/WAIT    Decision Trace
(Active)     (Tracking)        (Cold Memory)  (Explanation)
```

---

## Agent 1: Critic Agent

**File:** `src/scoring/critic_agent.py`

### Function Signature

```python
def evaluate_cluster(cluster: dict) -> dict
```

### Evaluates

1. **Signal Count** - Evidence breadth
2. **Source Diversity** - Cross-domain validation
3. **Semantic Coherence** - Cluster tightness

### Confidence Levels

| Level | Criteria | Meaning |
|-------|----------|---------|
| **HIGH** | count ≥5, coherence ≥0.70, sources ≥2 | Ready for promotion |
| **MEDIUM** | count ≥3, moderate coherence | Keep tracking |
| **LOW** | coherence <0.55 OR single-source OR <3 signals | Wait for more evidence |

### Flags Generated

- `"high coherence"` - Coherence ≥ 0.80
- `"low coherence"` - Coherence < 0.55
- `"single source"` - Only 1 RSS feed
- `"multi-source validated"` - ≥3 sources
- `"insufficient evidence"` - <3 signals
- `"strong evidence"` - ≥10 signals

### Output Format

```python
{
    "confidence": "high" | "medium" | "low",
    "flags": ["high coherence", "multi-source validated"],
    "recommended_action": "promote" | "keep_candidate" | "demote_wait",
    "metrics": {
        "signal_count": 5,
        "source_diversity": 2,
        "coherence": 0.95
    }
}
```

---

## Agent 2: Controller Agent

**File:** `src/scoring/controller_agent.py`

### Function Signature

```python
def controller_decide(cluster: dict, critic_report: dict) -> dict
```

### Decision Policy

```python
if confidence == "high":
    action = "promote"
    # → Move to active clusters (warm memory)

elif confidence == "medium":
    action = "keep_candidate"
    # → Keep in candidate pool (tracking)

else:  # low
    action = "demote_wait"
    # → Store in cold memory, wait for future evidence
```

### Decision Traces

**High Confidence:**
```
"High confidence → Promoted to active (5 signals, 2 sources, coherence 0.95)"
```

**Medium Confidence:**
```
"Medium confidence → Kept as candidate (tracking for future promotion)"
```

**Low Confidence:**
```
"Low confidence → Demoted to wait state (low coherence 0.51)"
"Low confidence → Demoted to wait state (single source only)"
"Low confidence → Demoted to wait state (only 2 signals)"
```

### Output Format

```python
{
    "final_action": "promote" | "keep_candidate" | "demote_wait",
    "decision_trace": "High confidence → Promoted to active (...)",
    "confidence": "high",
    "flags": ["high coherence"]
}
```

---

## Pipeline Integration

### main.py Changes

**Old Logic:**
```python
# Simple threshold-based promotion
ACTIVE_MIN = 3
active_clusters = [c for c in candidates if c["signal_count"] >= ACTIVE_MIN]
```

**New Logic:**
```python
# Critic + Controller evaluation
for cluster in candidate_clusters:
    critic_report = evaluate_cluster(cluster)
    controller_decision = controller_decide(cluster, critic_report)
    
    cluster["critic_report"] = critic_report
    cluster["controller_decision"] = controller_decision
    
    if controller_decision["final_action"] == "promote":
        promoted_clusters.append(cluster)
    elif controller_decision["final_action"] == "keep_candidate":
        candidate_pool.append(cluster)
    else:  # demote_wait
        demoted_clusters.append(cluster)

active_clusters = promoted_clusters
```

### Output Example

```
[INFO] Critic+Controller Results:
  - Promoted to Active: 7
  - Kept as Candidates: 12
  - Demoted (waiting): 5
```

---

## UI Integration (app.py)

### Display Format

```
### 📈 AI Energy Independence: Labs Building Private Power Grids

🧠 Grounding: 9 signals | 78% recent | 3 sources | coherence 0.95

🧪 Critic: 🟢 High | Flags: high coherence, multi-source validated
🤖 Controller: High confidence → Promoted to active (9 signals, 3 sources, coherence 0.95)

Size: 9 | Emergence: rapid | Growth: 0.78
```

### Confidence Badges

- **🟢 High** - Green badge
- **🟡 Medium** - Yellow badge
- **🔴 Low** - Red badge

---

## Autonomous Behavior

### Self-Regulation

The system autonomously decides cluster promotion without manual intervention:

1. **Evidence Accumulation** - Low-quality clusters stored in cold memory
2. **Temporal Evolution** - Future ingestion runs may add more signals
3. **Re-Evaluation** - Controller re-assesses clusters each run
4. **Automatic Promotion** - Once criteria met, cluster auto-promotes

### No Runtime Expansion

**Constraints Respected:**
- ❌ No runtime Qdrant expansion
- ❌ No global reclustering
- ❌ No re-embedding
- ✅ Uses pre-computed embeddings
- ✅ Uses existing metrics (grounding agent)
- ✅ Deployment-safe decisions

---

## Testing

**Test File:** `test_critic_controller.py`

### Test Coverage

1. ✅ **High Confidence** → Promote (5 signals, 2 sources, coherence 1.00)
2. ✅ **Medium Confidence** → Keep candidate (3 signals, coherence 0.99)
3. ✅ **Low Coherence** → Demote (coherence 0.51)
4. ✅ **Single Source** → Demote (only 1 feed)
5. ✅ **Insufficient Evidence** → Demote (only 2 signals)

### Run Tests

```bash
python test_critic_controller.py
```

### Expected Output

```
🎉 ALL TESTS PASSED!

Summary:
✅ HIGH confidence → promote to active
✅ MEDIUM confidence → keep as candidate
✅ LOW confidence (coherence) → demote, wait for evidence
✅ LOW confidence (single source) → demote, wait for evidence
✅ LOW confidence (insufficient signals) → demote, wait for evidence
```

---

## Decision Examples

### Example 1: High Confidence Cluster

**Input:**
- 8 signals
- 3 sources (arxiv, semianalysis, datacenterdynamics)
- Coherence: 0.92

**Critic Output:**
```python
{
    "confidence": "high",
    "flags": ["high coherence", "multi-source validated", "strong evidence"],
    "recommended_action": "promote"
}
```

**Controller Decision:**
```python
{
    "final_action": "promote",
    "decision_trace": "High confidence → Promoted to active (8 signals, 3 sources, coherence 0.92)"
}
```

**Result:** ✅ Cluster promoted to active feed

---

### Example 2: Medium Confidence Cluster

**Input:**
- 4 signals
- 2 sources
- Coherence: 0.75

**Critic Output:**
```python
{
    "confidence": "medium",
    "flags": [],
    "recommended_action": "keep_candidate"
}
```

**Controller Decision:**
```python
{
    "final_action": "keep_candidate",
    "decision_trace": "Medium confidence → Kept as candidate (tracking for future promotion)"
}
```

**Result:** 📊 Kept as candidate, waits for more signals

---

### Example 3: Low Confidence (Poor Coherence)

**Input:**
- 6 signals
- 2 sources
- Coherence: 0.48

**Critic Output:**
```python
{
    "confidence": "low",
    "flags": ["low coherence"],
    "recommended_action": "demote_wait"
}
```

**Controller Decision:**
```python
{
    "final_action": "demote_wait",
    "decision_trace": "Low confidence → Demoted to wait state (low coherence 0.48)"
}
```

**Result:** ❌ Demoted to cold storage, signals may be loosely related

---

## Multi-Agent System Update

The system now has **11 agents**:

| # | Agent | Role |
|---|-------|------|
| 1 | Ingestion | Fetch RSS data |
| 2 | Embedding | Vectorize text |
| 3 | Memory | Persist to Qdrant |
| 4 | Clustering | Group signals |
| 5 | Temporal Reasoning | Merge historical clusters |
| 6 | Emergence Scoring | Classify growth |
| 7 | Search | Hybrid retrieval |
| 8 | Explainer | LLM summaries |
| 9 | Grounding | Evidence metrics |
| **10** | **Critic** | **Evaluate quality** |
| **11** | **Controller** | **Make decisions** |

---

## Advantages

### 1. Autonomous Operation
- Self-regulating cluster promotion
- No manual threshold tuning
- Adapts to evidence quality

### 2. Explainable Decisions
- Clear confidence levels
- Specific flags for issues
- Human-readable traces

### 3. Temporal Intelligence
- Low-quality clusters wait for more evidence
- Future runs may promote previously demoted clusters
- Accumulation-based validation

### 4. Production-Safe
- No runtime Qdrant queries
- No re-embedding overhead
- Deterministic decisions

### 5. Quality Control
- Prevents noise clusters in active feed
- Enforces multi-source validation
- Requires semantic coherence

---

## Future Enhancements

### 1. Adaptive Thresholds
```python
# Learn optimal thresholds from historical performance
optimal_coherence_threshold = learn_from_user_feedback()
```

### 2. Confidence Scores
```python
# Numeric confidence instead of categorical
confidence_score = 0.85  # 0.0-1.0 range
```

### 3. Multi-Criteria Ranking
```python
# Rank clusters by combined score
ranking_score = (
    0.4 * coherence +
    0.3 * (signal_count / max_count) +
    0.3 * (source_diversity / max_sources)
)
```

### 4. Feedback Loop
```python
# User marks clusters as relevant/irrelevant
# Controller adjusts criteria based on feedback
```

---

## Summary

The **Critic + Controller** system brings autonomous, evidence-based decision-making to SignalWeave:

- 🧪 **Critic** evaluates cluster quality objectively
- 🤖 **Controller** makes explainable promotion decisions
- 📊 Only high-confidence clusters promoted to active
- ⏳ Low-quality clusters wait for future evidence accumulation
- 🚀 Fully autonomous, production-safe, and explainable

This creates a self-regulating weak signal detection system that continuously improves as more evidence accumulates over time.
