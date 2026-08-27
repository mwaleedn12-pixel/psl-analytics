"""
PSL Analytics & Match Intelligence — Dashboard

Entry point for the Streamlit application.
Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path so src modules are importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DASHBOARD_TITLE, DASHBOARD_ICON, DASHBOARD_LAYOUT

# ── Page Config ──
st.set_page_config(
    page_title=DASHBOARD_TITLE,
    page_icon=DASHBOARD_ICON,
    layout=DASHBOARD_LAYOUT,
)

# ── Main Page ──
st.title(f"{DASHBOARD_ICON} {DASHBOARD_TITLE}")
st.markdown("---")

st.info(
    "🚧 **Dashboard is under development.**\n\n"
    "The data pipeline, analytics engine, and ML models are being built phase by phase.\n\n"
    "Check back as features are added!"
)

st.markdown(
    """
    ### Planned Pages
    1. **Overview** — Season summaries & key stats
    2. **Player Analytics** — Individual performance & Impact Score
    3. **Team Analytics** — Team strengths & comparisons
    4. **Match Explorer** — Ball-by-ball match breakdowns
    5. **Matchups** — Batter vs Bowler & Team vs Team
    6. **Phase Analytics** — Powerplay / Middle / Death analysis
    7. **Venue Intelligence** — Venue profiles & trends
    8. **Player Form** — Rolling performance & recent form
    9. **Match Intelligence** — Win probability & turning points
    10. **Predictions** — Live win probability simulator
    """
)

st.markdown("---")
st.caption("PSL Analytics & Match Intelligence Platform • Portfolio Project")
