# Deployment Guide - GitHub Actions & Streamlit Cloud

## ✅ Code Successfully Pushed to GitHub!

### 📋 Next Steps for Full Deployment:

## 1️⃣ Set up GitHub Secrets (for Cron Job)

Navigate to your repository on GitHub:
- Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Add these 3 secrets:

**Secret 1: QDRANT_URL**
```
https://a19898e3-ff5c-4b2f-a43a-e3517f561147.europe-west3-0.gcp.cloud.qdrant.io:6333
```

**Secret 2: QDRANT_API_KEY**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.sP3jMqdJ8jf8gj0AgfdmsUnAk8AjeoavwSMHc9EHiMY
```

**Secret 3: GEMINI_API_KEY**
```
AIzaSyCqLH2mS4h0O4T02B1nGdHHoK0oORAlFe8
```

✅ Cron job will now run daily at 12:00 PM UTC!

---

## 2️⃣ Deploy to Streamlit Cloud (Optional)

1. **Sign up**: https://share.streamlit.io/
2. **Connect repository**: Link your GitHub repo
3. **Set main file**: `app.py`
4. **Add Secrets** (Settings → Secrets):
   ```toml
   QDRANT_URL = "https://a19898e3-ff5c-4b2f-a43a-e3517f561147.europe-west3-0.gcp.cloud.qdrant.io:6333"
   QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.sP3jMqdJ8jf8gj0AgfdmsUnAk8AjeoavwSMHc9EHiMY"
   GEMINI_API_KEY = "AIzaSyCqLH2mS4h0O4T02B1nGdHHoK0oORAlFe8"
   ```
5. **Deploy**: Click "Deploy" button

✅ Your app will be live at: `https://your-app-name.streamlit.app`

---

## 🔄 How It Works in Production

### Daily Automated Workflow:
```
12:00 PM UTC
  ↓
GitHub Actions Cron Job Triggers
  ↓
Runs: python main.py
  ↓
1. Ingests RSS feeds (arXiv, SemiAnalysis, DataCenter)
2. Creates embeddings for new signals
3. Clusters signals (intra-batch + evolution)
4. Saves to Qdrant Cloud:
   - signals_hot collection (new signals)
   - clusters_warm collection (new/updated clusters)
5. Saves backup to candidate_clusters.json
  ↓
✅ Data now available in Qdrant Cloud
  ↓
Users open Streamlit app
  ↓
App loads from Qdrant Cloud
  ↓
Title generation (only for NEW clusters)
  ↓
Cached in cluster_titles collection
```

### Cost Optimization:
- **Cron job**: 0 Gemini API calls (data ingestion only)
- **First user**: ~2-5 API calls (only for new clusters)
- **Other users**: 0 API calls (cached titles)

---

## 🎯 What's Live Now:

✅ **Data**: 758 signals + 19 clusters in Qdrant Cloud  
✅ **Cron**: Daily RSS ingestion at 12 PM UTC  
✅ **Caching**: Titles stored in cloud (shared across users)  
✅ **Fallback**: Works locally even if cloud is down  

---

## 🧪 Test the Cron Job

Manually trigger the workflow:
1. Go to: `Actions` tab in your GitHub repo
2. Click: `Automated RSS Ingestion`
3. Click: `Run workflow` → `Run workflow`

Watch the logs to see it running!

---

## 📊 Monitor Your Data

**Qdrant Cloud Dashboard**: https://cloud.qdrant.io
- View: signals_hot (758 points)
- View: clusters_warm (19 points)
- View: cluster_titles (created on-demand)

**GitHub Actions**: Check workflow runs and logs

**Streamlit App**: Test locally or on Streamlit Cloud

---

## 🎉 You're All Set!

Your Weak Signal Engine is now fully automated and cloud-enabled!
