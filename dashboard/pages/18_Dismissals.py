"""Dismissal Analytics — how players get out."""
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
hero_card("🏏 Dismissal Analytics", "How players get out — bowled, caught, LBW, run out, stumped, hit wicket")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
deliveries = load_data()

tab1, tab2 = st.tabs(["📊 Overall Dismissals", "👤 Player Dismissals"])

with tab1:
    overall = StatsEngine.dismissal_analysis(deliveries)
    colors = ["#c9f34d", "#38bdf8", "#f87171", "#fb923c", "#c084fc", "#34d399", "#fbbf24", "#818cf8"]
    fig = go.Figure(data=[go.Pie(
        labels=overall.wicket_kind, values=overall["count"], hole=0.55,
        marker=dict(colors=colors[:len(overall)]),
        textinfo="label+percent", textfont=dict(size=12, color="#fff", family="Oswald"),
    )])
    fig.update_layout(**PLOTLY_LAYOUT, title="DISMISSAL TYPES — ALL PSL", height=450, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(overall, use_container_width=True, hide_index=True)

with tab2:
    batters = sorted(deliveries[deliveries.is_legal == 1].batter.unique())
    player = st.selectbox("Select Player", batters)
    p_dis = StatsEngine.dismissal_analysis(deliveries, player=player)
    if len(p_dis) > 0:
        fig2 = go.Figure(data=[go.Bar(
            x=p_dis.wicket_kind, y=p_dis["count"],
            marker=dict(color="#c9f34d"),
            text=p_dis["count"], textposition="outside",
            textfont=dict(color="#c9f34d", family="Share Tech Mono"),
        )])
        fig2.update_layout(**PLOTLY_LAYOUT, title=f"{player} — DISMISSAL BREAKDOWN", height=400)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No dismissal data found.")
