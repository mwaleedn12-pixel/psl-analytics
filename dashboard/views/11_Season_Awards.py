"""Season Awards — Best performers per PSL season."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT
from src.analytics.premium import SeasonAwards

inject_custom_css()
hero_card("🏆 Season Awards", "Best batter, bowler, all-rounder, and six-hitter per PSL season")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)

deliveries = load_data()
awards = SeasonAwards.compute(deliveries)

for _, row in awards.iterrows():
    st.markdown(f"### {row.season}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏏 Best Batter", row.best_batter, f"{row.batter_runs} runs (SR {row.batter_sr})")
    c2.metric("🎯 Best Bowler", row.best_bowler, f"{row.bowler_wickets} wkts (Econ {row.bowler_economy})")
    c3.metric("⭐ Best All-rounder", row.best_allrounder, f"{row.ar_runs}r / {row.ar_wickets}w")
    c4.metric("💥 Most Sixes", row.most_sixes_player, f"{row.most_sixes} sixes")
    st.markdown("---")
