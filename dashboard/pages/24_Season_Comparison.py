"""Season Comparison — compare any two PSL seasons side by side."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, fix_metrics

inject_custom_css()
fix_metrics()
hero_card("📊 Season Comparison", "Compare any two PSL seasons — how the tournament has evolved")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv")
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()
seasons = sorted(deliveries.psl_edition.unique(), key=lambda x: deliveries[deliveries.psl_edition==x].season_year.iloc[0])

col1, col2 = st.columns(2)
with col1: s1 = st.selectbox("Season 1", seasons, index=0)
with col2: s2 = st.selectbox("Season 2", seasons, index=len(seasons)-1)

def season_stats(d, m, season):
    sd = d[d.psl_edition == season]
    sm = m[m.psl_edition == season]
    legal = sd[sd.is_legal == 1]
    innings = sd.groupby(["match_id","innings"])["total_runs"].sum()
    return {
        "Matches": len(sm),
        "Total Runs": int(sd.total_runs.sum()),
        "Total Wickets": int(sd.is_wicket.sum()),
        "Avg Score": round(innings.mean(), 1),
        "Total 4s": int(sd.is_four.sum()),
        "Total 6s": int(sd.is_six.sum()),
        "Avg SR": round(legal.batter_runs.sum() / len(legal) * 100, 1),
        "Avg Economy": round(sd.total_runs.sum() / (legal.is_legal.sum() / 6), 2),
        "Boundaries/Match": round((sd.is_four.sum() + sd.is_six.sum()) / len(sm), 1),
    }

st1 = season_stats(deliveries, matches, s1)
st2 = season_stats(deliveries, matches, s2)

# Comparison table
metrics = list(st1.keys())
for metric in metrics:
    col1, col2, col3 = st.columns([2, 1, 2])
    v1, v2 = st1[metric], st2[metric]
    diff = v2 - v1 if isinstance(v1, (int, float)) else 0
    with col1: st.metric(f"{s1}", v1)
    with col2: st.markdown(f"<div style='text-align:center; padding:20px 0; font-family:Oswald; color:#5a8a6f; font-size:0.8rem; text-transform:uppercase;'>{metric}</div>", unsafe_allow_html=True)
    with col3: st.metric(f"{s2}", v2, delta=f"{'+' if diff>0 else ''}{diff:.1f}" if diff != 0 else None)

# Bar comparison chart
st.markdown("---")
fig = go.Figure()
fig.add_trace(go.Bar(name=s1, x=["Avg Score","Total 6s","Avg SR","Boundaries/Match"],
                     y=[st1["Avg Score"],st1["Total 6s"],st1["Avg SR"],st1["Boundaries/Match"]],
                     marker=dict(color="#c9f34d")))
fig.add_trace(go.Bar(name=s2, x=["Avg Score","Total 6s","Avg SR","Boundaries/Match"],
                     y=[st2["Avg Score"],st2["Total 6s"],st2["Avg SR"],st2["Boundaries/Match"]],
                     marker=dict(color="#f0b429")))
fig.update_layout(**PLOTLY_LAYOUT, barmode="group", title="SEASON COMPARISON", height=400)
st.plotly_chart(fig, use_container_width=True)
