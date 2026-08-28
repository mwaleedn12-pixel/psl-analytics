"""Venue Intelligence Page."""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.analytics.engines import VenueEngine, TossEngine


from dashboard.components.style import inject_custom_css, PLOTLY_LAYOUT

st.title("🏟️ Venue Intelligence")
inject_custom_css()

@st.cache_data
def load_data():
    P = PROJECT_ROOT / "data" / "processed"
    m = pd.read_csv(P / "psl_matches_clean.csv")
    d = pd.read_csv(P / "psl_deliveries_clean.csv", low_memory=False)
    return m, d

matches, deliveries = load_data()
profile = VenueEngine.venue_profile(deliveries, matches)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(profile.sort_values("avg_score"), x="avg_score", y="venue",
                 orientation="h", title="Average Innings Score by Venue",
                 color="avg_score", color_continuous_scale="YlOrRd",
                 labels={"avg_score": "Avg Score", "venue": ""})
    fig.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = px.bar(profile.sort_values("chase_win_pct"), x="chase_win_pct", y="venue",
                  orientation="h", title="Chasing Win % by Venue",
                  color="chase_win_pct", color_continuous_scale="Blues",
                  labels={"chase_win_pct": "Chase Win %", "venue": ""})
    fig2.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

cols_to_show = ["venue", "matches", "avg_score", "avg_1st_innings", "avg_2nd_innings",
                "chase_win_pct", "boundary_pct", "six_pct"]
st.dataframe(profile[[c for c in cols_to_show if c in profile.columns]],
             use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("🪙 Toss Analysis")
toss = TossEngine.toss_analysis(matches)
col1, col2, col3 = st.columns(3)
col1.metric("Toss Winner Wins Match", f"{toss['overall']['toss_win_match_win_pct']}%")
col2.metric("Choose to Field First", f"{toss['overall']['field_first_pct']}%")
col3.metric("Total Decided Matches", toss['overall']['total_matches'])

st.dataframe(toss["by_decision"], use_container_width=True, hide_index=True)