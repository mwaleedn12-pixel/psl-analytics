"""Matchups Page — Batter vs Bowler and Team vs Team."""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.analytics.engines import MatchupEngine


from dashboard.components.style import inject_custom_css, PLOTLY_LAYOUT

st.title("⚔️ Matchups")
inject_custom_css()

@st.cache_data
def load_data():
    P = PROJECT_ROOT / "data" / "processed"
    m = pd.read_csv(P / "psl_matches_clean.csv")
    d = pd.read_csv(P / "psl_deliveries_clean.csv", low_memory=False)
    return m, d

matches, deliveries = load_data()

tab1, tab2 = st.tabs(["Batter vs Bowler", "Team vs Team"])

with tab1:
    col1, col2 = st.columns(2)
    batters = sorted(deliveries.batter.unique())
    bowlers = sorted(deliveries.bowler.unique())
    with col1:
        sel_batter = st.selectbox("Batter", batters, index=batters.index("Babar Azam") if "Babar Azam" in batters else 0)
    with col2:
        sel_bowler = st.selectbox("Bowler", bowlers, index=bowlers.index("Hasan Ali") if "Hasan Ali" in bowlers else 0)

    matchups = MatchupEngine.batter_vs_bowler(deliveries, min_balls=1)

    specific = matchups[(matchups.batter == sel_batter) & (matchups.bowler == sel_bowler)]
    if not specific.empty:
        r = specific.iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Balls", int(r.balls))
        c2.metric("Runs", int(r.runs))
        c3.metric("SR", f"{r.sr}")
        c4.metric("Dismissals", int(r.dismissals))
        c5.metric("Dots", int(r.dots))
    else:
        st.info("No head-to-head data found for this matchup.")

    st.markdown(f"**{sel_batter}'s record vs all bowlers** (min 12 balls)")
    batter_all = matchups[matchups.batter == sel_batter].sort_values("runs", ascending=False)
    batter_12 = batter_all[batter_all.balls >= 12]
    st.dataframe(batter_12[["bowler", "balls", "runs", "sr", "dots", "fours", "sixes", "dismissals"]].head(15),
                 use_container_width=True, hide_index=True)

with tab2:
    records = MatchupEngine.team_vs_team(matches)
    st.dataframe(records, use_container_width=True, hide_index=True)

    if not records.empty:
        fig = px.bar(records, x="team1", y="team1_win_pct", color="team2",
                     barmode="group", title="Head-to-Head Win %",
                     labels={"team1": "Team", "team1_win_pct": "Win %", "team2": "Opponent"})
        fig.update_layout(**PLOTLY_LAYOUT, height=450)
        st.plotly_chart(fig, use_container_width=True)