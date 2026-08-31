"""PSL Records — All-time records and milestones."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT

inject_custom_css()
hero_card("📜 PSL Records", "All-time highs, milestones, and record-breaking performances")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d

matches, deliveries = load_data()
legal = deliveries[deliveries.is_legal == 1]

tab1, tab2, tab3, tab4 = st.tabs(["🏏 Batting Records", "🎯 Bowling Records", "👥 Team Records", "💥 Match Records"])

with tab1:
    # Highest individual scores
    innings_scores = legal.groupby(["match_id", "batter", "psl_edition", "batting_team"]).agg(
        runs=("batter_runs", "sum"), balls=("batter_runs", "count"),
        fours=("is_four", "sum"), sixes=("is_six", "sum"),
    ).reset_index()
    innings_scores["sr"] = (innings_scores.runs / innings_scores.balls * 100).round(1)
    top_scores = innings_scores.nlargest(15, "runs")

    st.markdown("##### 🔥 Highest Individual Scores")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top_scores["runs"], y=top_scores.apply(lambda r: f"{r.batter} ({r.psl_edition})", axis=1),
        orientation="h",
        marker=dict(color=top_scores["sr"], colorscale=[[0,"#38bdf8"],[1,"#c9f34d"]],
                    colorbar=dict(title="SR")),
        text=[f"{int(r)}({int(b)}) SR:{s}" for r,b,s in zip(top_scores.runs, top_scores.balls, top_scores.sr)],
        textposition="outside", textfont=dict(color="#7aaa8f", size=10, family="Share Tech Mono"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=500, yaxis=dict(autorange="reversed"), title="")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Most runs in career
    career = legal.groupby("batter").agg(
        innings=("match_id", "nunique"), runs=("batter_runs", "sum"),
        balls=("batter_runs", "count"), fours=("is_four", "sum"), sixes=("is_six", "sum"),
    ).reset_index()
    career["sr"] = (career.runs / career.balls * 100).round(1)
    career["avg"] = (career.runs / career.innings).round(1)

    st.markdown("##### 🏅 Most Career Runs")
    st.dataframe(career.nlargest(20, "runs")[["batter", "innings", "runs", "avg", "sr", "fours", "sixes"]],
                 use_container_width=True, hide_index=True)

    # Most sixes
    st.markdown("##### 💥 Most Career Sixes")
    st.dataframe(career.nlargest(15, "sixes")[["batter", "innings", "sixes", "runs", "sr"]],
                 use_container_width=True, hide_index=True)

with tab2:
    # Best bowling figures
    bowl_innings = deliveries.groupby(["match_id", "bowler", "psl_edition", "bowling_team"]).agg(
        legal_balls=("is_legal", "sum"), runs_conceded=("total_runs", "sum"),
        wickets=("is_wicket", "sum"), dots=("is_dot", "sum"),
    ).reset_index()
    bowl_innings["overs"] = (bowl_innings.legal_balls / 6).round(1)
    bowl_innings["economy"] = np.where(bowl_innings.overs > 0, (bowl_innings.runs_conceded / bowl_innings.overs).round(2), 0)
    best_figures = bowl_innings.nlargest(15, "wickets")

    st.markdown("##### 🎯 Best Bowling Figures (Single Match)")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=best_figures["wickets"],
        y=best_figures.apply(lambda r: f"{r.bowler} ({r.psl_edition})", axis=1),
        orientation="h",
        marker=dict(color=best_figures["economy"], colorscale=[[0,"#c9f34d"],[1,"#f87171"]],
                    colorbar=dict(title="Econ")),
        text=[f"{int(w)}/{int(r)} ({o}ov)" for w,r,o in zip(best_figures.wickets, best_figures.runs_conceded, best_figures.overs)],
        textposition="outside", textfont=dict(color="#7aaa8f", size=10, family="Share Tech Mono"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=500, yaxis=dict(autorange="reversed"), title="")
    st.plotly_chart(fig, use_container_width=True)

    # Most career wickets
    career_bowl = deliveries.groupby("bowler").agg(
        innings=("match_id", "nunique"), legal_balls=("is_legal", "sum"),
        runs_conceded=("total_runs", "sum"), wickets=("is_wicket", "sum"),
    ).reset_index()
    career_bowl["overs"] = (career_bowl.legal_balls / 6).round(1)
    career_bowl["economy"] = np.where(career_bowl.overs > 0, (career_bowl.runs_conceded / career_bowl.overs).round(2), 0)
    career_bowl["bowling_sr"] = np.where(career_bowl.wickets > 0, (career_bowl.legal_balls / career_bowl.wickets).round(1), 0)

    st.markdown("##### 🏅 Most Career Wickets")
    st.dataframe(career_bowl.nlargest(20, "wickets")[["bowler", "innings", "wickets", "economy", "bowling_sr"]],
                 use_container_width=True, hide_index=True)

with tab3:
    # Highest team totals
    team_totals = deliveries.groupby(["match_id", "innings", "batting_team", "psl_edition"]).agg(
        total=("total_runs", "sum"), wickets=("is_wicket", "sum"),
        fours=("is_four", "sum"), sixes=("is_six", "sum"),
    ).reset_index()

    st.markdown("##### 🔥 Highest Team Totals")
    top_totals = team_totals.nlargest(15, "total")
    st.dataframe(top_totals[["batting_team", "total", "wickets", "fours", "sixes", "psl_edition"]],
                 use_container_width=True, hide_index=True)

    st.markdown("##### 😱 Lowest Team Totals")
    low_totals = team_totals[team_totals.wickets == 10].nsmallest(15, "total")
    if len(low_totals) == 0:
        low_totals = team_totals.nsmallest(15, "total")
    st.dataframe(low_totals[["batting_team", "total", "wickets", "psl_edition"]],
                 use_container_width=True, hide_index=True)

with tab4:
    # Biggest wins (by runs)
    run_wins = matches[matches.win_by_runs.notna()].nlargest(10, "win_by_runs")
    st.markdown("##### 🏆 Biggest Wins (by Runs)")
    st.dataframe(run_wins[["winner", "team1", "team2", "win_by_runs", "venue", "psl_edition"]],
                 use_container_width=True, hide_index=True)

    # Biggest chases
    wkt_wins = matches[matches.win_by_wickets.notna()].copy()
    # Get target (innings 1 total + 1)
    inn1 = deliveries[deliveries.innings == 1].groupby("match_id")["total_runs"].sum().reset_index()
    inn1.columns = ["match_id", "target_minus_1"]
    inn1["match_id"] = inn1.match_id.astype(str)
    wkt_wins["match_id"] = wkt_wins.match_id.astype(str)
    wkt_wins = wkt_wins.merge(inn1, on="match_id", how="left")
    wkt_wins["target"] = wkt_wins["target_minus_1"] + 1
    biggest_chases = wkt_wins.nlargest(10, "target")
    st.markdown("##### 🎯 Highest Successful Chases")
    st.dataframe(biggest_chases[["winner", "team1", "team2", "target", "win_by_wickets", "venue", "psl_edition"]],
                 use_container_width=True, hide_index=True)
