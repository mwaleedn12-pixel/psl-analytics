"""Match Simulator — simulate hypothetical match scenarios."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, fix_metrics

inject_custom_css()
fix_metrics()
hero_card("🎮 Match Simulator", "Simulate hypothetical match scenarios — projected scores & win probability")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv")
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()

teams = sorted(set(matches.team1) | set(matches.team2))
venues = sorted(matches.venue.unique())

st.markdown("##### ⚙️ Setup Match")
col1, col2, col3 = st.columns(3)
with col1: team1 = st.selectbox("Team 1 (Batting First)", teams)
with col2: team2 = st.selectbox("Team 2", [t for t in teams if t != team1])
with col3: venue = st.selectbox("Venue", venues)

if st.button("⚡ SIMULATE MATCH"):
    # Historical stats for simulation
    t1_bat = deliveries[(deliveries.batting_team == team1)].copy()
    t2_bat = deliveries[(deliveries.batting_team == team2)].copy()
    t1_bowl = deliveries[(deliveries.bowling_team == team1)].copy()
    t2_bowl = deliveries[(deliveries.bowling_team == team2)].copy()

    # Avg score at venue
    venue_inn = deliveries[deliveries.venue == venue].groupby(["match_id","innings"])["total_runs"].sum()
    venue_avg = venue_inn.mean() if len(venue_inn) > 0 else 160

    # Team batting avg
    t1_avg = t1_bat.groupby(["match_id","innings"])["total_runs"].sum().mean()
    t2_avg = t2_bat.groupby(["match_id","innings"])["total_runs"].sum().mean()

    # Team bowling avg conceded
    t1_bowl_avg = t1_bowl.groupby(["match_id","innings"])["total_runs"].sum().mean()
    t2_bowl_avg = t2_bowl.groupby(["match_id","innings"])["total_runs"].sum().mean()

    # Projected scores (weighted average)
    t1_projected = int((t1_avg * 0.35 + t2_bowl_avg * 0.35 + venue_avg * 0.30))
    t2_projected = int((t2_avg * 0.35 + t1_bowl_avg * 0.35 + venue_avg * 0.30))

    # Add randomness
    np.random.seed(42)
    t1_range = [t1_projected - 20, t1_projected + 20]
    t2_range = [t2_projected - 20, t2_projected + 20]

    # Simulate 1000 matches
    t1_scores = np.random.normal(t1_projected, 18, 1000).astype(int)
    t2_scores = np.random.normal(t2_projected, 18, 1000).astype(int)
    t1_win_pct = round((t1_scores > t2_scores).mean() * 100, 1)
    t2_win_pct = round(100 - t1_win_pct, 1)

    tc1 = TEAM_COLORS.get(team1, {"primary":"#c9f34d"})["primary"]
    tc2 = TEAM_COLORS.get(team2, {"primary":"#38bdf8"})["primary"]

    st.markdown("---")

    # Result display
    col1, col2, col3 = st.columns([2,1,2])
    with col1:
        st.markdown(f"""
        <div style="text-align:center; padding:24px; background:rgba(13,43,31,0.5);
             border-radius:16px; border:2px solid {tc1};">
            <div style="font-family:Oswald; font-size:1.2rem; color:{tc1}; text-transform:uppercase;">{team1}</div>
            <div style="font-family:'Share Tech Mono'; font-size:2.5rem; color:#fff;">{t1_projected}</div>
            <div style="font-family:'Share Tech Mono'; font-size:1rem; color:{tc1};">{t1_win_pct}% win</div>
            <div style="color:#5a8a6f; font-size:0.75rem;">Range: {t1_range[0]}-{t1_range[1]}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div style="text-align:center; padding:50px 0; font-family:Oswald;
             font-size:1.5rem; color:#3a5a4a;">VS</div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="text-align:center; padding:24px; background:rgba(13,43,31,0.5);
             border-radius:16px; border:2px solid {tc2};">
            <div style="font-family:Oswald; font-size:1.2rem; color:{tc2}; text-transform:uppercase;">{team2}</div>
            <div style="font-family:'Share Tech Mono'; font-size:2.5rem; color:#fff;">{t2_projected}</div>
            <div style="font-family:'Share Tech Mono'; font-size:1rem; color:{tc2};">{t2_win_pct}% win</div>
            <div style="color:#5a8a6f; font-size:0.75rem;">Range: {t2_range[0]}-{t2_range[1]}</div>
        </div>""", unsafe_allow_html=True)

    # Score distribution
    st.markdown("---")
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=t1_scores, name=team1, marker=dict(color=tc1), opacity=0.6, nbinsx=30))
    fig.add_trace(go.Histogram(x=t2_scores, name=team2, marker=dict(color=tc2), opacity=0.6, nbinsx=30))
    fig.update_layout(**PLOTLY_LAYOUT, barmode="overlay", title="SIMULATED SCORE DISTRIBUTION (1000 matches)",
                      height=400, xaxis_title="Projected Score", yaxis_title="Frequency")
    st.plotly_chart(fig, use_container_width=True)

    # Factors
    st.markdown("##### 📊 Key Factors")
    st.markdown(f"🏟️ **Venue avg:** {venue_avg:.0f} at {venue.split(',')[0]}")
    st.markdown(f"🏏 **{team1} batting avg:** {t1_avg:.0f} | **{team2} bowling avg conceded:** {t2_bowl_avg:.0f}")
    st.markdown(f"🏏 **{team2} batting avg:** {t2_avg:.0f} | **{team1} bowling avg conceded:** {t1_bowl_avg:.0f}")
