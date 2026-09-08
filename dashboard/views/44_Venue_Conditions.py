"""Merged: Venue & Conditions"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("🏟️ Venue & Conditions", "Venue Intelligence · Chase vs Defend")
seam_divider()

tab1, tab2 = st.tabs(["🏟️ Venue Intelligence", "🏃 Chase vs Defend"])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "4_Venue_Intelligence.py"), run_name="__tab__")
    except Exception as e: st.error(f"Venue: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "17_Chase_Defence.py"), run_name="__tab__")
    except Exception as e: st.error(f"Chase: {e}")
