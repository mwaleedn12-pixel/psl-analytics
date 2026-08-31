"""PSL Analytics — Clean 7-Section Navigation"""
import streamlit as st
import sys, runpy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(page_title="PSL Analytics", page_icon="🏏", layout="wide")

from dashboard.components.style import inject_custom_css
inject_custom_css()

# ── Sidebar Logo ──
st.sidebar.markdown("""
<div style="text-align:center; padding: 10px 0 5px 0;">
    <span style="font-size: 1.8rem;">🏏</span>
    <span style="font-family: 'Oswald', sans-serif; font-size: 1rem; font-weight: 700;
         color: #c9f34d; letter-spacing: 2px; text-transform: uppercase; vertical-align: middle;
         margin-left: 6px;">PSL Analytics</span>
</div>
""", unsafe_allow_html=True)

# ── 7 Main Sections ──
SECTIONS = {
    "🏠 Overview":       ["Overview", "Search", "AI Insights"],
    "👤 Players":        ["Player Profile", "Player Analytics", "Player Form", "Player Rankings", "Player Comparison", "Auction Value"],
    "👥 Teams":          ["Team Profile", "Team Analytics", "Home vs Away", "Optimal XI"],
    "📋 Matches":        ["Match Explorer", "Match Intelligence", "Match Predictor", "Match Simulator"],
    "📊 Analytics":      ["Phase Analytics", "Powerplay Deep", "Death Overs Deep", "Venue Intelligence", "Chase Defence", "Dismissals", "Partnerships", "Fielding", "Clutch Pressure"],
    "⚔️ Matchups":       ["Matchups", "H2H Deep Dive"],
    "🏆 Tournaments":    ["Season Explorer", "Season Comparison", "Season Awards", "PSL History", "Playoffs", "Super Overs", "Records", "Leaderboard"],
}

# Page file mapping
PAGE_FILES = {
    "Overview": "0_Overview", "Search": "31_Search", "AI Insights": "32_AI_Insights",
    "Player Profile": "23_Player_Profile", "Player Analytics": "1_Player_Analytics",
    "Player Form": "6_Player_Form", "Player Rankings": "33_Player_Rankings",
    "Player Comparison": "12_Player_Comparison", "Auction Value": "34_Auction_Value",
    "Team Profile": "16_Team_Profile", "Team Analytics": "2_Team_Analytics",
    "Home vs Away": "27_Home_Away", "Optimal XI": "13_Optimal_XI",
    "Match Explorer": "21_Match_Explorer", "Match Intelligence": "7_Match_Intelligence",
    "Match Predictor": "10_Match_Predictor", "Match Simulator": "35_Match_Simulator",
    "Phase Analytics": "5_Phase_Analytics", "Powerplay Deep": "28_Powerplay_Deep",
    "Death Overs Deep": "29_Death_Deep", "Venue Intelligence": "4_Venue_Intelligence",
    "Chase Defence": "17_Chase_Defence", "Dismissals": "18_Dismissals",
    "Partnerships": "19_Partnerships", "Fielding": "20_Fielding",
    "Clutch Pressure": "9_Clutch_Pressure",
    "Matchups": "3_Matchups", "H2H Deep Dive": "36_H2H_Deep",
    "Season Explorer": "15_Season_Explorer", "Season Comparison": "24_Season_Comparison",
    "Season Awards": "11_Season_Awards", "PSL History": "26_PSL_History",
    "Playoffs": "30_Playoffs", "Super Overs": "25_Super_Overs",
    "Records": "14_Records", "Leaderboard": "22_Leaderboard",
}

# ── Navigation ──
section = st.sidebar.selectbox("", list(SECTIONS.keys()), label_visibility="collapsed")
sub_pages = SECTIONS[section]
page = st.sidebar.selectbox("", sub_pages, label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption("357 Matches • 83,799 Balls • 11 Seasons")

# ── Load Page ──
page_file = str(Path(__file__).parent / "views" / (PAGE_FILES[page] + ".py"))
runpy.run_path(page_file, run_name="__main__")