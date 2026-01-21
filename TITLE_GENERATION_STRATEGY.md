"""
How Title Generation Works - Cost Optimization
================================================

CRON JOB (Daily at 12 PM):
- Runs: main.py
- Does: Ingests new RSS feeds → Creates/updates clusters → Saves to Qdrant Cloud
- Does NOT: Generate titles (saves API costs!)

STREAMLIT APP (When User Opens):
- Loads clusters from Qdrant Cloud
- Checks cache in Qdrant Cloud's 'cluster_titles' collection
- Only calls Gemini API if:
  ✓ Cluster is NEW (no cached title)
  ✓ Cluster was updated (new signals added)
  
COST SAVINGS:
- No API calls during cron job (runs 365 times/year)
- API calls only when user views NEW clusters
- Titles cached forever in Qdrant Cloud
- Multi-user apps share same cache (1 API call per cluster, ever)

EXAMPLE:
Day 1: 
  - Cron ingests 10 new signals → 3 new clusters created
  - User opens app → Generates 3 titles (3 API calls)
  
Day 2:
  - Cron ingests 5 new signals → 1 existing cluster updated, 1 new cluster
  - User opens app → Generates 1 title for new cluster (1 API call)
  - Existing clusters show cached titles (0 API calls)

Day 3:
  - Cron ingests 0 new signals (no changes)
  - User opens app → All cached titles (0 API calls)
  
TOTAL: 4 API calls instead of 1095+ calls if done on every cron run!
