"""PSL Analytics — Dashboard with Manual Navigation"""
import streamlit as st
import sys, runpy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(page_title="PSL Analytics", page_icon="🏏", layout="wide")

from dashboard.components.style import inject_custom_css
inject_custom_css()

st.sidebar.markdown("""
<div style="text-align:center; padding: 16px 0;">
    <div style="font-size: 2.5rem;">🏏</div>
    <div style="font-family: 'Oswald', sans-serif; font-size: 1.3rem; font-weight: 700;
         background: linear-gradient(135deg, #c9f34d, #f0b429);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent;
         letter-spacing: 2px; margin-top: 8px; text-transform: uppercase;">PSL Analytics</div>
    <div style="font-family: 'Oswald'; font-size: 0.65rem; color: #3a5a4a;
         text-transform: uppercase; letter-spacing: 3px; margin-top: 2px;">Match Intelligence</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

PAGES = {
    "🏠 Overview": "0_Overview",
    "🏏 Player Analytics": "1_Player_Analytics",
    "👥 Team Analytics": "2_Team_Analytics",
    "⚔️ Matchups": "3_Matchups",
    "🏟️ Venue Intelligence": "4_Venue_Intelligence",
    "⏱️ Phase Analytics": "5_Phase_Analytics",
    "📈 Player Form": "6_Player_Form",
    "🧠 Match Intelligence": "7_Match_Intelligence",
    "🔮 Predictions": "8_Predictions",
    "🔥 Clutch & Pressure": "9_Clutch_Pressure",
    "🎯 Match Predictor": "10_Match_Predictor",
    "🏆 Season Awards": "11_Season_Awards",
    "🆚 Player Comparison": "12_Player_Comparison",
    "🧩 Optimal XI": "13_Optimal_XI",
    "📜 Records": "14_Records",
    "📅 Season Explorer": "15_Season_Explorer",
    "🏏 Team Profile": "16_Team_Profile",
    "🎯 Chase & Defence": "17_Chase_Defence",
    "💀 Dismissals": "18_Dismissals",
    "🤝 Partnerships": "19_Partnerships",
    "🧤 Fielding": "20_Fielding",
    "📋 Match Explorer": "21_Match_Explorer",
    "🥇 Leaderboard": "22_Leaderboard",
    "👤 Player Profile": "23_Player_Profile",
    "📊 Season Comparison": "24_Season_Comparison",
    "⚡ Super Overs": "25_Super_Overs",
    "👑 PSL History": "26_PSL_History",
    "🏠 Home vs Away": "27_Home_Away",
    "🚀 Powerplay Deep": "28_Powerplay_Deep",
    "💀 Death Overs Deep": "29_Death_Deep",
    "🏆 Playoffs": "30_Playoffs",
    "🔎 Search": "31_Search",
    "🤖 AI Insights": "32_AI_Insights",
    "🏅 Player Rankings": "33_Player_Rankings",
    "💰 Auction Value": "34_Auction_Value",
    "🎮 Match Simulator": "35_Match_Simulator",
    "⚔️ H2H Deep Dive": "36_H2H_Deep",
    "🏅 Player Rankings": "33_Player_Rankings",
    "💰 Auction Value": "34_Auction_Value",
    "⚔️ H2H Deep Dive": "35_H2H_Deep",
    "🎮 Match Simulator": "36_Match_Simulator",
}

selected = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption("🏟️ 357 Matches • 83,799 Balls • 11 Seasons")

# Load selected page using runpy (proper __file__ handling)
page_file = str(Path(__file__).parent / "pages" / (PAGES[selected] + ".py"))
runpy.run_path(page_file, run_name="__main__")