"""Merged: PSL History"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("📜 PSL History & Records", "History · Playoffs · Super Overs · Records")
seam_divider()

tab1, tab2, tab3, tab4 = st.tabs(["📜 PSL History", "🏆 Playoffs", "⚡ Super Overs", "📊 Records"])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "26_PSL_History.py"), run_name="__tab__")
    except Exception as e: st.error(f"History: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "30_Playoffs.py"), run_name="__tab__")
    except Exception as e: st.error(f"Playoffs: {e}")
with tab3:
    try: runpy.run_path(str(Path(__file__).parent / "25_Super_Overs.py"), run_name="__tab__")
    except Exception as e: st.error(f"Super Overs: {e}")
with tab4:
    try: runpy.run_path(str(Path(__file__).parent / "14_Records.py"), run_name="__tab__")
    except Exception as e: st.error(f"Records: {e}")
