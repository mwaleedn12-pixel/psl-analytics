"""Partnership Analytics."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT
from src.analytics.stats_engine import StatsEngine

inject_custom_css()
hero_card("🤝 Partnership Analytics", "Best batting partnerships, pair combinations, and partnership records")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)

deliveries = load_data()

@st.cache_data
def get_partnerships(_d):
    return StatsEngine.partnerships(_d, min_runs=50)

partnerships = get_partnerships(deliveries)

if len(partnerships) > 0:
    c1, c2, c3 = st.columns(3)
    c1.metric("Top Partnership Runs", int(partnerships.total_runs.max()))
    c2.metric("Highest Single", int(partnerships.highest.max()))
    c3.metric("Unique Pairs", len(partnerships))

    st.markdown("##### 🏏 Top Partnerships (Career)")
    top20 = partnerships.head(20).copy()
    top20["pair_name"] = top20.batter1 + " & " + top20.batter2

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top20.total_runs, y=top20.pair_name, orientation="h",
        marker=dict(color="#c9f34d"),
        text=[f"{int(r)}r ({int(p)} inns, HS {int(h)})" for r, p, h in
              zip(top20.total_runs, top20.partnerships, top20.highest)],
        textposition="outside", textfont=dict(color="#7aaa8f", size=10, family="Share Tech Mono"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=600, yaxis=dict(autorange="reversed"),
                      title="TOP PARTNERSHIP RUNS")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(partnerships.head(30)[["batter1", "batter2", "partnerships", "total_runs",
                                         "avg_runs", "highest", "fifty_plus", "avg_sr"]],
                 use_container_width=True, hide_index=True)
else:
    st.info("Computing partnerships...")
