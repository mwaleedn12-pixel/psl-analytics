"""Merged: Season Hub"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("🏆 Seasons", "Explorer · Comparison · Awards")
seam_divider()

tab1, tab2, tab3 = st.tabs(["📋 Season Explorer", "🔄 Season Comparison", "🏅 Season Awards"])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "15_Season_Explorer.py"), run_name="__tab__")
    except Exception as e: st.error(f"Explorer: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "24_Season_Comparison.py"), run_name="__tab__")
    except Exception as e: st.error(f"Comparison: {e}")
with tab3:
    try: runpy.run_path(str(Path(__file__).parent / "11_Season_Awards.py"), run_name="__tab__")
    except Exception as e: st.error(f"Awards: {e}")
