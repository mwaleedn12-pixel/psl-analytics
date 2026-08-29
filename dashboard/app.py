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
}

selected = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption("🏟️ 357 Matches • 83,799 Balls • 11 Seasons")

# Load selected page using runpy (proper __file__ handling)
page_file = str(Path(__file__).parent / "pages" / (PAGES[selected] + ".py"))
runpy.run_path(page_file, run_name="__main__")