"""Player Profile — complete deep-dive."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, fix_metrics
from src.analytics.stats_engine import StatsEngine

inject_custom_css()
fix_metrics()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()
legal = deliveries[deliveries.is_legal == 1]
all_players = sorted(set(legal.batter.unique()) | set(deliveries.bowler.unique()))

player = st.sidebar.selectbox("👤 Select Player", all_players, key="pp_sel")

is_batter = player in legal.batter.values
is_bowler = player in deliveries.bowler.values
teams = legal[legal.batter == player].batting_team.unique() if is_batter else deliveries[deliveries.bowler == player].bowling_team.unique()
team = teams[-1] if len(teams) > 0 else "Unknown"
tc = TEAM_COLORS.get(team, {"primary": "#c9f34d"})

role = "All-rounder" if is_batter and is_bowler else ("Batter" if is_batter else "Bowler")
hero_card(f"👤 {player}", f"{role} • {team}")
seam_divider()

def safe_int(val):
    return int(val) if pd.notna(val) else 0

def safe_float(val, decimals=1):
    return round(float(val), decimals) if pd.notna(val) else 0

tabs = []
if is_batter: tabs.append("🏏 Batting")
if is_bowler: tabs.append("🎯 Bowling")
tabs += ["💀 Dismissals", "📈 Form"]
tab_objects = st.tabs(tabs)
tab_idx = 0

if is_batter:
    with tab_objects[tab_idx]:
        bat = StatsEngine.full_batting_stats(deliveries, min_innings=1)
        p = bat[bat.batter == player]
        if len(p) > 0:
            p = p.iloc[0]
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Innings", safe_int(p.innings))
            c2.metric("Runs", safe_int(p.runs))
            c3.metric("Batting Avg", safe_float(p.batting_avg, 2))
            c4.metric("Strike Rate", safe_float(p.sr, 2))

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Highest Score", safe_int(p.highest_score))
            c2.metric("Not Outs", safe_int(p.not_outs))
            c3.metric("Balls Faced", safe_int(p.balls))
            c4.metric("Boundary %", f"{safe_float(p.boundary_pct)}%")

            c1,c2,c3,c4,c5,c6 = st.columns(6)
            c1.metric("50s", safe_int(p.fifties))
            c2.metric("100s", safe_int(p.hundreds))
            c3.metric("Ducks", safe_int(p.ducks))
            c4.metric("4s", safe_int(p.fours))
            c5.metric("6s", safe_int(p.sixes))
            c6.metric("Dot %", f"{safe_float(p.dot_pct)}%")

            st.markdown("##### Phase Performance")
            phase_df = pd.DataFrame({
                "Phase": ["Powerplay", "Middle", "Death"],
                "Runs": [safe_int(p.get("runs_powerplay",0)), safe_int(p.get("runs_middle",0)), safe_int(p.get("runs_death",0))],
                "SR": [safe_float(p.get("sr_powerplay",0)), safe_float(p.get("sr_middle",0)), safe_float(p.get("sr_death",0))],
            })
            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=phase_df.Phase, y=phase_df.Runs,
                    marker=dict(color=[tc["primary"]]*3),
                    text=phase_df.Runs, textposition="outside",
                    textfont=dict(color=tc["primary"], family="Share Tech Mono")))
                fig.update_layout(**PLOTLY_LAYOUT, title="RUNS BY PHASE", height=350)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=phase_df.Phase, y=phase_df.SR,
                    marker=dict(color=["#38bdf8","#c9f34d","#f87171"]),
                    text=[f"{v:.0f}" for v in phase_df.SR], textposition="outside",
                    textfont=dict(color="#c9f34d", family="Share Tech Mono")))
                fig2.update_layout(**PLOTLY_LAYOUT, title="STRIKE RATE BY PHASE", height=350)
                st.plotly_chart(fig2, use_container_width=True)

            # Recent innings with dismissal + opposition
            st.markdown("##### Recent Innings")
            p_del = deliveries[deliveries.batter == player].copy()
            p_legal = p_del[p_del.is_legal == 1]

            inn_scores = p_legal.groupby(["match_id","date","batting_team","bowling_team","psl_edition"]).agg(
                runs=("batter_runs","sum"), balls=("batter_runs","count"),
                fours=("is_four","sum"), sixes=("is_six","sum"),
            ).reset_index()
            inn_scores["sr"] = (inn_scores.runs / inn_scores.balls * 100).round(1)

            # Get dismissal info
            wickets = p_del[p_del.is_wicket == 1][["match_id","player_out","wicket_kind","bowler","fielder"]].copy()
            wickets = wickets[wickets.player_out == player]
            wickets["dismissal"] = wickets.apply(
                lambda r: f"{r.wicket_kind}" + (f" (b: {r.bowler})" if pd.notna(r.bowler) else ""), axis=1
            )
            wickets = wickets[["match_id","dismissal"]].drop_duplicates(subset="match_id")
            inn_scores = inn_scores.merge(wickets, on="match_id", how="left")
            inn_scores["dismissal"] = inn_scores.dismissal.fillna("not out")
            inn_scores = inn_scores.sort_values("date", ascending=False)

            st.dataframe(
                inn_scores.head(25)[["date","psl_edition","bowling_team","runs","balls","sr","fours","sixes","dismissal"]].rename(
                    columns={"bowling_team":"vs", "psl_edition":"season"}),
                use_container_width=True, hide_index=True,
            )
    tab_idx += 1

if is_bowler:
    with tab_objects[tab_idx]:
        bowl = StatsEngine.full_bowling_stats(deliveries, min_innings=1)
        b = bowl[bowl.bowler == player]
        if len(b) > 0:
            b = b.iloc[0]
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Innings", safe_int(b.innings))
            c2.metric("Wickets", safe_int(b.wickets))
            c3.metric("Economy", safe_float(b.economy, 2))
            c4.metric("Bowling Avg", safe_float(b.bowling_avg, 2))

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Bowling SR", safe_float(b.bowling_sr, 1))
            c2.metric("Best Figures", b.best_figures)
            c3.metric("Overs", safe_float(b.overs, 1))
            c4.metric("Dot %", f"{safe_float(b.dot_pct)}%")

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("3W Hauls", safe_int(b.three_wickets))
            c2.metric("4W Hauls", safe_int(b.four_wickets))
            c3.metric("5W Hauls", safe_int(b.five_wickets))
            c4.metric("Runs Conceded", safe_int(b.runs_conceded))

            st.markdown("##### Phase Economy")
            phase_df = pd.DataFrame({
                "Phase": ["Powerplay", "Middle", "Death"],
                "Economy": [safe_float(b.get("economy_powerplay",0)), safe_float(b.get("economy_middle",0)), safe_float(b.get("economy_death",0))],
                "Wickets": [safe_int(b.get("wickets_powerplay",0)), safe_int(b.get("wickets_middle",0)), safe_int(b.get("wickets_death",0))],
            })
            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=phase_df.Phase, y=phase_df.Economy,
                    marker=dict(color=["#38bdf8","#c9f34d","#f87171"]),
                    text=[f"{v:.1f}" for v in phase_df.Economy], textposition="outside"))
                fig.update_layout(**PLOTLY_LAYOUT, title="ECONOMY BY PHASE", height=350)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=phase_df.Phase, y=phase_df.Wickets,
                    marker=dict(color=[tc["primary"]]*3),
                    text=phase_df.Wickets, textposition="outside"))
                fig2.update_layout(**PLOTLY_LAYOUT, title="WICKETS BY PHASE", height=350)
                st.plotly_chart(fig2, use_container_width=True)
    tab_idx += 1

with tab_objects[tab_idx]:
    dis = StatsEngine.dismissal_analysis(deliveries, player=player)
    if len(dis) > 0:
        fig = go.Figure(data=[go.Pie(labels=dis.wicket_kind, values=dis["count"], hole=0.5,
              marker=dict(colors=["#c9f34d","#38bdf8","#f87171","#fb923c","#c084fc","#34d399"]),
              textfont=dict(color="#fff", family="Oswald"))])
        fig.update_layout(**PLOTLY_LAYOUT, title=f"HOW {player.upper()} GETS OUT", height=400, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No dismissal data.")
tab_idx += 1

with tab_objects[tab_idx]:
    if is_batter:
        p_data = legal[legal.batter==player]
        form = p_data.groupby(["match_id","date"]).agg(runs=("batter_runs","sum")).reset_index().sort_values("date")
        form["rolling_5"] = form.runs.rolling(5, min_periods=1).mean().round(1)
        form["match_num"] = range(1, len(form)+1)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=form.match_num, y=form.runs, name="Score",
                             marker=dict(color=tc["primary"], opacity=0.4)))
        fig.add_trace(go.Scatter(x=form.match_num, y=form.rolling_5, name="5-Match Avg",
                                  line=dict(color="#f0b429", width=3, shape="spline")))
        fig.update_layout(**PLOTLY_LAYOUT, title="FORM TRACKER", height=400, xaxis_title="Match #")
        st.plotly_chart(fig, use_container_width=True)