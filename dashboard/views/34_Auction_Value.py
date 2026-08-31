"""Auction Value Estimator — estimated player value based on performance."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, fix_metrics
from src.analytics.stats_engine import StatsEngine

inject_custom_css()
fix_metrics()
hero_card("💰 Auction Value Estimator", "Estimated player market value based on PSL performance metrics")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv")
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()

# Base values (in PKR Lakhs)
BASE_BATTER = 50
BASE_BOWLER = 50
BASE_AR = 80

bat = StatsEngine.full_batting_stats(deliveries, min_innings=10)
bowl = StatsEngine.full_bowling_stats(deliveries, min_innings=10)

# Batting value
bat["bat_value"] = (
    BASE_BATTER
    + bat.runs / 50
    + bat.batting_avg * 2
    + np.clip(bat.sr - 120, 0, 80) * 1.5
    + bat.fifties * 5 + bat.hundreds * 20
    + bat.sixes * 0.5
    + np.where(bat.sr_death > 150, 30, 0)
).round(0).astype(int)

# Bowling value
bowl["bowl_value"] = (
    BASE_BOWLER
    + bowl.wickets * 3
    + np.clip(8 - bowl.economy, 0, 4) * 30
    + bowl.four_wickets * 10 + bowl.five_wickets * 25
    + bowl.dot_pct * 1.5
    + np.where(bowl.economy_death < 9, 30, 0)
).round(0).astype(int)

# Merge for all-rounders
ar = bat[["batter","bat_value","runs","batting_avg","sr"]].rename(columns={"batter":"player"})
ar_bowl = bowl[["bowler","bowl_value","wickets","economy"]].rename(columns={"bowler":"player"})
merged = ar.merge(ar_bowl, on="player", how="outer")
merged["bat_value"] = merged.bat_value.fillna(0).astype(int)
merged["bowl_value"] = merged.bowl_value.fillna(0).astype(int)
merged["total_value"] = merged.bat_value + merged.bowl_value
merged["category"] = np.where(
    (merged.bat_value > 0) & (merged.bowl_value > 0), "All-Rounder",
    np.where(merged.bat_value > 0, "Batter", "Bowler")
)
merged = merged.sort_values("total_value", ascending=False).reset_index(drop=True)

# Value tiers
def tier(val):
    if val >= 300: return "🔴 Platinum"
    elif val >= 200: return "🟡 Gold"
    elif val >= 120: return "🔵 Silver"
    else: return "⚪ Bronze"

merged["tier"] = merged.total_value.apply(tier)

# Display
c1, c2, c3 = st.columns(3)
c1.metric("Platinum Players", len(merged[merged.tier.str.contains("Platinum")]))
c2.metric("Gold Players", len(merged[merged.tier.str.contains("Gold")]))
c3.metric("Avg Value", f"{merged.total_value.mean():.0f} Lakhs")

st.markdown("---")

# Top 20 chart
top20 = merged.head(20)
tier_colors = {"🔴 Platinum": "#f87171", "🟡 Gold": "#fbbf24", "🔵 Silver": "#38bdf8", "⚪ Bronze": "#666"}
colors = [tier_colors.get(t, "#666") for t in top20.tier]

fig = go.Figure()
fig.add_trace(go.Bar(
    x=top20.total_value, y=top20.player, orientation="h",
    marker=dict(color=colors),
    text=[f"₨ {v}L ({t})" for v, t in zip(top20.total_value, top20.tier)],
    textposition="outside", textfont=dict(color="#7aaa8f", family="Share Tech Mono", size=10),
))
fig.update_layout(**PLOTLY_LAYOUT, title="ESTIMATED AUCTION VALUE", height=600, yaxis=dict(autorange="reversed"))
st.plotly_chart(fig, use_container_width=True)

st.dataframe(merged.head(40)[["player","category","tier","bat_value","bowl_value","total_value"]],
             use_container_width=True, hide_index=True)

st.markdown("<div style='color:#3a5a4a; font-size:0.7rem; margin-top:10px;'>⚠️ Values are estimated based on PSL performance data only — not actual auction prices.</div>", unsafe_allow_html=True)
