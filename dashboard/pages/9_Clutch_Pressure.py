"""Clutch & Pressure Analysis Page."""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.analytics.extended_engines import (
    PressurePerformance, ClutchAnalysis, PlayerValueIndex,
)
from src.analytics.impact_engine import compute_impact_scores, compute_career_impact


from dashboard.components.style import inject_custom_css, PLOTLY_LAYOUT

st.title("🔥 Clutch & Pressure Analysis")
inject_custom_css()

@st.cache_data
def load_data():
    P = PROJECT_ROOT / "data" / "processed"
    m = pd.read_csv(P / "psl_matches_clean.csv")
    d = pd.read_csv(P / "psl_deliveries_clean.csv", low_memory=False)
    return m, d

matches, deliveries = load_data()

tab1, tab2, tab3 = st.tabs(["Clutch Performers", "Pressure Stats", "Player Value Index"])

with tab1:
    rr_threshold = st.slider("Required RR Threshold", 8.0, 14.0, 10.0, 0.5)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Clutch Batters** (high RR chases)")
        cb = ClutchAnalysis.clutch_batters(deliveries, rr_threshold=rr_threshold, min_balls=20)
        st.dataframe(cb[["batter", "clutch_innings", "clutch_runs", "clutch_sr",
                          "clutch_boundary_pct"]].head(15),
                     use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**Clutch Bowlers** (defending under pressure)")
        cbowl = ClutchAnalysis.clutch_bowlers(deliveries, rr_threshold=rr_threshold, min_balls=20)
        st.dataframe(cbowl[["bowler", "clutch_innings", "clutch_wickets", "clutch_economy",
                             "clutch_dot_pct"]].head(15),
                     use_container_width=True, hide_index=True)

with tab2:
    pp = PressurePerformance.batting_under_pressure(deliveries, matches, min_innings=3)
    fig = px.scatter(pp.head(50), x="pressure_avg", y="pressure_sr",
                     size="pressure_runs", hover_name="batter",
                     title="Batting Under Pressure (Close Matches)",
                     labels={"pressure_avg": "Avg (Close Matches)", "pressure_sr": "SR (Close Matches)"})
    fig.update_layout(**PLOTLY_LAYOUT, height=450)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    scores = compute_impact_scores(deliveries, matches)
    pvi = PlayerValueIndex.compute(scores, min_matches=15)
    fig = px.bar(pvi.head(20), x="value_index", y="player", orientation="h",
                 title="Player Value Index (Impact × Consistency)",
                 color="consistency", color_continuous_scale="Greens",
                 labels={"value_index": "Value Index", "player": "", "consistency": "Consistency"})
    fig.update_layout(yaxis=dict(autorange="reversed"), height=550)
    st.plotly_chart(fig, use_container_width=True)