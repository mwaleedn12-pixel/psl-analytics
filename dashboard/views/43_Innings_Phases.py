"""Merged: Innings & Phases"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("📊 Innings & Phase Analytics", "Phase Breakdown · Powerplay Deep Dive · Death Overs Analysis")
seam_divider()

tab1, tab2, tab3 = st.tabs(["📊 Phase Analytics", "⚡ Powerplay Deep", "🎯 Death Overs Deep"])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "5_Phase_Analytics.py"), run_name="__tab__")
    except Exception as e: st.error(f"Phase: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "28_Powerplay_Deep.py"), run_name="__tab__")
    except Exception as e: st.error(f"Powerplay: {e}")
with tab3:
    try: runpy.run_path(str(Path(__file__).parent / "29_Death_Deep.py"), run_name="__tab__")
    except Exception as e: st.error(f"Death: {e}")
