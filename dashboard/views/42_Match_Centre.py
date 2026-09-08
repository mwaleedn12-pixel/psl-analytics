"""Merged: Match Centre = Explorer + Intelligence"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("🏟️ Match Centre", "Explorer · Intelligence")
seam_divider()

tab1, tab2 = st.tabs(["📋 Match Explorer", "🧠 Match Intelligence"])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "21_Match_Explorer.py"), run_name="__tab__")
    except Exception as e: st.error(f"Explorer: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "7_Match_Intelligence.py"), run_name="__tab__")
    except Exception as e: st.error(f"Intelligence: {e}")
