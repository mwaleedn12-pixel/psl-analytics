"""PSL Leaderboard — filterable rankings."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, fix_metrics
from src.analytics.stats_engine import StatsEngine

inject_custom_css()
fix_metrics()
hero_card("🥇 PSL Leaderboard", "Filter by season, team — rank by any stat")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
deliveries = load_data()

col1, col2, col3 = st.columns(3)
with col1:
    seasons = ["All Time"] + sorted(deliveries.psl_edition.unique())
    season_filter = st.selectbox("Season", seasons)
with col2:
    teams = ["All Teams"] + sorted(deliveries.batting_team.unique())
    team_filter = st.selectbox("Team", teams)
with col3:
    min_inn = st.slider("Min Innings", 1, 30, 5)

# Apply filters
d = deliveries.copy()
if season_filter != "All Time":
    d = d[d.psl_edition == season_filter]

tab1, tab2, tab3 = st.tabs(["🏏 Batting", "🎯 Bowling", "🧤 Fielding"])

with tab1:
    d_bat = d.copy()
    if team_filter != "All Teams":
        d_bat = d_bat[d_bat.batting_team == team_filter]

    bat = StatsEngine.full_batting_stats(d_bat, min_innings=min_inn)
    stat = st.selectbox("Rank By", ["runs", "batting_avg", "sr", "fifties", "hundreds", "sixes",
                                     "fours", "highest_score", "boundary_pct", "dot_pct",
                                     "sr_death", "ducks"], key="bat_rank")
    asc = stat in ["dot_pct", "ducks"]
    bat_sorted = bat.sort_values(stat, ascending=asc).head(30)
    st.dataframe(bat_sorted[["batter", "innings", "runs", "batting_avg", "sr", "highest_score",
                              "fifties", "hundreds", "ducks", "not_outs", "fours", "sixes",
                              "boundary_pct", "dot_pct"]],
                 use_container_width=True, hide_index=True)

with tab2:
    d_bowl = d.copy()
    if team_filter != "All Teams":
        d_bowl = d_bowl[d_bowl.bowling_team == team_filter]

    bowl = StatsEngine.full_bowling_stats(d_bowl, min_innings=min_inn)
    stat_b = st.selectbox("Rank By", ["wickets", "economy", "bowling_avg", "bowling_sr",
                                       "dot_pct", "four_wickets", "five_wickets"], key="bowl_rank")
    asc_b = stat_b in ["economy", "bowling_avg", "bowling_sr"]
    bowl_sorted = bowl.sort_values(stat_b, ascending=asc_b).head(30)
    st.dataframe(bowl_sorted[["bowler", "innings", "wickets", "economy", "bowling_avg", "bowling_sr",
                               "best_figures", "three_wickets", "four_wickets", "five_wickets",
                               "dot_pct", "overs"]],
                 use_container_width=True, hide_index=True)

with tab3:
    fielding = StatsEngine.fielding_stats(d)
    st.dataframe(fielding.head(30)[["player", "catches", "run_outs", "stumpings", "caught_bowled", "total_dismissals"]],
                 use_container_width=True, hide_index=True)