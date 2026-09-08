"""Merged: Team Hub"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("⚔️ Team Hub", "Profile · Analytics · Home vs Away · Optimal XI")
seam_divider()

tab1, tab2, tab3, tab4 = st.tabs(["👥 Profile", "📊 Analytics", "🏠 Home vs Away", "⭐ Optimal XI"])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "16_Team_Profile.py"), run_name="__tab__")
    except Exception as e: st.error(f"Profile: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "2_Team_Analytics.py"), run_name="__tab__")
    except Exception as e: st.error(f"Analytics: {e}")
with tab3:
    try: runpy.run_path(str(Path(__file__).parent / "27_Home_Away.py"), run_name="__tab__")
    except Exception as e: st.error(f"Home/Away: {e}")
with tab4:
    try: runpy.run_path(str(Path(__file__).parent / "13_Optimal_XI.py"), run_name="__tab__")
    except Exception as e: st.error(f"Optimal XI: {e}")
