# app.py - Professional SaaS Dashboard

import streamlit as st
from src.memory.candidate_store import load_candidates
from src.dashboard.feed import build_emerging_feed
from src.dashboard.gemini_explainer import generate_human_cluster_title, explain_cluster_with_gemini
from src.dashboard.graph import build_cluster_graph
from src.dashboard.search import search_clusters_hybrid
from src.dashboard.time_filter import compute_time_slider_bounds, filter_clusters_by_time
from src.dashboard.utils import format_signal_date
from src.embeddings.embedding_model import EmbeddingModel
from src.scoring.grounding_agent import compute_cluster_grounding
from src.scoring.emergence import compute_emergence
from streamlit.components.v1 import html

st.set_page_config(page_title="SignalWeave", layout="wide", initial_sidebar_state="expanded")

# === CUSTOM CSS FOR PROFESSIONAL LOOK ===
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Container styling */
    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Modern font and spacing */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Background gradient */
    .stApp {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
    }
    
    /* Cluster card styling */
    .cluster-card {
        background: linear-gradient(135deg, rgba(30, 30, 46, 0.95) 0%, rgba(24, 24, 37, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .cluster-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 12px 48px rgba(99, 102, 241, 0.15);
        transform: translateY(-2px);
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    
    .badge-high {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .badge-medium {
        background: rgba(251, 191, 36, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }
    
    .badge-low {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .badge-rapid {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .badge-stable {
        background: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .badge-dormant {
        background: rgba(107, 114, 128, 0.15);
        color: #6b7280;
        border: 1px solid rgba(107, 114, 128, 0.3);
    }
    
    /* Title styling */
    .cluster-title {
        color: #f0f0f0;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 12px;
        line-height: 1.4;
    }
    
    /* Metrics row */
    .metrics-row {
        display: flex;
        gap: 12px;
        margin: 12px 0;
        flex-wrap: wrap;
    }
    
    /* Grounding info */
    .info-row {
        background: rgba(99, 102, 241, 0.08);
        border-left: 3px solid #6366f1;
        padding: 10px 14px;
        border-radius: 8px;
        margin: 8px 0;
        font-size: 13px;
        color: #d1d5db;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(24, 24, 37, 0.98) 0%, rgba(15, 15, 30, 0.98) 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Header override */
    h1, h2, h3 {
        color: #f0f0f0 !important;
    }
    
    /* Divider styling */
    hr {
        border-color: rgba(255, 255, 255, 0.1);
        margin: 24px 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
        transform: translateY(-1px);
    }
    
    /* Signal list styling */
    .signal-item {
        background: rgba(255, 255, 255, 0.03);
        border-left: 2px solid rgba(99, 102, 241, 0.5);
        padding: 12px;
        margin: 8px 0;
        border-radius: 6px;
        font-size: 14px;
        color: #d1d5db;
    }
    
    /* Graph container */
    .graph-container {
        background: linear-gradient(135deg, rgba(30, 30, 46, 0.95) 0%, rgba(24, 24, 37, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Initialize embedding model
@st.cache_resource
def get_embedding_model():
    return EmbeddingModel()

embedding_model = get_embedding_model()

# === HEADER ===
st.markdown("""
<div style='text-align: center; padding: 20px 0 40px 0;'>
    <h1 style='font-size: 48px; font-weight: 800; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px;'>
        📡 SignalWeave
    </h1>
    <p style='color: #9ca3af; font-size: 18px; font-weight: 400;'>
        Temporal Vector Memory for Emerging Trend Intelligence
    </p>
</div>
""", unsafe_allow_html=True)

# === SIDEBAR CONTROLS ===
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    st.divider()
    
    # Load candidates
    candidates = load_candidates()
    original_candidates = candidates.copy()
    
    if not candidates:
        st.error("⚠️ No clusters available. Run main.py first.")
        st.stop()
    
    # Time filter
    st.markdown("#### ⏰ Time Range")
    min_days, max_days, default_days = compute_time_slider_bounds(candidates)
    
    time_range_days = st.slider(
        "Days of history",
        min_value=min_days,
        max_value=max_days,
        value=default_days,
        help="Filter signals by recency"
    )
    
    st.caption(f"📊 {time_range_days} days | {len(candidates)} clusters")
    st.divider()
    
    # Mode toggle
    st.markdown("#### 🎯 Display Mode")
    display_mode = st.radio(
        "Filter by maturity",
        ["All Clusters", "Early Weak Signals", "Mature Trends"],
        help="Focus on different cluster stages"
    )
    
    st.divider()
    
    # Active threshold
    st.markdown("#### 🔥 Active Threshold")
    ACTIVE_MIN = st.number_input(
        "Min signals for active status",
        min_value=1,
        max_value=20,
        value=3,
        help="Clusters with fewer signals are candidates"
    )

# Apply time filter
candidates = filter_clusters_by_time(candidates, time_range_days)

if not candidates:
    st.warning(f"⚠️ No clusters in the last {time_range_days} days. Increase time range.")
    st.stop()

# === SEARCH SECTION ===
st.markdown("### 🔍 Search Emerging Signals")

col1, col2 = st.columns([5, 1])

with col1:
    search_query = st.text_input(
        "Search Clusters",
        placeholder="🔎 Search for trends... (e.g., AWS Trainium3, AI power, quantum computing)",
        key="search_input",
        label_visibility="collapsed"
    )

with col2:
    search_button = st.button("Search", use_container_width=True, type="primary")

# Perform search
if search_button and search_query:
    with st.spinner("🔍 Searching across all clusters..."):
        results = search_clusters_hybrid(
            query=search_query,
            clusters=candidates,
            embedding_model=embedding_model,
            min_final_score=0.35
        )
    
    if results:
        st.success(f"✅ Found {len(results)} matching clusters")
        
        for idx, result in enumerate(results):
            # Get original cluster for full signal list
            original_cluster = next(c for c in original_candidates if c["cluster_id"] == result["cluster_id"])
            all_signals = original_cluster["signals"]
            
            # Compute emergence
            emergence = compute_emergence(result, recent_days=30)
            result["growth_ratio"] = emergence["growth_ratio"]
            
            # Generate title
            signal_texts = [s['text'] for s in result["signals"]]
            cluster_id = result["cluster_id"]
            title = generate_human_cluster_title(signal_texts, cluster_id=cluster_id)
            
            # Grounding
            grounding = compute_cluster_grounding(result)
            
            # === CLUSTER CARD ===
            st.markdown(f"""
            <div class="cluster-card">
                <div class="cluster-title">🔎 {title}</div>
            """, unsafe_allow_html=True)
            
            # Badges row
            badge_html = f'<div class="metrics-row">'
            
            # Cluster type badge
            cluster_type = result.get("cluster_type", "Candidate")
            badge_html += f'<span class="badge badge-medium">{"🔥 Active" if cluster_type == "Active" else "🌱 Candidate"}</span>'
            
            # Emergence badge
            emergence_level = emergence.get("emergence_level", "stable")
            if emergence_level == "rapid":
                badge_html += f'<span class="badge badge-rapid">⚡ Rapid</span>'
            elif emergence_level == "stable":
                badge_html += f'<span class="badge badge-stable">📊 Stable</span>'
            else:
                badge_html += f'<span class="badge badge-dormant">😴 Dormant</span>'
            
            # Critic confidence badge
            if "critic_report" in result and result["critic_report"] is not None:
                confidence = result["critic_report"].get("confidence", "unknown")
                if confidence == "high":
                    badge_html += f'<span class="badge badge-high">🟢 High Confidence</span>'
                elif confidence == "medium":
                    badge_html += f'<span class="badge badge-medium">🟡 Medium</span>'
                else:
                    badge_html += f'<span class="badge badge-low">🔴 Low</span>'
            
            # Coherence badge
            coherence = grounding.get("coherence", 0.0)
            coherence_color = "badge-high" if coherence >= 0.70 else "badge-medium" if coherence >= 0.50 else "badge-low"
            badge_html += f'<span class="badge {coherence_color}">🎯 {coherence:.2f} coherence</span>'
            
            badge_html += '</div>'
            st.markdown(badge_html, unsafe_allow_html=True)
            
            # Grounding info
            st.markdown(f"""
            <div class="info-row">
                🧠 <strong>Grounding:</strong> {grounding['explanation']}
            </div>
            """, unsafe_allow_html=True)
            
            # Critic + Controller info
            if ("critic_report" in result and result["critic_report"] is not None and 
                "controller_decision" in result and result["controller_decision"] is not None):
                critic = result["critic_report"]
                controller = result["controller_decision"]
                flags_str = ", ".join(critic.get("flags", [])) if critic.get("flags") else "none"
                
                st.markdown(f"""
                <div class="info-row">
                    🧪 <strong>Critic:</strong> {critic.get('confidence', 'unknown')} | Flags: {flags_str}
                </div>
                <div class="info-row">
                    🤖 <strong>Controller:</strong> {controller.get('decision_trace', 'No trace')}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Metrics
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Final Score", f"{result['final_score']:.1%}")
            with col_b:
                st.metric("Semantic", f"{result['semantic_score']:.1%}")
            with col_c:
                st.metric("Lexical", f"{result['lexical_score']:.1%}")
            with col_d:
                st.metric("Signals", result["signal_count"])
            
            # View signals modal
            with st.expander(f"📋 View all {len(all_signals)} signals"):
                for sig in sorted(all_signals, key=lambda s: s['timestamp'], reverse=True):
                    st.markdown(f"""
                    <div class="signal-item">
                        <strong>[{format_signal_date(sig['timestamp'])}]</strong><br>
                        {sig['text']}
                    </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
    else:
        st.info(f"💡 No clusters found for '{search_query}'. Try broader terms.")

st.divider()

# === ACTIVE CLUSTERS FEED ===
active_clusters = [c for c in candidates if c["signal_count"] >= ACTIVE_MIN]
candidate_clusters = [c for c in candidates if c["signal_count"] < ACTIVE_MIN]

# Apply display mode filter
if display_mode == "Early Weak Signals":
    active_clusters = [c for c in active_clusters if c["signal_count"] < 10]
elif display_mode == "Mature Trends":
    active_clusters = [c for c in active_clusters if c["signal_count"] >= 10]

st.markdown("### 🔥 Active Emerging Clusters")

if active_clusters:
    feed = build_emerging_feed(active_clusters)
    
    # Pagination
    clusters_per_page = 5
    total_pages = (len(feed) + clusters_per_page - 1) // clusters_per_page
    
    if total_pages > 1:
        col_page, col_info = st.columns([1, 3])
        with col_page:
            page = st.selectbox("Page", range(1, total_pages + 1), key="active_page")
        with col_info:
            st.caption(f"📊 Showing {clusters_per_page} per page | Total: {len(feed)}")
    else:
        page = 1
        st.caption(f"📊 Total: {len(feed)} active clusters")
    
    start_idx = (page - 1) * clusters_per_page
    end_idx = min(start_idx + clusters_per_page, len(feed))
    page_feed = feed[start_idx:end_idx]

    for idx, item in enumerate(page_feed):
        # Get cluster data
        cluster_data = next(c for c in active_clusters if c["cluster_id"] == item["cluster_id"])
        cluster_data["growth_ratio"] = item["growth_ratio"]
        
        original_cluster = next(c for c in original_candidates if c["cluster_id"] == item["cluster_id"])
        all_signals = original_cluster["signals"]
        
        signal_texts = [s['text'] for s in cluster_data["signals"]]
        cluster_id = cluster_data["cluster_id"]
        title = generate_human_cluster_title(signal_texts, cluster_id=cluster_id)
        
        # Grounding
        grounding = compute_cluster_grounding(cluster_data)
        
        # === CLUSTER CARD ===
        st.markdown(f"""
        <div class="cluster-card">
            <div class="cluster-title">📈 {title}</div>
        """, unsafe_allow_html=True)
        
        # Badges row
        badge_html = f'<div class="metrics-row">'
        
        # Emergence badge
        emergence_level = item.get("emergence_level", "stable")
        if emergence_level == "rapid":
            badge_html += f'<span class="badge badge-rapid">⚡ Rapid Growth</span>'
        elif emergence_level == "stable":
            badge_html += f'<span class="badge badge-stable">📊 Stable</span>'
        else:
            badge_html += f'<span class="badge badge-dormant">😴 Dormant</span>'
        
        # Critic confidence badge
        if "critic_report" in cluster_data and cluster_data["critic_report"] is not None:
            confidence = cluster_data["critic_report"].get("confidence", "unknown")
            if confidence == "high":
                badge_html += f'<span class="badge badge-high">🟢 High Confidence</span>'
            elif confidence == "medium":
                badge_html += f'<span class="badge badge-medium">🟡 Medium</span>'
            else:
                badge_html += f'<span class="badge badge-low">🔴 Low</span>'
        
        # Coherence badge
        coherence = grounding.get("coherence", 0.0)
        coherence_color = "badge-high" if coherence >= 0.70 else "badge-medium" if coherence >= 0.50 else "badge-low"
        badge_html += f'<span class="badge {coherence_color}">🎯 {coherence:.2f} coherence</span>'
        
        # Signal count badge
        badge_html += f'<span class="badge badge-medium">📊 {item["signal_count"]} signals</span>'
        
        badge_html += '</div>'
        st.markdown(badge_html, unsafe_allow_html=True)
        
        # Grounding info
        st.markdown(f"""
        <div class="info-row">
            🧠 <strong>Grounding:</strong> {grounding['explanation']}
        </div>
        """, unsafe_allow_html=True)
        
        # Critic + Controller info
        if ("critic_report" in cluster_data and cluster_data["critic_report"] is not None and 
            "controller_decision" in cluster_data and cluster_data["controller_decision"] is not None):
            critic = cluster_data["critic_report"]
            controller = cluster_data["controller_decision"]
            flags_str = ", ".join(critic.get("flags", [])) if critic.get("flags") else "none"
            
            st.markdown(f"""
            <div class="info-row">
                🧪 <strong>Critic:</strong> {critic.get('confidence', 'unknown')} | Flags: {flags_str}
            </div>
            <div class="info-row">
                🤖 <strong>Controller:</strong> {controller.get('decision_trace', 'No trace')}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Metrics row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Growth Ratio", f"{item['growth_ratio']:.2f}x")
        with col2:
            st.metric("Total Signals", len(all_signals))
        with col3:
            st.metric("Recent Signals", item['signal_count'])
        
        # View signals button
        with st.expander(f"📋 View all {len(all_signals)} signals (recent: {item['signal_count']})"):
            sorted_signals = sorted(all_signals, key=lambda s: s['timestamp'], reverse=True)
            
            # Pagination for large signal lists
            signals_per_page = 15
            total_signal_pages = (len(sorted_signals) + signals_per_page - 1) // signals_per_page
            
            if total_signal_pages > 1:
                signal_page = st.selectbox(
                    f"Page ({signals_per_page} per page)",
                    range(1, total_signal_pages + 1),
                    key=f"sig_{idx}_{cluster_id}"
                )
            else:
                signal_page = 1
            
            sig_start = (signal_page - 1) * signals_per_page
            sig_end = min(sig_start + signals_per_page, len(sorted_signals))
            page_signals = sorted_signals[sig_start:sig_end]
            
            for sig in page_signals:
                st.markdown(f"""
                <div class="signal-item">
                    <strong>[{format_signal_date(sig['timestamp'])}]</strong><br>
                    {sig['text']}
                </div>
                """, unsafe_allow_html=True)
        
        # Cluster Explainer
        st.markdown("#### 💬 Ask about this cluster")
        
        col1, col2, col3 = st.columns(3)
        question_key = f"question_{idx}_{cluster_id}"
        
        with col1:
            if st.button("Why emerging?", key=f"why_{idx}_{cluster_id}"):
                st.session_state[question_key] = "Why is this emerging?"
        with col2:
            if st.button("Who cares?", key=f"who_{idx}_{cluster_id}"):
                st.session_state[question_key] = "Who should care?"
        with col3:
            if st.button("What's next?", key=f"next_{idx}_{cluster_id}"):
                st.session_state[question_key] = "What could happen next?"
        
        user_question = st.text_input(
            "Custom question:",
            key=question_key,
            placeholder="e.g., What are the risks?",
            label_visibility="collapsed"
        )
        
        if user_question:
            with st.spinner("🤔 Generating explanation..."):
                response = explain_cluster_with_gemini(signal_texts, user_question)
                st.info(response)
        
        st.divider()
else:
    st.info("💡 No active clusters match your filters.")

# === GRAPH VISUALIZATION ===
st.markdown("### 🕸 Cluster Relationship Graph")

if active_clusters:
    st.markdown("""
    <div class="graph-container">
    """, unsafe_allow_html=True)
    
    # Legend
    st.markdown("#### 📖 Graph Legend")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background: rgba(244, 176, 0, 0.1); padding: 12px; border-radius: 8px; border-left: 3px solid #f4b000;'>
            <span style='font-size: 20px;'>🟡</span> <strong>Cluster</strong><br>
            <small style='color: #9ca3af;'>Aggregated emerging topic</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: rgba(142, 202, 230, 0.1); padding: 12px; border-radius: 8px; border-left: 3px solid #8ecae6;'>
            <span style='font-size: 20px;'>🔵</span> <strong>Signal</strong><br>
            <small style='color: #9ca3af;'>Individual data point</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: rgba(107, 114, 128, 0.1); padding: 12px; border-radius: 8px; border-left: 3px solid #6b7280;'>
            <span style='font-size: 20px;'>➖</span> <strong>Edge</strong><br>
            <small style='color: #9ca3af;'>Semantic similarity</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.caption("💡 **Tip:** Drag nodes to explore relationships. Clusters are labeled with AI-generated titles.")
    
    # Add labels to clusters
    for c in active_clusters:
        signal_texts = [s['text'] for s in c["signals"]]
        cluster_id = c["cluster_id"]
        c["label"] = generate_human_cluster_title(signal_texts, cluster_id=cluster_id)
    
    # Build graph
    build_cluster_graph(active_clusters)
    html(open("cluster_graph.html").read(), height=700)
    
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("💡 Need active clusters to visualize relationships.")

st.divider()

# === CANDIDATE CLUSTERS ===
st.markdown("### 🌱 Candidate Clusters (Incubating)")

if candidate_clusters:
    st.caption(f"📊 {len(candidate_clusters)} clusters below active threshold (< {ACTIVE_MIN} signals)")
    
    for c in candidate_clusters:
        original_cluster = next(orig_c for orig_c in original_candidates if orig_c["cluster_id"] == c["cluster_id"])
        all_signals = original_cluster["signals"]
        
        signal_texts = [s['text'] for s in c["signals"]]
        cluster_id = c["cluster_id"]
        c["label"] = generate_human_cluster_title(signal_texts, cluster_id=cluster_id)
        
        with st.expander(f"🌱 {c['label']} ({c['signal_count']} recent / {len(all_signals)} total)"):
            for sig in sorted(all_signals, key=lambda s: s['timestamp'], reverse=True):
                st.markdown(f"""
                <div class="signal-item">
                    <strong>[{format_signal_date(sig['timestamp'])}]</strong><br>
                    {sig['text']}
                </div>
                """, unsafe_allow_html=True)
else:
    st.info("💡 No candidate clusters at this time.")

# === FOOTER ===
st.divider()
st.markdown("""
<div style='text-align: center; padding: 40px 0; color: #6b7280;'>
    <p style='font-size: 14px;'>
        Powered by <strong>SignalWeave</strong> — Temporal Vector Memory for Emerging Intelligence<br>
        <small>Built with Qdrant Cloud · SentenceTransformers · Gemini AI · Streamlit</small>
    </p>
</div>
""", unsafe_allow_html=True)
