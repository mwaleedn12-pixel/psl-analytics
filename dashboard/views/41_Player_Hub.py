"""Merged: Player Hub = Profile + Form + Rankings + Analytics + Auction Value + Comparison"""
import streamlit as st, sys, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
inject_custom_css(); fix_metrics()

hero_card("🏏 Player Hub", "Profile · Form · Rankings · Analytics · Auction Value · Compare")
seam_divider()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "👤 Profile", "📈 Form", "🏆 Rankings", "📊 Analytics", "💰 Auction Value", "🔄 Compare"
])
with tab1:
    try: runpy.run_path(str(Path(__file__).parent / "23_Player_Profile.py"), run_name="__tab__")
    except Exception as e: st.error(f"Profile: {e}")
with tab2:
    try: runpy.run_path(str(Path(__file__).parent / "6_Player_Form.py"), run_name="__tab__")
    except Exception as e: st.error(f"Form: {e}")
with tab3:
    try: runpy.run_path(str(Path(__file__).parent / "33_Player_Rankings.py"), run_name="__tab__")
    except Exception as e: st.error(f"Rankings: {e}")
with tab4:
    try: runpy.run_path(str(Path(__file__).parent / "1_Player_Analytics.py"), run_name="__tab__")
    except Exception as e: st.error(f"Analytics: {e}")
with tab5:
    try: runpy.run_path(str(Path(__file__).parent / "34_Auction_Value.py"), run_name="__tab__")
    except Exception as e: st.error(f"Auction Value: {e}")
with tab6:
    try: runpy.run_path(str(Path(__file__).parent / "12_Player_Comparison.py"), run_name="__tab__")
    except Exception as e: st.error(f"Comparison: {e}")
