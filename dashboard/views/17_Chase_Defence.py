"""Chase & Defence Analytics."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT
from src.analytics.stats_engine import StatsEngine

inject_custom_css()
hero_card("🎯 Chase & Defence Analytics", "Success rates by target range, highest chases, lowest defended scores")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()
chase = StatsEngine.chase_analytics(deliveries, matches)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Chase Wins", chase["overall"]["total_chases"])
c2.metric("Defence Wins", chase["overall"]["total_defences"])
c3.metric("Chase Success", f"{chase['overall']['chase_pct']}%")
c4.metric("Highest Chase", chase["overall"]["highest_chase"])

st.markdown("---")
st.markdown("##### Chase Success by Target Range")
rng = chase["by_range"]
fig = go.Figure()
fig.add_trace(go.Bar(
    x=rng.target_range.astype(str), y=rng.chase_pct,
    marker=dict(color=["#c9f34d" if v > 50 else "#f87171" for v in rng.chase_pct]),
    text=[f"{v}%" for v in rng.chase_pct],
    textposition="outside", textfont=dict(color="#c9f34d", size=14, family="Share Tech Mono"),
))
fig.add_hline(y=50, line_dash="dot", line_color="rgba(201,243,77,0.2)")
layout3 = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")}
fig.update_layout(**layout3, height=400, xaxis_title="Target Range", yaxis_title="Chase Win %",
                  yaxis=dict(range=[0, 100]))
st.plotly_chart(fig, use_container_width=True)
st.dataframe(rng, use_container_width=True, hide_index=True)
