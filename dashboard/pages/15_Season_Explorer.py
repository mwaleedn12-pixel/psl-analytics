"""Season Explorer — deep dive into any PSL season."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, get_team_bar_colors

inject_custom_css()
hero_card("📅 Season Explorer", "Deep dive into any PSL season — team standings, top performers, stats")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d

matches, deliveries = load_data()
seasons = sorted(matches.psl_edition.unique(), key=lambda x: matches[matches.psl_edition == x].season_year.iloc[0])

selected_season = st.selectbox("Select Season", seasons, index=len(seasons)-1)
s_matches = matches[matches.psl_edition == selected_season]
s_del = deliveries[deliveries.psl_edition == selected_season]
legal = s_del[s_del.is_legal == 1]

# Season KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Matches", len(s_matches))
col2.metric("Total Runs", f"{s_del.total_runs.sum():,}")
col3.metric("Wickets", int(s_del.is_wicket.sum()))
col4.metric("Sixes", int(s_del.is_six.sum()))

st.markdown("---")

# Team Standings
st.markdown("##### 🏆 Team Standings")
team_list = []
for _, row in s_matches.iterrows():
    for team in [row.team1, row.team2]:
        team_list.append({"team": team, "won": 1 if team == row.winner else 0})
team_df = pd.DataFrame(team_list)
standings = team_df.groupby("team").agg(played=("won", "count"), won=("won", "sum")).reset_index()
standings["lost"] = standings.played - standings.won
standings["win_pct"] = (standings.won / standings.played * 100).round(1)
standings = standings.sort_values("win_pct", ascending=False).reset_index(drop=True)
standings.index = standings.index + 1
standings.index.name = "Rank"

bar_colors = get_team_bar_colors(standings.team)
fig = go.Figure()
fig.add_trace(go.Bar(
    x=standings.win_pct, y=standings.team, orientation="h",
    marker=dict(color=bar_colors),
    text=[f"{w}W-{l}L ({p}%)" for w,l,p in zip(standings.won, standings.lost, standings.win_pct)],
    textposition="outside", textfont=dict(color="#7aaa8f", family="Share Tech Mono", size=11),
))
fig.update_layout(**PLOTLY_LAYOUT, height=350, yaxis=dict(autorange="reversed"), title="")
st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 🏏 Top Batters")
    bat = legal.groupby("batter").agg(
        inn=("match_id", "nunique"), runs=("batter_runs", "sum"),
        balls=("batter_runs", "count"), fours=("is_four", "sum"), sixes=("is_six", "sum"),
    ).reset_index()
    bat["sr"] = (bat.runs / bat.balls * 100).round(1)
    bat["avg"] = (bat.runs / bat.inn).round(1)
    st.dataframe(bat.nlargest(10, "runs")[["batter", "inn", "runs", "avg", "sr", "fours", "sixes"]],
                 use_container_width=True, hide_index=True)

with col2:
    st.markdown("##### 🎯 Top Bowlers")
    bowl = s_del.groupby("bowler").agg(
        inn=("match_id", "nunique"), legal_balls=("is_legal", "sum"),
        runs_conceded=("total_runs", "sum"), wickets=("is_wicket", "sum"),
    ).reset_index()
    bowl["overs"] = (bowl.legal_balls / 6).round(1)
    bowl["economy"] = (bowl.runs_conceded / bowl.overs).round(2)
    st.dataframe(bowl.nlargest(10, "wickets")[["bowler", "inn", "wickets", "economy", "overs"]],
                 use_container_width=True, hide_index=True)

# Player of the matches
st.markdown("---")
st.markdown("##### 🌟 Players of the Match")
pom = s_matches[s_matches.player_of_match.notna()].groupby("player_of_match").size().reset_index(name="awards")
pom = pom.sort_values("awards", ascending=False)
st.dataframe(pom.head(10), use_container_width=True, hide_index=True)
