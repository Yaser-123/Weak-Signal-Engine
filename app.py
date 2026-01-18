# app.py

import streamlit as st
from src.memory.candidate_store import load_candidates
from src.dashboard.feed import build_emerging_feed

st.set_page_config(page_title="Weak Signal Engine", layout="wide")

st.title("📡 Weak Signal Engine — Emerging Trends")

candidates = load_candidates()

if not candidates:
    st.warning("No candidate clusters found. Run main.py first.")
    st.stop()

ACTIVE_MIN = 3

active_clusters = [
    c for c in candidates if c["signal_count"] >= ACTIVE_MIN
]

candidate_clusters = [
    c for c in candidates if c["signal_count"] < ACTIVE_MIN
]

st.subheader("🔥 Active Emerging Clusters")

if active_clusters:
    feed = build_emerging_feed(active_clusters)

    for item in feed:
        with st.container():
            headline = item.get("headline", "Emerging Topic")
            st.markdown(f"### 📈 {headline}")
            st.write(
                f"**Size:** {item['signal_count']}  |  "
                f"**Emergence:** {item['emergence_level']}  |  "
                f"**Growth:** {item['growth_ratio']:.2f}"
            )
            st.divider()
else:
    st.info("No active clusters yet.")

st.subheader("🌱 Candidate Clusters (Incubating)")

with st.expander("Show candidate clusters"):
    for c in candidate_clusters:
        headline = c["signals"][0]["text"][:120] + "..."
        st.write(f"• {headline}  (size={c['signal_count']})")