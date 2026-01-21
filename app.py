# app.py

import streamlit as st
from src.memory.candidate_store import load_candidates
from src.dashboard.feed import build_emerging_feed
from src.dashboard.gemini_explainer import generate_human_cluster_title, explain_cluster_with_gemini
from src.dashboard.graph import build_cluster_graph
from src.dashboard.search import search_clusters_hybrid
from src.dashboard.time_filter import compute_time_slider_bounds, filter_clusters_by_time
from src.dashboard.utils import format_signal_date
from src.embeddings.embedding_model import EmbeddingModel
from streamlit.components.v1 import html

st.set_page_config(page_title="Weak Signal Engine", layout="wide")

# Initialize embedding model (reused across search operations)
@st.cache_resource
def get_embedding_model():
    return EmbeddingModel()

embedding_model = get_embedding_model()

st.title("📡 Weak Signal Engine — Emerging Trends")

# === DYNAMIC TIME SLIDER ===
candidates = load_candidates()

# Keep original clusters for full signal display
original_candidates = candidates.copy()

if candidates:
    # Compute slider bounds from actual data
    min_days, max_days, default_days = compute_time_slider_bounds(candidates)
    
    st.subheader("⏰ Time Range Filter")
    time_range_days = st.slider(
        f"Show signals from the last X days (oldest signal: {max_days} days ago) - Default: ALL signals",
        min_value=min_days,
        max_value=max_days,
        value=default_days,
        help="Filter all clusters and graphs to show only recent signals. Default shows all historical signals for trend accumulation."
    )
    
    # Apply time filter to all candidates
    candidates = filter_clusters_by_time(candidates, time_range_days)
    
    st.caption(f"📊 Showing signals from the last **{time_range_days} days** | {len(candidates)} clusters after filtering | Default: ALL historical signals")
    st.divider()
else:
    st.warning("No clusters available. Run main.py first.")
    st.stop()

# === INTENT-BASED SEARCH ===
st.subheader("🔍 Search Emerging Signals")

col1, col2 = st.columns([4, 1])

with col1:
    search_query = st.text_input(
        "What trend are you looking for?",
        placeholder="e.g., AWS Trainium3, compute, AI power, data centers",
        key="search_input"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    search_button = st.button("🔎 Search", use_container_width=True)

# Perform search
if search_button and search_query:
    if candidates:
        with st.spinner("Searching across all clusters..."):
            results = search_clusters_hybrid(
                query=search_query,
                clusters=candidates,
                embedding_model=embedding_model,
                min_final_score=0.35
            )
        
        if results:
            st.success(f"Found {len(results)} matching clusters")
            
            for idx, result in enumerate(results):
                with st.container():
                    # Get original cluster data for full signal list
                    original_cluster = next(c for c in original_candidates if c["cluster_id"] == result["cluster_id"])
                    all_signals = original_cluster["signals"]
                    
                    # Generate title using filtered signals
                    signal_texts = [s['text'] for s in result["signals"]]
                    cluster_id = result["cluster_id"]
                    title = generate_human_cluster_title(signal_texts, cluster_id=cluster_id)
                    
                    # Cluster type badge
                    badge_color = "🔥" if result["cluster_type"] == "Active" else "🌱"
                    
                    st.markdown(f"### {badge_color} {title}")
                    
                    # Display scores in 5 columns
                    col_a, col_b, col_c, col_d, col_e = st.columns(5)
                    with col_a:
                        st.metric("Type", result["cluster_type"])
                    with col_b:
                        st.metric("Final Score", f"{result['final_score']:.2%}")
                    with col_c:
                        st.metric("Semantic", f"{result['semantic_score']:.2%}")
                    with col_d:
                        st.metric("Lexical", f"{result['lexical_score']:.2%}")
                    with col_e:
                        st.metric("Signals", result["signal_count"])
                    
                    # Expandable signal list - show ALL signals
                    with st.expander(f"View all {len(all_signals)} signals (filtered: {result['signal_count']})"):
                        for sig in all_signals:
                            st.markdown(f"• [{format_signal_date(sig['timestamp'])}] {sig['text']}")
                    
                    st.divider()
        else:
            st.info(f"No clusters found matching '{search_query}'. Try broader terms or lower the similarity threshold.")
    else:
        st.warning("No clusters available. Run main.py first.")

st.divider()

# === EXISTING CONTENT ===
# Note: candidates already filtered by time slider above

if not candidates:
    st.info(f"No clusters with signals in the last {time_range_days} days. Try increasing the time range.")
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
    
    # Pagination for active clusters
    clusters_per_page = 5
    total_pages = (len(feed) + clusters_per_page - 1) // clusters_per_page
    
    if total_pages > 1:
        col_page, col_info = st.columns([1, 3])
        with col_page:
            page = st.selectbox(
                f"Page",
                range(1, total_pages + 1),
                key="active_clusters_page"
            )
        with col_info:
            st.caption(f"📊 Showing {clusters_per_page} clusters per page | Total: {len(feed)} active clusters")
    else:
        page = 1
        st.caption(f"📊 Total: {len(feed)} active clusters")
    
    # Calculate slice
    start_idx = (page - 1) * clusters_per_page
    end_idx = min(start_idx + clusters_per_page, len(feed))
    page_feed = feed[start_idx:end_idx]
    
    if total_pages > 1:
        st.markdown(f"*Showing clusters {start_idx + 1}–{end_idx} of {len(feed)}*")

    for item in page_feed:
        with st.container():
            # Get filtered cluster data for display
            cluster_data = next(c for c in active_clusters if c["cluster_id"] == item["cluster_id"])
            
            # Get original cluster data for full signal list
            original_cluster = next(c for c in original_candidates if c["cluster_id"] == item["cluster_id"])
            all_signals = original_cluster["signals"]
            
            # Use filtered signals for title generation (recent signals are more representative)
            signal_texts = [s['text'] for s in cluster_data["signals"]]
            
            # Use cluster_id as stable cache key
            cluster_id = cluster_data["cluster_id"]
            label = generate_human_cluster_title(signal_texts, cluster_id=cluster_id)
            st.markdown(f"### 📈 {label}")

            st.write(
                f"**Size:** {item['signal_count']}  |  "
                f"**Emergence:** {item['emergence_level']}  |  "
                f"**Growth:** {item['growth_ratio']:.2f}"
            )

            # Expandable signals - show ALL signals from the cluster with pagination
            with st.expander(f"Show all {len(all_signals)} signals (filtered: {item['signal_count']})"):
                # Sort signals by recency
                sorted_signals = sorted(all_signals, key=lambda s: s['timestamp'], reverse=True)
                
                # Pagination within expander for large signal lists
                signals_per_page = 20
                total_signal_pages = (len(sorted_signals) + signals_per_page - 1) // signals_per_page
                
                if total_signal_pages > 1:
                    signal_page = st.selectbox(
                        f"Signals page (showing {signals_per_page} per page)",
                        range(1, total_signal_pages + 1),
                        key=f"signals_page_{idx}_{cluster_data['cluster_id']}"
                    )
                else:
                    signal_page = 1
                
                # Calculate signal slice
                sig_start = (signal_page - 1) * signals_per_page
                sig_end = min(sig_start + signals_per_page, len(sorted_signals))
                page_signals = sorted_signals[sig_start:sig_end]
                
                if total_signal_pages > 1:
                    st.caption(f"Showing signals {sig_start + 1}–{sig_end} of {len(sorted_signals)}")
                
                for s in page_signals:
                    st.markdown(f"• [{format_signal_date(s['timestamp'])}] {s['text']}")

            # Cluster Explainer Chat
            st.markdown("#### 💬 Ask about this cluster")
            
            # Create unique key for each cluster's chat (with index to avoid duplicates)
            chat_key = f"chat_{idx}_{cluster_data['cluster_id']}"
            question_key = f"question_{idx}_{cluster_data['cluster_id']}"
            
            # Common questions as buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Why is this emerging?", key=f"why_{idx}_{cluster_data['cluster_id']}"):
                    st.session_state[question_key] = "Why is this emerging?"
            with col2:
                if st.button("Who should care?", key=f"who_{idx}_{cluster_data['cluster_id']}"):
                    st.session_state[question_key] = "Who should care about this?"
            with col3:
                if st.button("What could happen next?", key=f"next_{idx}_{cluster_data['cluster_id']}"):
                    st.session_state[question_key] = "What could happen next?"
            
            # Custom question input
            user_question = st.text_input(
                "Or ask your own question:",
                key=question_key,
                placeholder="e.g., What are the risks?"
            )
            
            # Generate response
            if user_question:
                with st.spinner("Generating explanation..."):
                    response = explain_cluster_with_gemini(signal_texts, user_question)
                    st.info(response)

            st.divider()
else:
    st.info("No active clusters yet.")

st.subheader("🕸 Cluster Relationship Graph")

if active_clusters:
    # Legend above the graph
    st.markdown("### 📖 Graph Legend")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 4px solid #f4b000;'>
            <span style='font-size: 24px;'>🟡</span> <strong>Cluster</strong><br>
            <small style='color: #aaa;'>Emerging topic (aggregates signals)</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 4px solid #8ecae6;'>
            <span style='font-size: 24px;'>🔵</span> <strong>Signal</strong><br>
            <small style='color: #aaa;'>Individual article or research paper</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 4px solid #666;'>
            <span style='font-size: 24px;'>➖</span> <strong>Edge</strong><br>
            <small style='color: #aaa;'>Semantic similarity / evidence link</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("**💡 Tip:** Drag cluster centers to move entire groups, or drag signal dots individually to rearrange.")
    st.divider()
    
    # Add labels to clusters for graph
    for c in active_clusters:
        signal_texts = [s['text'] for s in c["signals"]]
        cluster_id = c["cluster_id"]
        c["label"] = generate_human_cluster_title(signal_texts, cluster_id=cluster_id)

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
        format_func=lambda c: f"{c['label']} ({c['signal_count']} signals)"
    )

    # Get original cluster data for full signal list
    original_cluster = next(c for c in original_candidates if c["cluster_id"] == selected_cluster["cluster_id"])
    all_signals = original_cluster["signals"]
    
    # Sort signals by recency (most recent first)
    sorted_signals = sorted(all_signals, key=lambda s: s['timestamp'], reverse=True)
    
    st.markdown(f"**{selected_cluster['label']}**")
    st.caption(f"Total signals: {len(sorted_signals)} | Shown in graph: {min(len(sorted_signals), 25)}")
    
    # Pagination for large clusters
    signals_per_page = 20
    total_pages = (len(sorted_signals) + signals_per_page - 1) // signals_per_page
    
    if total_pages > 1:
        page = st.selectbox(
            f"Page (showing {signals_per_page} signals per page)",
            range(1, total_pages + 1),
            key=f"page_{selected_cluster['cluster_id']}"
        )
    else:
        page = 1
    
    # Calculate slice
    start_idx = (page - 1) * signals_per_page
    end_idx = min(start_idx + signals_per_page, len(sorted_signals))
    page_signals = sorted_signals[start_idx:end_idx]
    
    st.markdown(f"*Showing signals {start_idx + 1}–{end_idx} of {len(sorted_signals)}*")
    
    for s in page_signals:
        st.markdown(f"**• [{format_signal_date(s['timestamp'])}] {s['text']}**")
        st.divider()
else:
    st.info("No active clusters to show details.")

st.subheader("🌱 Candidate Clusters (Incubating)")

if candidate_clusters:
    for c in candidate_clusters:
        # Get original cluster data for full signal list
        original_cluster = next(orig_c for orig_c in original_candidates if orig_c["cluster_id"] == c["cluster_id"])
        all_signals = original_cluster["signals"]
        
        # Generate label for candidate cluster using filtered signals
        signal_texts = [s['text'] for s in c["signals"]]
        cluster_id = c["cluster_id"]
        c["label"] = generate_human_cluster_title(signal_texts, cluster_id=cluster_id)
        
        with st.expander(f"{c['label']} (filtered size={c['signal_count']}, total={len(all_signals)})"):
            for s in all_signals:
                st.markdown(f"• [{format_signal_date(s['timestamp'])}] {s['text']}")
else:
    st.info("No candidate clusters yet.")