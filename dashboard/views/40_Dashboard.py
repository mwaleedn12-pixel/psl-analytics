"""Merged: Dashboard = Overview + Search + AI Insights"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("📊 PSL Analytics Dashboard", "Overview · Search · AI Insights — all in one view")
seam_divider()

tab1, tab2, tab3 = st.tabs(["🏠 Overview", "🔍 Search", "🤖 AI Insights"])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "0_Overview.py"), run_name="__tab__")
    except Exception as e: st.error(f"Overview: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "31_Search.py"), run_name="__tab__")
    except Exception as e: st.error(f"Search: {e}")
with tab3:
    try: runpy.run_path(str(Path(__file__).parent / "32_AI_Insights.py"), run_name="__tab__")
    except Exception as e: st.error(f"AI Insights: {e}")
