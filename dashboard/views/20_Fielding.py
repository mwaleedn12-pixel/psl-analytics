"""Fielding Analytics."""
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
hero_card("🧤 Fielding Analytics", "Catches, run-outs, stumpings — best fielders in PSL")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
deliveries = load_data()
fielding = StatsEngine.fielding_stats(deliveries)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Catches", int(fielding.catches.sum()))
c2.metric("Total Run-Outs", int(fielding.run_outs.sum()))
c3.metric("Total Stumpings", int(fielding.stumpings.sum()))
c4.metric("Total Dismissals", int(fielding.total_dismissals.sum()))

st.markdown("---")
top20 = fielding.head(20)
fig = go.Figure()
fig.add_trace(go.Bar(name="Catches", x=top20.player, y=top20.catches, marker=dict(color="#c9f34d")))
fig.add_trace(go.Bar(name="Run-Outs", x=top20.player, y=top20.run_outs, marker=dict(color="#38bdf8")))
fig.add_trace(go.Bar(name="Stumpings", x=top20.player, y=top20.stumpings, marker=dict(color="#c084fc")))
fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", title="TOP FIELDERS", height=450,
                  xaxis=dict(tickangle=-45))
st.plotly_chart(fig, use_container_width=True)

st.dataframe(fielding.head(30)[["player", "catches", "run_outs", "stumpings", "caught_bowled", "total_dismissals"]],
             use_container_width=True, hide_index=True)
