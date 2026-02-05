# Streamlit Cloud Deployment Guide

## Prerequisites
- GitHub account with SignalWeave repository
- Streamlit Cloud account (free at share.streamlit.io)
- Qdrant Cloud cluster
- Gemini API key

## Deployment Steps

### 1. Configure Secrets in Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Click on your deployed app
3. Click **Settings** → **Secrets**
4. Add the following:

```toml
QDRANT_URL = "https://your-cluster.cloud.qdrant.io"
QDRANT_API_KEY = "your-qdrant-api-key"
GEMINI_API_KEY = "your-gemini-api-key"
```

### 2. Deploy from GitHub
1. Click **New app** on Streamlit Cloud
2. Connect your GitHub repository: `Yaser-123/signalweave`
3. Select branch: `main`
4. Main file path: `app.py`
5. Click **Deploy**

### 3. Verify Deployment
- Check logs for any errors
- Ensure all 3 Qdrant collections are accessible:
  - `signals_hot`
  - `clusters_warm`
  - `cluster_titles`

## Troubleshooting

### Vector Dimension Error
If you see `Vector dimension error: expected dim: 384, got 1`:
- Delete `cluster_titles` collection in Qdrant dashboard
- Run locally: `python fix_cluster_titles.py`
- Or wait for auto-recreation with correct dimensions

### Missing Titles
If clusters show without titles:
- Run locally: `python generate_fallback_titles.py`
- This generates keyword-based titles without API quota

### UI Doesn't Match Local
- Ensure `requirements.txt` has `streamlit==1.54.0` (exact version)
- Check `.streamlit/config.toml` is committed (except secrets.toml)
- Reboot app in Streamlit Cloud dashboard

### Daily Cron Not Running
- Check GitHub Actions secrets are set:
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
  - `GEMINI_API_KEY`
- View logs at: https://github.com/Yaser-123/signalweave/actions

## Production Checklist
- ✅ requirements.txt pinned to specific versions
- ✅ .streamlit/config.toml configured
- ✅ Secrets configured in Streamlit Cloud
- ✅ GitHub Actions secrets configured
- ✅ Qdrant collections have correct vector dimensions
- ✅ Daily cron job tested and working
- ✅ Fallback titles generated for all clusters

## Performance Tips
- Use `@st.cache_resource` for embedding model (already implemented)
- Qdrant Cloud free tier: 1GB storage, sufficient for ~100k signals
- Gemini API free tier: 20 requests/day (use fallback titles for bulk)

## Support
- Streamlit Cloud docs: https://docs.streamlit.io/streamlit-community-cloud
- Qdrant docs: https://qdrant.tech/documentation/
- Gemini API: https://ai.google.dev/gemini-api/docs
