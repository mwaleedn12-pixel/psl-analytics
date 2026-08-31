"""Team Analytics Page — strengths, comparisons, phase performance."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.analytics.engines import TeamEngine, PhaseEngine


from dashboard.components.style import inject_custom_css, PLOTLY_LAYOUT

st.title("👥 Team Analytics")
inject_custom_css()

@st.cache_data
def load_data():
    P = PROJECT_ROOT / "data" / "processed"
    m = pd.read_csv(P / "psl_matches_clean.csv")
    d = pd.read_csv(P / "psl_deliveries_clean.csv", low_memory=False)
    return m, d

matches, deliveries = load_data()

tab1, tab2, tab3 = st.tabs(["Batting Strength", "Bowling Strength", "Phase Performance"])

with tab1:
    bat_str = TeamEngine.team_batting_strength(deliveries)
    fig = px.bar(bat_str.sort_values("avg_score"), x="avg_score", y="batting_team",
                 orientation="h", title="Average Innings Score",
                 color="avg_score", color_continuous_scale="YlGn",
                 labels={"avg_score": "Avg Score", "batting_team": ""})
    fig.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    cols = ["batting_team", "innings_count", "avg_score", "avg_sr",
            "avg_wickets_lost", "avg_powerplay_score", "avg_middle_score", "avg_death_score"]
    st.dataframe(bat_str[[c for c in cols if c in bat_str.columns]],
                 use_container_width=True, hide_index=True)

with tab2:
    bowl_str = TeamEngine.team_bowling_strength(deliveries)
    fig = px.bar(bowl_str.sort_values("avg_conceded", ascending=False),
                 x="avg_conceded", y="bowling_team", orientation="h",
                 title="Average Runs Conceded", color="avg_wickets",
                 color_continuous_scale="Purples",
                 labels={"avg_conceded": "Avg Conceded", "bowling_team": "", "avg_wickets": "Avg Wkts"})
    fig.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(bowl_str, use_container_width=True, hide_index=True)

with tab3:
    team = st.selectbox("Select Team", sorted(deliveries.batting_team.unique()))
    team_phase = PhaseEngine.team_phase_performance(deliveries)
    tp = team_phase[team_phase.batting_team == team].copy()
    order = {"powerplay": 0, "middle": 1, "death": 2}
    tp["order"] = tp.phase.map(order)
    tp = tp.sort_values("order")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(tp, x="phase", y="avg_runs", title=f"{team} — Avg Runs by Phase",
                     color="phase", color_discrete_map={
                         "powerplay": "#2196F3", "middle": "#4CAF50", "death": "#F44336"})
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.bar(tp, x="phase", y="sr", title=f"{team} — Strike Rate by Phase",
                      color="phase", color_discrete_map={
                          "powerplay": "#2196F3", "middle": "#4CAF50", "death": "#F44336"})
        st.plotly_chart(fig2, use_container_width=True)