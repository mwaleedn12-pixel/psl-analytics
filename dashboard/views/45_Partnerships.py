"""Merged: Partnerships & Fielding"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("🤝 Partnerships & Fielding", "Partnerships · Fielding · Dismissals")
seam_divider()

tab1, tab2, tab3 = st.tabs(["🤝 Partnerships", "🏃 Fielding", "❌ Dismissals"])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "19_Partnerships.py"), run_name="__tab__")
    except Exception as e: st.error(f"Partnerships: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "20_Fielding.py"), run_name="__tab__")
    except Exception as e: st.error(f"Fielding: {e}")
with tab3:
    try: runpy.run_path(str(Path(__file__).parent / "18_Dismissals.py"), run_name="__tab__")
    except Exception as e: st.error(f"Dismissals: {e}")
