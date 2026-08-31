"""Player Comparison — Side-by-side radar comparison."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT
from src.analytics.premium import PlayerComparison

inject_custom_css()
hero_card("🆚 Player Comparison", "Side-by-side batting and bowling comparison with radar charts")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)

deliveries = load_data()
legal = deliveries[deliveries.is_legal == 1]
batters = sorted(legal.batter.unique())
bowlers = sorted(deliveries.bowler.unique())

tab1, tab2 = st.tabs(["⚡ Batting Comparison", "🎯 Bowling Comparison"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        p1 = st.selectbox("Player 1", batters, index=batters.index("Babar Azam") if "Babar Azam" in batters else 0)
    with col2:
        p2 = st.selectbox("Player 2", [b for b in batters if b != p1], index=0)

    comp = PlayerComparison.compare_batters(deliveries, p1, p2)
    s1, s2 = comp["player1"], comp["player2"]

    if s1 and s2:
        col1, col2 = st.columns(2)
        with col1:
            for k in ["innings", "runs", "avg", "sr", "boundary_pct", "dot_pct"]:
                label = k.replace("_", " ").title()
                delta = round(s1[k] - s2[k], 1) if isinstance(s1[k], float) else s1[k] - s2[k]
                st.metric(f"{label}", f"{s1[k]}", delta=f"{'+' if delta > 0 else ''}{delta} vs {p2}")
        with col2:
            for k in ["innings", "runs", "avg", "sr", "boundary_pct", "dot_pct"]:
                label = k.replace("_", " ").title()
                delta = round(s2[k] - s1[k], 1) if isinstance(s2[k], float) else s2[k] - s1[k]
                st.metric(f"{label}", f"{s2[k]}", delta=f"{'+' if delta > 0 else ''}{delta} vs {p1}")

        # Radar
        cats = ["Average", "Strike Rate", "Boundary%", "PP SR", "Middle SR", "Death SR"]
        max_vals = [max(s1["avg"], s2["avg"], 1), max(s1["sr"], s2["sr"], 1),
                    max(s1["boundary_pct"], s2["boundary_pct"], 1),
                    max(s1["sr_powerplay"], s2["sr_powerplay"], 1),
                    max(s1["sr_middle"], s2["sr_middle"], 1),
                    max(s1["sr_death"], s2["sr_death"], 1)]

        v1 = [s1["avg"]/max_vals[0]*100, s1["sr"]/max_vals[1]*100, s1["boundary_pct"]/max_vals[2]*100,
              s1["sr_powerplay"]/max_vals[3]*100, s1["sr_middle"]/max_vals[4]*100, s1["sr_death"]/max_vals[5]*100]
        v2 = [s2["avg"]/max_vals[0]*100, s2["sr"]/max_vals[1]*100, s2["boundary_pct"]/max_vals[2]*100,
              s2["sr_powerplay"]/max_vals[3]*100, s2["sr_middle"]/max_vals[4]*100, s2["sr_death"]/max_vals[5]*100]
        v1.append(v1[0]); v2.append(v2[0])
        cats_closed = cats + [cats[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=v1, theta=cats_closed, fill="toself", name=p1,
                                       fillcolor="rgba(201,243,77,0.15)", line=dict(color="#c9f34d", width=2)))
        fig.add_trace(go.Scatterpolar(r=v2, theta=cats_closed, fill="toself", name=p2,
                                       fillcolor="rgba(56,189,248,0.15)", line=dict(color="#38bdf8", width=2)))
        fig.update_layout(**PLOTLY_LAYOUT, title=f"{p1} vs {p2}",
                          polar=dict(bgcolor="rgba(0,0,0,0)",
                                     radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.05)"),
                                     angularaxis=dict(gridcolor="rgba(255,255,255,0.05)")),
                          height=500, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        b1 = st.selectbox("Bowler 1", bowlers, index=bowlers.index("Hasan Ali") if "Hasan Ali" in bowlers else 0, key="b1")
    with col2:
        b2 = st.selectbox("Bowler 2", [b for b in bowlers if b != b1], index=0, key="b2")

    bcomp = PlayerComparison.compare_bowlers(deliveries, b1, b2)
    bs1, bs2 = bcomp["player1"], bcomp["player2"]

    if bs1 and bs2:
        col1, col2 = st.columns(2)
        with col1:
            for k in ["innings", "wickets", "economy", "dot_pct", "bowling_sr"]:
                label = k.replace("_", " ").title()
                st.metric(f"{label}", f"{bs1[k]}")
        with col2:
            for k in ["innings", "wickets", "economy", "dot_pct", "bowling_sr"]:
                label = k.replace("_", " ").title()
                st.metric(f"{label}", f"{bs2[k]}")
