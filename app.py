# app.py

import streamlit as st
from src.memory.candidate_store import load_candidates
from src.dashboard.feed import build_emerging_feed
from src.dashboard.labeler import generate_cluster_label
from src.dashboard.graph import build_cluster_graph
from streamlit.components.v1 import html

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
            # Generate meaningful cluster label
            cluster_data = next(c for c in active_clusters if c["cluster_id"] == item["cluster_id"])
            label = generate_cluster_label(cluster_data["signals"])
            st.markdown(f"### 📈 {label}")

            st.write(
                f"**Size:** {item['signal_count']}  |  "
                f"**Emergence:** {item['emergence_level']}  |  "
                f"**Growth:** {item['growth_ratio']:.2f}"
            )

            # Expandable signals
            with st.expander(f"Show {item['signal_count']} signals"):
                for s in cluster_data["signals"]:
                    st.markdown(f"- {s['text']}")

            st.divider()
else:
    st.info("No active clusters yet.")

st.subheader("🕸 Cluster Relationship Graph")

if active_clusters:
    # Add labels to clusters for graph
    for c in active_clusters:
        c["label"] = generate_cluster_label(c["signals"])

    # Build and display graph
    build_cluster_graph(active_clusters)
    html(open("cluster_graph.html").read(), height=650)
else:
    st.info("Need active clusters to show relationships.")

st.subheader("📄 Cluster Details")

if active_clusters:
    selected_cluster = st.selectbox(
        "Select a cluster to view full signals",
        active_clusters,
        format_func=lambda c: c["label"]
    )

    st.markdown(f"**{selected_cluster['label']}** ({selected_cluster['signal_count']} signals)")

    for s in selected_cluster["signals"]:
        st.markdown(f"**• {s['text']}**")
        st.divider()
else:
    st.info("No active clusters to show details.")

st.subheader("🌱 Candidate Clusters (Incubating)")

if candidate_clusters:
    for c in candidate_clusters:
        # Generate label for candidate cluster
        c["label"] = generate_cluster_label(c["signals"])
        
        with st.expander(f"{c['label']} (size={c['signal_count']})"):
            for s in c["signals"]:
                st.markdown(f"- {s['text']}")
else:
    st.info("No candidate clusters yet.")