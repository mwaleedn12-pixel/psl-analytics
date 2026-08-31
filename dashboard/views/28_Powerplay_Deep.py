"""Powerplay Deep Dive — dedicated powerplay analytics."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, get_team_bar_colors, fix_metrics

inject_custom_css()
fix_metrics()
hero_card("🚀 Powerplay Deep Dive", "Overs 1-6 — scoring, wickets, best performers, team rankings")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
deliveries = load_data()
pp = deliveries[deliveries.phase == "powerplay"]
pp_legal = pp[pp.is_legal == 1]

# Overall KPIs
pp_innings = pp.groupby(["match_id","innings"]).agg(
    runs=("total_runs","sum"), wkts=("is_wicket","sum"),
    fours=("is_four","sum"), sixes=("is_six","sum"),
).reset_index()

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Avg PP Score", f"{pp_innings.runs.mean():.1f}")
c2.metric("Highest PP", int(pp_innings.runs.max()))
c3.metric("Lowest PP", int(pp_innings.runs.min()))
c4.metric("Avg Wickets", f"{pp_innings.wkts.mean():.1f}")
c5.metric("Run Rate", f"{pp.total_runs.sum() / (pp_legal.is_legal.sum()/6):.2f}")

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 🏏 Best PP Batters")
    bat = pp_legal.groupby("batter").agg(
        inn=("match_id","nunique"), runs=("batter_runs","sum"),
        balls=("batter_runs","count"), fours=("is_four","sum"), sixes=("is_six","sum"),
    ).reset_index()
    bat["sr"] = (bat.runs/bat.balls*100).round(1)
    bat = bat[bat.inn >= 10].sort_values("runs", ascending=False)
    st.dataframe(bat.head(15)[["batter","inn","runs","sr","fours","sixes"]],
                 use_container_width=True, hide_index=True)

with col2:
    st.markdown("##### 🎯 Best PP Bowlers")
    bowl = pp.groupby("bowler").agg(
        inn=("match_id","nunique"), legal=("is_legal","sum"),
        runs_c=("total_runs","sum"), wkts=("is_wicket","sum"),
    ).reset_index()
    bowl["overs"] = (bowl.legal/6).round(1)
    bowl["econ"] = np.where(bowl.overs>0,(bowl.runs_c/bowl.overs).round(2),0)
    bowl = bowl[bowl.inn >= 10].sort_values("wkts", ascending=False)
    st.dataframe(bowl.head(15)[["bowler","inn","wkts","econ","overs"]],
                 use_container_width=True, hide_index=True)

# Team PP rankings
st.markdown("---")
st.markdown("##### 👥 Team Powerplay Rankings")
team_pp = pp.groupby("batting_team").agg(
    innings=("match_id","nunique"), runs=("total_runs","sum"),
    legal=("is_legal","sum"), wkts=("is_wicket","sum"),
).reset_index()
team_pp["avg_score"] = (team_pp.runs/team_pp.innings).round(1)
team_pp["rr"] = (team_pp.runs/(team_pp.legal/6)).round(2)
team_pp = team_pp.sort_values("avg_score", ascending=False)

colors = get_team_bar_colors(team_pp.batting_team)
fig = go.Figure()
fig.add_trace(go.Bar(x=team_pp.batting_team, y=team_pp.avg_score,
                     marker=dict(color=colors),
                     text=[f"{v}" for v in team_pp.avg_score],
                     textposition="outside", textfont=dict(color="#c9f34d", family="Share Tech Mono")))
fig.update_layout(**PLOTLY_LAYOUT, title="AVG POWERPLAY SCORE BY TEAM", height=400)
st.plotly_chart(fig, use_container_width=True)
