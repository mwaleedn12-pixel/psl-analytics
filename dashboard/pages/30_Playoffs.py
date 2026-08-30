"""Playoffs Dashboard — playoff-specific stats, regular vs playoffs comparison."""
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
hero_card("🏆 Playoffs Dashboard", "Playoff-specific performance — qualifiers, eliminators, finals")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()

# Identify playoff matches — typically last 3-4 matches per season
# Heuristic: matches with match_number > total_league_matches or last 4 per season
playoff_ids = set()
regular_ids = set()
for season in matches.psl_edition.unique():
    s_matches = matches[matches.psl_edition == season].sort_values("date")
    n = len(s_matches)
    # Last 4 matches are typically playoffs (Qualifier, Eliminator, Qualifier 2, Final)
    playoff_count = min(4, max(1, n - (n - 4)))
    playoffs = s_matches.tail(4)
    regulars = s_matches.head(n - 4) if n > 4 else s_matches.head(0)
    playoff_ids.update(playoffs.match_id.values)
    regular_ids.update(regulars.match_id.values)

playoff_matches = matches[matches.match_id.isin(playoff_ids)]
regular_matches = matches[matches.match_id.isin(regular_ids)]
playoff_del = deliveries[deliveries.match_id.isin(playoff_ids)]
regular_del = deliveries[deliveries.match_id.isin(regular_ids)]

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Playoff Matches", len(playoff_matches))
c2.metric("Regular Matches", len(regular_matches))
pl_avg = playoff_del.groupby(["match_id","innings"])["total_runs"].sum().mean()
rg_avg = regular_del.groupby(["match_id","innings"])["total_runs"].sum().mean()
c3.metric("Playoff Avg Score", f"{pl_avg:.0f}")
c4.metric("Regular Avg Score", f"{rg_avg:.0f}")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Regular vs Playoffs", "👥 Team Records", "🏏 Top Performers"])

with tab1:
    # Comparison
    def phase_stats(d):
        legal = d[d.is_legal == 1]
        return {
            "Avg Score": round(d.groupby(["match_id","innings"])["total_runs"].sum().mean(), 1),
            "Avg SR": round(legal.batter_runs.sum() / len(legal) * 100, 1) if len(legal) > 0 else 0,
            "Avg Wickets": round(d.groupby(["match_id","innings"])["is_wicket"].sum().mean(), 1),
            "6s/Match": round(d.is_six.sum() / d.match_id.nunique(), 1),
            "4s/Match": round(d.is_four.sum() / d.match_id.nunique(), 1),
        }

    reg_stats = phase_stats(regular_del)
    pl_stats = phase_stats(playoff_del)

    metrics = list(reg_stats.keys())
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Regular Season", x=metrics, y=list(reg_stats.values()),
                         marker=dict(color="#38bdf8")))
    fig.add_trace(go.Bar(name="Playoffs", x=metrics, y=list(pl_stats.values()),
                         marker=dict(color="#c9f34d")))
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", title="REGULAR SEASON vs PLAYOFFS", height=420)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Team playoff record
    teams = sorted(set(playoff_matches.team1) | set(playoff_matches.team2))
    records = []
    for team in teams:
        tm = playoff_matches[(playoff_matches.team1 == team) | (playoff_matches.team2 == team)]
        wins = len(tm[tm.winner == team])
        records.append({"team": team, "played": len(tm), "won": wins,
                        "lost": len(tm) - wins,
                        "win_pct": round(wins / len(tm) * 100, 1) if len(tm) > 0 else 0})

    rec_df = pd.DataFrame(records).sort_values("win_pct", ascending=False)
    colors = get_team_bar_colors(rec_df.team)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=rec_df.win_pct, y=rec_df.team, orientation="h",
        marker=dict(color=colors),
        text=[f"{int(w)}W-{int(l)}L ({p}%)" for w, l, p in zip(rec_df.won, rec_df.lost, rec_df.win_pct)],
        textposition="outside", textfont=dict(color="#7aaa8f", family="Share Tech Mono", size=11),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, title="PLAYOFF WIN %", height=400, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    pl_legal = playoff_del[playoff_del.is_legal == 1]

    with col1:
        st.markdown("##### 🏏 Top Playoff Batters")
        bat = pl_legal.groupby("batter").agg(
            inn=("match_id","nunique"), runs=("batter_runs","sum"),
            balls=("batter_runs","count"),
        ).reset_index()
        bat["sr"] = (bat.runs / bat.balls * 100).round(1)
        bat["avg"] = (bat.runs / bat.inn).round(1)
        bat = bat[bat.inn >= 3].sort_values("runs", ascending=False)
        st.dataframe(bat.head(15)[["batter","inn","runs","avg","sr"]],
                     use_container_width=True, hide_index=True)

    with col2:
        st.markdown("##### 🎯 Top Playoff Bowlers")
        bowl = playoff_del.groupby("bowler").agg(
            inn=("match_id","nunique"), legal=("is_legal","sum"),
            runs_c=("total_runs","sum"), wkts=("is_wicket","sum"),
        ).reset_index()
        bowl["overs"] = (bowl.legal / 6).round(1)
        bowl["econ"] = np.where(bowl.overs > 0, (bowl.runs_c / bowl.overs).round(2), 0)
        bowl = bowl[bowl.inn >= 3].sort_values("wkts", ascending=False)
        st.dataframe(bowl.head(15)[["bowler","inn","wkts","econ","overs"]],
                     use_container_width=True, hide_index=True)
