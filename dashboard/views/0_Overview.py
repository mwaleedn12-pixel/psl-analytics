"""Overview — Home Page"""
import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.style import (
    inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT,
    TEAM_COLORS, get_team_bar_colors, team_color_card,
)
#inject_custom_css()  # temporarily disabled

import pandas as pd
import plotly.graph_objects as go

@st.cache_data
def load_data():
    P = PROJECT_ROOT / "data" / "processed"
    m = pd.read_csv(P / "psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(P / "psl_deliveries_clean.csv", parse_dates=["date"], low_memory=False)
    return m, d

matches, deliveries = load_data()

# ── Sidebar ──
st.sidebar.markdown("""
<div style="text-align:center; padding: 16px 0;">
    <div style="font-size: 2.5rem;">🏏</div>
    <div style="font-family: 'Oswald', sans-serif; font-size: 1.3rem; font-weight: 700;
         background: linear-gradient(135deg, #c9f34d, #f0b429);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent;
         letter-spacing: 2px; margin-top: 8px; text-transform: uppercase;">PSL Analytics</div>
    <div style="font-family: 'Oswald'; font-size: 0.65rem; color: #3a5a4a;
         text-transform: uppercase; letter-spacing: 3px; margin-top: 2px;">Match Intelligence</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.caption("🏟️ 357 Matches • 83,799 Balls • 11 Seasons")

# ── Hero ──
hero_card("🏏 PSL Analytics & Match Intelligence",
          "Comprehensive cricket intelligence across 11 PSL seasons — powered by data science & machine learning")
seam_divider()

# ── KPI Row ──
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Matches", f"{len(matches)}")
col2.metric("Seasons", f"{matches.psl_edition.nunique()}")
col3.metric("Total Runs", f"{deliveries.total_runs.sum():,}")
col4.metric("Wickets", f"{deliveries.is_wicket.sum():,}")
col5.metric("Sixes", f"{deliveries.is_six.sum():,}")

st.markdown("")

# ── Charts ──
col1, col2 = st.columns(2)

with col1:
    innings_totals = deliveries.groupby(["match_id", "innings", "psl_edition", "season_year"])["total_runs"].sum().reset_index()
    season_avg = innings_totals.groupby(["psl_edition", "season_year"])["total_runs"].mean().reset_index()
    season_avg.columns = ["psl_edition", "season_year", "avg_score"]
    season_avg = season_avg.sort_values("season_year")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=season_avg["psl_edition"], y=season_avg["avg_score"],
        mode="lines+markers",
        line=dict(color="#c9f34d", width=3, shape="spline"),
        marker=dict(size=9, color="#c9f34d", line=dict(width=2, color="#030f0a"), symbol="diamond"),
        fill="tozeroy", fillcolor="rgba(201, 243, 77, 0.06)",
        hovertemplate="<b>%{x}</b><br>Avg Score: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, title="📈 AVERAGE INNINGS SCORE TREND", height=420)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    team_list = []
    for _, row in matches.iterrows():
        for team in [row.team1, row.team2]:
            team_list.append({"team": team, "won": 1 if team == row.winner else 0})
    team_df = pd.DataFrame(team_list)
    team_perf = team_df.groupby("team").agg(played=("won", "count"), won=("won", "sum")).reset_index()
    team_perf["win_pct"] = (team_perf["won"] / team_perf["played"] * 100).round(1)
    team_perf = team_perf.sort_values("win_pct", ascending=True)

    bar_colors = get_team_bar_colors(team_perf["team"])
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=team_perf["win_pct"], y=team_perf["team"], orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f'{v}%' for v in team_perf["win_pct"]],
        textposition="outside",
        textfont=dict(color="#7aaa8f", size=11, family="Share Tech Mono"),
        hovertemplate="<b>%{y}</b><br>Win: %{x}%<extra></extra>",
    ))
    fig2.update_layout(**PLOTLY_LAYOUT, title="🏆 ALL-TIME WIN PERCENTAGE", height=420)
    st.plotly_chart(fig2, use_container_width=True)

# ── Team Cards ──
st.markdown("##### ⚡ FRANCHISE OVERVIEW")
cols = st.columns(4)
sorted_teams = team_perf.sort_values("win_pct", ascending=False)
for i, (_, row) in enumerate(sorted_teams.iterrows()):
    with cols[i % 4]:
        team_color_card(row.team, "Win Rate", f"{row.win_pct}%")

st.markdown("---")

# ── Phase + Chasing ──
col1, col2 = st.columns(2)

with col1:
    phase_stats = deliveries.groupby("phase").agg(
        runs=("total_runs", "sum"), balls=("is_legal", "sum")
    ).reset_index()
    phase_stats["rpo"] = (phase_stats["runs"] / (phase_stats["balls"] / 6)).round(2)
    order = {"powerplay": 0, "middle": 1, "death": 2}
    phase_stats["order"] = phase_stats.phase.map(order)
    phase_stats = phase_stats.sort_values("order")

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=phase_stats["phase"].str.upper(), y=phase_stats["rpo"],
        marker=dict(color=["#38bdf8", "#c9f34d", "#f87171"], line=dict(width=0)),
        text=[f"{v}" for v in phase_stats["rpo"]],
        textposition="outside",
        textfont=dict(color="#c9f34d", size=16, family="Share Tech Mono"),
        hovertemplate="<b>%{x}</b><br>RPO: %{y}<extra></extra>",
    ))
    layout3 = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")}
    fig3.update_layout(**layout3, title="⏱️ RUNS PER OVER BY PHASE", height=380,
                        yaxis=dict(range=[0, 12], gridcolor="rgba(201,243,77,0.04)"))
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    decided = matches[matches.winner.notna()].copy()
    chase_wins = int(decided["win_by_wickets"].notna().sum())
    defend_wins = int(decided["win_by_runs"].notna().sum())

    fig4 = go.Figure(data=[go.Pie(
        labels=["CHASING WON", "DEFENDING WON"], values=[chase_wins, defend_wins],
        hole=0.6,
        marker=dict(colors=["#c9f34d", "#f0b429"], line=dict(color="#030f0a", width=3)),
        textinfo="label+percent",
        textfont=dict(size=12, color="#fff", family="Oswald"),
        hovertemplate="<b>%{label}</b><br>Matches: %{value}<br>%{percent}<extra></extra>",
        rotation=90,
    )])
    fig4.add_annotation(
        text=f"<b style='font-family:Share Tech Mono;font-size:22px'>{chase_wins+defend_wins}</b>"
             f"<br><span style='font-size:9px;color:#3a5a4a;font-family:Oswald;letter-spacing:2px'>MATCHES</span>",
        showarrow=False, font=dict(size=20, color="#fff"))
    fig4.update_layout(**PLOTLY_LAYOUT, title="🎯 CHASING VS DEFENDING", height=380, showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)