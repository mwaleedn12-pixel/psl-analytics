"""Team Profile — Complete team stats, records, history, and performance breakdown."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS

inject_custom_css()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d

matches, deliveries = load_data()
teams = sorted(set(matches.team1) | set(matches.team2))

team = st.sidebar.selectbox("🏏 Select Team", teams, key="team_profile_sel")
tc = TEAM_COLORS.get(team, {"primary": "#c9f34d", "secondary": "#1a1a2e", "accent": "#c9f34d"})

hero_card(f"🏏 {team}", "Complete franchise profile — stats, records, players, seasons, venues")
seam_divider()

# ── Filter team data ──
team_matches = matches[(matches.team1 == team) | (matches.team2 == team)].copy()
team_matches["won"] = (team_matches.winner == team).astype(int)
team_bat = deliveries[deliveries.batting_team == team]
team_bowl = deliveries[deliveries.bowling_team == team]
legal_bat = team_bat[team_bat.is_legal == 1]

total_played = len(team_matches)
total_won = team_matches.won.sum()
total_lost = total_played - total_won
win_pct = round(total_won / total_played * 100, 1) if total_played > 0 else 0

# ════════════════════════════════════════
# KPI ROW
# ════════════════════════════════════════
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Played", total_played)
c2.metric("Won", total_won)
c3.metric("Lost", total_lost)
c4.metric("Win %", f"{win_pct}%")
c5.metric("Total Runs", f"{team_bat.total_runs.sum():,}")
c6.metric("Seasons", team_matches.psl_edition.nunique())

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Season History", "🏏 Batting", "🎯 Bowling",
    "⏱️ Phase Wise", "🏟️ Venue Records", "⚔️ vs Opponents"
])

# ════════════════════════════════════════
# TAB 1: SEASON HISTORY
# ════════════════════════════════════════
with tab1:
    season_perf = team_matches.groupby(["psl_edition", "season_year"]).agg(
        played=("match_id", "count"), won=("won", "sum"),
    ).reset_index().sort_values("season_year")
    season_perf["lost"] = season_perf.played - season_perf.won
    season_perf["win_pct"] = (season_perf.won / season_perf.played * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Won", x=season_perf.psl_edition, y=season_perf.won,
                         marker=dict(color=tc["primary"])))
    fig.add_trace(go.Bar(name="Lost", x=season_perf.psl_edition, y=season_perf.lost,
                         marker=dict(color="#333")))
    fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", title="SEASON RESULTS", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Win % trend
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=season_perf.psl_edition, y=season_perf.win_pct,
        mode="lines+markers+text",
        line=dict(color=tc["primary"], width=3, shape="spline"),
        marker=dict(size=10, color=tc["primary"], line=dict(width=2, color="#030f0a")),
        text=[f"{v}%" for v in season_perf.win_pct],
        textposition="top center", textfont=dict(color="#7aaa8f", size=10, family="Share Tech Mono"),
    ))
    fig2.update_layout(**PLOTLY_LAYOUT, title="WIN % TREND", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(season_perf[["psl_edition", "played", "won", "lost", "win_pct"]],
                 use_container_width=True, hide_index=True)

# ════════════════════════════════════════
# TAB 2: BATTING
# ════════════════════════════════════════
with tab2:
    # Team batting overview
    innings = team_bat.groupby(["match_id", "innings"]).agg(
        runs=("total_runs", "sum"), wickets=("is_wicket", "sum"),
        fours=("is_four", "sum"), sixes=("is_six", "sum"),
        legal_balls=("is_legal", "sum"),
    ).reset_index()
    avg_score = innings.runs.mean()
    highest = innings.runs.max()
    lowest = innings.runs.min()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avg Score", f"{avg_score:.0f}")
    c2.metric("Highest", int(highest))
    c3.metric("Lowest", int(lowest))
    c4.metric("Total Sixes", int(innings.sixes.sum()))

    # Top batters for this team
    st.markdown("##### 🏏 Top Batters")
    bat_stats = legal_bat.groupby("batter").agg(
        inn=("match_id", "nunique"), runs=("batter_runs", "sum"),
        balls=("batter_runs", "count"), fours=("is_four", "sum"),
        sixes=("is_six", "sum"), dots=("is_dot", "sum"),
    ).reset_index()
    bat_stats["sr"] = (bat_stats.runs / bat_stats.balls * 100).round(1)
    bat_stats["avg"] = (bat_stats.runs / bat_stats.inn).round(1)
    bat_stats = bat_stats.sort_values("runs", ascending=False)

    top15 = bat_stats.head(15)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top15.runs, y=top15.batter, orientation="h",
        marker=dict(color=tc["primary"]),
        text=[f"{int(r)} ({s})" for r, s in zip(top15.runs, top15.sr)],
        textposition="outside", textfont=dict(color="#7aaa8f", size=10, family="Share Tech Mono"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=500, yaxis=dict(autorange="reversed"),
                      title="TOP RUN SCORERS")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(bat_stats.head(20)[["batter", "inn", "runs", "avg", "sr", "fours", "sixes"]],
                 use_container_width=True, hide_index=True)

# ════════════════════════════════════════
# TAB 3: BOWLING
# ════════════════════════════════════════
with tab3:
    # Team bowling overview
    bowl_innings = team_bowl.groupby(["match_id", "innings"]).agg(
        conceded=("total_runs", "sum"), wickets=("is_wicket", "sum"),
        dots=("is_dot", "sum"), legal_balls=("is_legal", "sum"),
    ).reset_index()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avg Conceded", f"{bowl_innings.conceded.mean():.0f}")
    c2.metric("Total Wickets", int(bowl_innings.wickets.sum()))
    c3.metric("Best (lowest)", int(bowl_innings.conceded.min()))
    c4.metric("Avg Dots/Inn", f"{bowl_innings.dots.mean():.0f}")

    # Top bowlers
    st.markdown("##### 🎯 Top Bowlers")
    bowl_stats = team_bowl.groupby("bowler").agg(
        inn=("match_id", "nunique"), legal_balls=("is_legal", "sum"),
        runs_conceded=("total_runs", "sum"), wickets=("is_wicket", "sum"),
        dots=("is_dot", "sum"),
    ).reset_index()
    bowl_stats["overs"] = (bowl_stats.legal_balls / 6).round(1)
    bowl_stats["economy"] = np.where(bowl_stats.overs > 0, (bowl_stats.runs_conceded / bowl_stats.overs).round(2), 0)
    bowl_stats["dot_pct"] = (bowl_stats.dots / bowl_stats.legal_balls * 100).round(1)
    bowl_stats = bowl_stats.sort_values("wickets", ascending=False)

    top15b = bowl_stats.head(15)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top15b.wickets, y=top15b.bowler, orientation="h",
        marker=dict(color=top15b.economy, colorscale=[[0, tc["primary"]], [1, "#f87171"]],
                    colorbar=dict(title="Econ")),
        text=[f"{int(w)}w (Econ {e})" for w, e in zip(top15b.wickets, top15b.economy)],
        textposition="outside", textfont=dict(color="#7aaa8f", size=10, family="Share Tech Mono"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=500, yaxis=dict(autorange="reversed"),
                      title="TOP WICKET TAKERS")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(bowl_stats.head(20)[["bowler", "inn", "wickets", "economy", "dot_pct", "overs"]],
                 use_container_width=True, hide_index=True)

# ════════════════════════════════════════
# TAB 4: PHASE WISE
# ════════════════════════════════════════
with tab4:
    # Batting by phase
    st.markdown("##### 🏏 Batting by Phase")
    phase_bat = team_bat.groupby("phase").agg(
        runs=("total_runs", "sum"), legal_balls=("is_legal", "sum"),
        wickets=("is_wicket", "sum"), fours=("is_four", "sum"), sixes=("is_six", "sum"),
        dots=("is_dot", "sum"), innings=("match_id", "nunique"),
    ).reset_index()
    phase_bat["rpo"] = (phase_bat.runs / (phase_bat.legal_balls / 6)).round(2)
    phase_bat["avg_runs"] = (phase_bat.runs / phase_bat.innings).round(1)
    phase_bat["sr"] = (phase_bat.runs / phase_bat.legal_balls * 100).round(1)
    phase_bat["dot_pct"] = (phase_bat.dots / phase_bat.legal_balls * 100).round(1)
    order = {"powerplay": 0, "middle": 1, "death": 2}
    phase_bat["order"] = phase_bat.phase.map(order)
    phase_bat = phase_bat.sort_values("order")

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=phase_bat.phase.str.upper(), y=phase_bat.avg_runs,
            marker=dict(color=["#38bdf8", tc["primary"], "#f87171"]),
            text=[f"{v}" for v in phase_bat.avg_runs],
            textposition="outside", textfont=dict(color=tc["primary"], size=14, family="Share Tech Mono"),
        ))
        layout3 = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")}
        fig.update_layout(**layout3, title="AVG RUNS PER PHASE", height=350)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=phase_bat.phase.str.upper(), y=phase_bat.sr,
            marker=dict(color=["#38bdf8", tc["primary"], "#f87171"]),
            text=[f"{v}" for v in phase_bat.sr],
            textposition="outside", textfont=dict(color=tc["primary"], size=14, family="Share Tech Mono"),
        ))
        fig2.update_layout(**layout3, title="STRIKE RATE BY PHASE", height=350)
        st.plotly_chart(fig2, use_container_width=True)

    # Bowling by phase
    st.markdown("##### 🎯 Bowling by Phase")
    phase_bowl = team_bowl.groupby("phase").agg(
        conceded=("total_runs", "sum"), legal_balls=("is_legal", "sum"),
        wickets=("is_wicket", "sum"), dots=("is_dot", "sum"),
        innings=("match_id", "nunique"),
    ).reset_index()
    phase_bowl["economy"] = (phase_bowl.conceded / (phase_bowl.legal_balls / 6)).round(2)
    phase_bowl["avg_wkts"] = (phase_bowl.wickets / phase_bowl.innings).round(2)
    phase_bowl["dot_pct"] = (phase_bowl.dots / phase_bowl.legal_balls * 100).round(1)
    phase_bowl["order"] = phase_bowl.phase.map(order)
    phase_bowl = phase_bowl.sort_values("order")

    st.dataframe(phase_bowl[["phase", "economy", "avg_wkts", "dot_pct"]],
                 use_container_width=True, hide_index=True)

# ════════════════════════════════════════
# TAB 5: VENUE RECORDS
# ════════════════════════════════════════
with tab5:
    venue_perf = team_matches.groupby("venue").agg(
        played=("match_id", "count"), won=("won", "sum"),
    ).reset_index()
    venue_perf["lost"] = venue_perf.played - venue_perf.won
    venue_perf["win_pct"] = (venue_perf.won / venue_perf.played * 100).round(1)
    venue_perf = venue_perf.sort_values("win_pct", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=venue_perf.win_pct, y=venue_perf.venue, orientation="h",
        marker=dict(color=[tc["primary"] if v > 50 else "#f87171" for v in venue_perf.win_pct]),
        text=[f"{int(w)}W-{int(l)}L ({p}%)" for w, l, p in zip(venue_perf.won, venue_perf.lost, venue_perf.win_pct)],
        textposition="outside", textfont=dict(color="#7aaa8f", size=10, family="Share Tech Mono"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=400, yaxis=dict(autorange="reversed"),
                      title=f"{team.upper()} — VENUE RECORD")
    st.plotly_chart(fig, use_container_width=True)

    # Avg score at each venue
    venue_bat = team_bat.groupby(["match_id", "venue"]).agg(
        runs=("total_runs", "sum")
    ).reset_index()
    venue_avg = venue_bat.groupby("venue")["runs"].mean().round(0).reset_index()
    venue_avg.columns = ["venue", "avg_score"]
    venue_perf = venue_perf.merge(venue_avg, on="venue", how="left")

    st.dataframe(venue_perf[["venue", "played", "won", "lost", "win_pct", "avg_score"]],
                 use_container_width=True, hide_index=True)

# ════════════════════════════════════════
# TAB 6: VS OPPONENTS
# ════════════════════════════════════════
with tab6:
    opponents = sorted([t for t in teams if t != team])
    opp_records = []
    for opp in opponents:
        mask = ((team_matches.team1 == opp) | (team_matches.team2 == opp))
        opp_matches = team_matches[mask]
        if len(opp_matches) == 0:
            continue
        opp_wins = opp_matches.won.sum()
        opp_records.append({
            "opponent": opp,
            "played": len(opp_matches),
            "won": opp_wins,
            "lost": len(opp_matches) - opp_wins,
            "win_pct": round(opp_wins / len(opp_matches) * 100, 1),
        })
    opp_df = pd.DataFrame(opp_records).sort_values("win_pct", ascending=False)

    opp_colors = [TEAM_COLORS.get(o, {"primary": "#666"})["primary"] for o in opp_df.opponent]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=opp_df.win_pct, y=opp_df.opponent, orientation="h",
        marker=dict(color=opp_colors),
        text=[f"{int(w)}W-{int(l)}L ({p}%)" for w, l, p in zip(opp_df.won, opp_df.lost, opp_df.win_pct)],
        textposition="outside", textfont=dict(color="#7aaa8f", size=11, family="Share Tech Mono"),
    ))
    fig.add_vline(x=50, line_dash="dot", line_color="rgba(201,243,77,0.2)")
    fig.update_layout(**PLOTLY_LAYOUT, height=400, yaxis=dict(autorange="reversed"),
                      title=f"{team.upper()} — HEAD TO HEAD RECORD")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(opp_df, use_container_width=True, hide_index=True)
