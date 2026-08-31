"""Optimal Playing XI — suggest best team for venue/opponent."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, TEAM_COLORS
from src.analytics.premium import OptimalXI

inject_custom_css()
hero_card("🧩 Optimal Playing XI", "AI-suggested best XI based on team, venue, and opponent performance data")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)

deliveries = load_data()
teams = sorted(deliveries.batting_team.unique())
venues = sorted(deliveries.venue.unique())

col1, col2, col3 = st.columns(3)
with col1:
    team = st.selectbox("Select Your Team", teams)
with col2:
    venue = st.selectbox("Venue", ["Any"] + venues)
with col3:
    opponent = st.selectbox("Opponent", ["Any"] + [t for t in teams if t != team])

venue_val = None if venue == "Any" else venue
opp_val = None if opponent == "Any" else opponent

result = OptimalXI.suggest(deliveries, team, venue=venue_val, opponent=opp_val)

tc = TEAM_COLORS.get(team, {"primary": "#c9f34d", "secondary": "#1a1a2e"})

st.markdown(f"""
<div style="text-align:center; padding:16px; margin:16px 0;
     background: linear-gradient(135deg, {tc['primary']}22, {tc['secondary']}22);
     border: 1px solid {tc['primary']}44; border-radius: 14px;">
    <div style="font-family:Oswald; font-size:1.4rem; color:{tc['primary']}; text-transform:uppercase; letter-spacing:2px;">
        {team} — Suggested XI
    </div>
    <div style="color:#5a8a6f; font-size:0.8rem;">
        {f"at {venue}" if venue != "Any" else "All Venues"} {f"vs {opponent}" if opponent != "Any" else ""}
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("##### 🏏 Batting Order")
    for i, b in enumerate(result["suggested_batters"], 1):
        st.markdown(f"""
        <div style="background:rgba(13,43,31,0.5); border-radius:10px; padding:10px 16px; margin:4px 0;
             border-left: 3px solid {tc['primary']};">
            <span style="font-family:'Share Tech Mono'; color:{tc['primary']}; font-size:1.1rem;">#{i}</span>
            <span style="font-family:Oswald; color:#fff; font-size:1rem; margin-left:8px;">{b['batter']}</span>
            <span style="float:right; font-family:'Share Tech Mono'; color:#7aaa8f; font-size:0.85rem;">
                {b['runs']}r | Avg {b['avg']} | SR {b['sr']}
            </span>
        </div>""", unsafe_allow_html=True)

with col2:
    st.markdown("##### 🎯 Bowling Attack")
    for i, b in enumerate(result["suggested_bowlers"], 1):
        st.markdown(f"""
        <div style="background:rgba(13,43,31,0.5); border-radius:10px; padding:10px 16px; margin:4px 0;
             border-left: 3px solid {tc['primary']};">
            <span style="font-family:'Share Tech Mono'; color:{tc['primary']}; font-size:1.1rem;">#{i}</span>
            <span style="font-family:Oswald; color:#fff; font-size:1rem; margin-left:8px;">{b['bowler']}</span>
            <span style="float:right; font-family:'Share Tech Mono'; color:#7aaa8f; font-size:0.85rem;">
                {b['wickets']}w | Econ {b['economy']} | Dot {b['dot_pct']}%
            </span>
        </div>""", unsafe_allow_html=True)
