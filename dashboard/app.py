"""PSL Analytics — Consolidated 5-Section Navigation"""
import streamlit as st
import sys, runpy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(page_title="PSL Analytics", page_icon="🏏", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stSidebar"] { min-width: 280px !important; max-width: 320px !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: flex !important; }
</style>
""", unsafe_allow_html=True)

from dashboard.components.style import inject_custom_css
inject_custom_css()

st.sidebar.markdown("""
<div style="text-align:center; padding: 10px 0 5px 0;">
    <span style="font-size: 1.8rem;">🏏</span>
    <span style="font-family: 'Oswald', sans-serif; font-size: 1rem; font-weight: 700;
         color: #c9f34d; letter-spacing: 2px; text-transform: uppercase; vertical-align: middle;
         margin-left: 6px;">PSL Analytics</span>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 5 CLEAN SECTIONS — merged, no clutter
# ═══════════════════════════════════════════════════════════

SECTIONS = {
    "📊 Overview": [
        "Dashboard",          # Home + Search + AI Insights merged
    ],
    "🏏 Players": [
        "Player Hub",         # Profile + Form + Rankings + Analytics + Auction Value + Comparison
        "Leaderboard",        # Orange/Purple cap + records
        "Similarity Finder",  # Player similarity
    ],
    "📈 Match Analysis": [
        "Match Centre",       # Match Explorer + Intelligence
        "Innings & Phases",   # Phase Analytics + Powerplay + Death
        "Venue & Conditions", # Venue + Chase/Defend + Toss
        "Partnerships",       # Partnerships + Fielding + Dismissals
        "Matchups & H2H",     # Matchups + H2H Deep Dive
        "Predictions",        # Win Predictor + What-If + Simulator
        "Clutch & Pressure",  # Clutch + Turning Points
    ],
    "⚔️ Teams & Seasons": [
        "Team Hub",           # Team Profile + Analytics + Home/Away + Optimal XI
        "Season Explorer",    # Season + Comparison + Awards
        "PSL History",        # History + Playoffs + Super Overs + Records
    ],
    "🏗️ Auction Room": [
        "Squad Builder",      # Squad analysis + AI draft
        "Coach Room",         # Retention + Worth + Alternatives
    ],
}

# Each merged page maps to a loader that runs sub-pages via tabs
PAGE_FILES = {
    # Overview
    "Dashboard": "40_Dashboard",
    # Players
    "Player Hub": "41_Player_Hub",
    "Leaderboard": "22_Leaderboard",
    "Similarity Finder": "12_Player_Comparison",
    # Match Analysis
    "Match Centre": "42_Match_Centre",
    "Innings & Phases": "43_Innings_Phases",
    "Venue & Conditions": "44_Venue_Conditions",
    "Partnerships": "45_Partnerships",
    "Matchups & H2H": "46_Matchups",
    "Predictions": "47_Predictions",
    "Clutch & Pressure": "9_Clutch_Pressure",
    # Teams & Seasons
    "Team Hub": "48_Team_Hub",
    "Season Explorer": "49_Season_Hub",
    "PSL History": "50_PSL_History",
    # Auction Room
    "Squad Builder": "37_Squad_Builder",
    "Coach Room": "39_Coach_Room",
}

section = st.sidebar.selectbox("", list(SECTIONS.keys()), label_visibility="collapsed")
sub_pages = SECTIONS[section]
page = st.sidebar.selectbox("", sub_pages, label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption("357 Matches • 83,799 Balls • 11 Seasons")

page_file = str(Path(__file__).parent / "views" / (PAGE_FILES[page] + ".py"))
runpy.run_path(page_file, run_name="__main__")