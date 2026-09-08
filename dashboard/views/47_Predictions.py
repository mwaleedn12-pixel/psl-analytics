"""Merged: Predictions"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("🔮 Predictions & Simulations", "Match Predictor · What-If · Simulator")
seam_divider()

tab1, tab2, tab3 = st.tabs(["🔮 Match Predictor", "❓ What-If", "🎮 Simulator"])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "10_Match_Predictor.py"), run_name="__tab__")
    except Exception as e: st.error(f"Predictor: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "8_Predictions.py"), run_name="__tab__")
    except Exception as e: st.error(f"What-If: {e}")
with tab3:
    try: runpy.run_path(str(Path(__file__).parent / "36_Match_Simulator.py"), run_name="__tab__")
    except Exception as e: st.error(f"Simulator: {e}")
