"""Death Overs Deep Dive — overs 16-20."""
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
hero_card("💀 Death Overs Deep Dive", "Overs 16-20 — finishers, death bowlers, team rankings")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
deliveries = load_data()
death = deliveries[deliveries.phase == "death"]
death_legal = death[death.is_legal == 1]

death_innings = death.groupby(["match_id","innings"]).agg(
    runs=("total_runs","sum"), wkts=("is_wicket","sum"),
    sixes=("is_six","sum"),
).reset_index()

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Avg Death Score", f"{death_innings.runs.mean():.1f}")
c2.metric("Highest Death", int(death_innings.runs.max()))
c3.metric("Avg Wickets", f"{death_innings.wkts.mean():.1f}")
c4.metric("Total 6s", int(death_innings.sixes.sum()))
c5.metric("Run Rate", f"{death.total_runs.sum()/(death_legal.is_legal.sum()/6):.2f}")

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 🏏 Best Finishers")
    bat = death_legal.groupby("batter").agg(
        inn=("match_id","nunique"), runs=("batter_runs","sum"),
        balls=("batter_runs","count"), fours=("is_four","sum"), sixes=("is_six","sum"),
    ).reset_index()
    bat["sr"] = (bat.runs/bat.balls*100).round(1)
    bat = bat[bat.inn >= 10].sort_values("sr", ascending=False)
    st.dataframe(bat.head(15)[["batter","inn","runs","sr","fours","sixes"]],
                 use_container_width=True, hide_index=True)

with col2:
    st.markdown("##### 🎯 Best Death Bowlers")
    bowl = death.groupby("bowler").agg(
        inn=("match_id","nunique"), legal=("is_legal","sum"),
        runs_c=("total_runs","sum"), wkts=("is_wicket","sum"), dots=("is_dot","sum"),
    ).reset_index()
    bowl["overs"] = (bowl.legal/6).round(1)
    bowl["econ"] = np.where(bowl.overs>0,(bowl.runs_c/bowl.overs).round(2),0)
    bowl["dot_pct"] = (bowl.dots/bowl.legal*100).round(1)
    bowl = bowl[bowl.inn >= 10].sort_values("econ")
    st.dataframe(bowl.head(15)[["bowler","inn","wkts","econ","dot_pct","overs"]],
                 use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("##### 👥 Team Death Overs Rankings")
team_d = death.groupby("batting_team").agg(
    innings=("match_id","nunique"), runs=("total_runs","sum"),
    legal=("is_legal","sum"),
).reset_index()
team_d["avg_score"] = (team_d.runs/team_d.innings).round(1)
team_d = team_d.sort_values("avg_score", ascending=False)

colors = get_team_bar_colors(team_d.batting_team)
fig = go.Figure()
fig.add_trace(go.Bar(x=team_d.batting_team, y=team_d.avg_score,
                     marker=dict(color=colors),
                     text=[f"{v}" for v in team_d.avg_score],
                     textposition="outside", textfont=dict(color="#f87171", family="Share Tech Mono")))
fig.update_layout(**PLOTLY_LAYOUT, title="AVG DEATH OVERS SCORE BY TEAM", height=400)
st.plotly_chart(fig, use_container_width=True)
