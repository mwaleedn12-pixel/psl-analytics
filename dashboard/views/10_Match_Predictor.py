"""Match Predictor — Pre-match winner prediction."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS
from src.models.match_predictor import MatchPredictor

inject_custom_css()
hero_card("🔮 Match Predictor", "Pre-match winner prediction based on teams, venue, and toss")
seam_divider()

@st.cache_data
def load_matches():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])

@st.cache_resource
def train_predictor(_m):
    mp = MatchPredictor()
    mp.train(_m)
    return mp

matches = load_matches()
predictor = train_predictor(matches)

col1, col2 = st.columns(2)
teams = sorted(set(matches.team1) | set(matches.team2))
venues = sorted(matches.venue.unique())

with col1:
    team1 = st.selectbox("Team 1", teams, index=0)
    toss_winner = st.selectbox("Toss Winner", [team1, "Team 2 (select first)"])
with col2:
    team2 = st.selectbox("Team 2", [t for t in teams if t != team1], index=0)
    toss_decision = st.selectbox("Toss Decision", ["field", "bat"])

toss_winner = toss_winner if toss_winner != "Team 2 (select first)" else team2
venue = st.selectbox("Venue", venues)

if st.button("⚡ PREDICT WINNER"):
    result = predictor.predict(team1, team2, venue, toss_winner, toss_decision)

    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])

    t1_color = TEAM_COLORS.get(team1, {"primary": "#c9f34d"})["primary"]
    t2_color = TEAM_COLORS.get(team2, {"primary": "#f0b429"})["primary"]

    with col1:
        st.markdown(f"""
        <div style="text-align:center; padding:20px; background:rgba(13,43,31,0.5);
             border-radius:16px; border:2px solid {t1_color};">
            <div style="font-family:Oswald; font-size:1.2rem; color:#fff; text-transform:uppercase;">{team1}</div>
            <div style="font-family:'Share Tech Mono'; font-size:2.5rem; color:{t1_color};">{result['team1_win_pct']}%</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align:center; padding:40px 10px; font-family:Oswald; font-size:1.5rem; color:#3a5a4a;">
            VS
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="text-align:center; padding:20px; background:rgba(13,43,31,0.5);
             border-radius:16px; border:2px solid {t2_color};">
            <div style="font-family:Oswald; font-size:1.2rem; color:#fff; text-transform:uppercase;">{team2}</div>
            <div style="font-family:'Share Tech Mono'; font-size:2.5rem; color:{t2_color};">{result['team2_win_pct']}%</div>
        </div>""", unsafe_allow_html=True)

    winner_color = TEAM_COLORS.get(result["predicted_winner"], {"primary": "#c9f34d"})["primary"]
    st.markdown(f"""
    <div style="text-align:center; margin:20px 0; padding:16px; background:rgba(13,43,31,0.6);
         border-radius:12px; border:1px solid {winner_color};">
        <span style="font-family:Oswald; font-size:0.8rem; color:#5a8a6f; text-transform:uppercase; letter-spacing:2px;">Predicted Winner</span><br>
        <span style="font-family:Oswald; font-size:1.8rem; color:{winner_color}; text-transform:uppercase;">{result['predicted_winner']}</span>
        <span style="font-family:'Share Tech Mono'; color:#7aaa8f;"> ({result['confidence']}% confidence)</span>
    </div>""", unsafe_allow_html=True)

    for f in result["factors"]:
        st.markdown(f"✅ {f}")
