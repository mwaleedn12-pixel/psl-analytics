"""Match Explorer — scorecard, worm, manhattan, fall of wickets."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, fix_metrics

inject_custom_css()
fix_metrics()
hero_card("📋 Match Explorer", "Full scorecard, worm chart, manhattan, fall of wickets")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()

decided = matches.sort_values("date", ascending=False).copy()
decided["label"] = decided.apply(lambda r: f"{r.psl_edition} | {r.team1} vs {r.team2} | {str(r.date)[:10]}", axis=1)
selected = st.selectbox("Select Match", decided.label.values)
match_row = decided[decided.label == selected].iloc[0]
mid = match_row.match_id
md = deliveries[deliveries.match_id == mid]

t1, t2 = match_row.team1, match_row.team2
tc1 = TEAM_COLORS.get(t1, {"primary":"#c9f34d"})["primary"]
tc2 = TEAM_COLORS.get(t2, {"primary":"#38bdf8"})["primary"]
winner = match_row.winner if pd.notna(match_row.winner) else "No Result"
margin = ""
if pd.notna(match_row.win_by_runs): margin = f"by {int(match_row.win_by_runs)} runs"
elif pd.notna(match_row.win_by_wickets): margin = f"by {int(match_row.win_by_wickets)} wickets"

st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; padding:16px 24px;
     background:rgba(13,43,31,0.5); border-radius:14px; margin-bottom:16px;">
    <div style="text-align:center; flex:1;">
        <div style="font-family:Oswald; font-size:1.2rem; color:{tc1}; text-transform:uppercase;">{t1}</div>
    </div>
    <div style="text-align:center; flex:1;">
        <div style="font-family:Oswald; font-size:0.7rem; color:#5a8a6f;">WINNER</div>
        <div style="font-family:Oswald; font-size:1rem; color:#c9f34d;">{winner}</div>
        <div style="font-family:'Share Tech Mono'; font-size:0.8rem; color:#5a8a6f;">{margin}</div>
    </div>
    <div style="text-align:center; flex:1;">
        <div style="font-family:Oswald; font-size:1.2rem; color:{tc2}; text-transform:uppercase;">{t2}</div>
    </div>
</div>""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Venue", match_row.venue.split(",")[0])
c2.metric("Toss", f"{match_row.toss_winner} ({match_row.toss_decision})")
pom = match_row.player_of_match if pd.notna(match_row.player_of_match) else "—"
c3.metric("Player of Match", pom)

tab1, tab2, tab3, tab4 = st.tabs(["📋 Scorecard", "🐛 Worm Chart", "📊 Manhattan", "💀 Fall of Wickets"])

with tab1:
    for inn in [1, 2]:
        inn_data = md[md.innings == inn]
        if len(inn_data) == 0: continue
        batting_team = inn_data.batting_team.iloc[0]
        btc = TEAM_COLORS.get(batting_team, {"primary":"#c9f34d"})["primary"]
        total = inn_data.total_runs.sum()
        wkts = inn_data.is_wicket.sum()
        legal_count = inn_data[inn_data.is_legal==1].shape[0]
        overs = legal_count / 6

        st.markdown(f"##### <span style='color:{btc}'>{batting_team}</span> — {total}/{wkts} ({overs:.1f} ov)", unsafe_allow_html=True)

        # Batting card — in batting order (first appearance)
        legal = inn_data[inn_data.is_legal == 1]
        first_ball = legal.groupby("batter")["over"].min().reset_index()
        first_ball.columns = ["batter", "first_over"]

        bat_card = legal.groupby("batter").agg(
            runs=("batter_runs","sum"), balls=("batter_runs","count"),
            fours=("is_four","sum"), sixes=("is_six","sum"),
        ).reset_index()
        bat_card["sr"] = (bat_card.runs / bat_card.balls * 100).round(1)
        bat_card = bat_card.merge(first_ball, on="batter")

        # Dismissal info
        dismissed = inn_data[inn_data.is_wicket==1][["player_out","wicket_kind","bowler","fielder"]].copy()
        dismissed = dismissed.rename(columns={"player_out":"batter"})
        dismissed["dismissal"] = dismissed.apply(
            lambda r: f"{r.wicket_kind}" + (f" b {r.bowler}" if r.wicket_kind in ["bowled","caught","lbw","stumped","caught and bowled"] and pd.notna(r.bowler) else "")
            + (f" c {r.fielder}" if r.wicket_kind == "caught" and pd.notna(r.fielder) else ""), axis=1
        )
        bat_card = bat_card.merge(dismissed[["batter","dismissal"]], on="batter", how="left")
        bat_card["dismissal"] = bat_card.dismissal.fillna("not out")

        # Sort by batting order
        bat_card = bat_card.sort_values("first_over")
        st.dataframe(bat_card[["batter","runs","balls","fours","sixes","sr","dismissal"]],
                     use_container_width=True, hide_index=True)

        # Bowling card — in bowling order (first over bowled)
        bowl_first = inn_data.groupby("bowler")["over"].min().reset_index()
        bowl_first.columns = ["bowler", "first_over"]

        bowl_card = inn_data.groupby("bowler").agg(
            legal_b=("is_legal","sum"), runs_c=("total_runs","sum"),
            wkts=("is_wicket","sum"), dots=("is_dot","sum"),
            fours_c=("is_four","sum"), sixes_c=("is_six","sum"),
        ).reset_index()
        bowl_card["overs"] = (bowl_card.legal_b/6).round(1)
        bowl_card["econ"] = np.where(bowl_card.overs>0,(bowl_card.runs_c/bowl_card.overs).round(2),0)
        bowl_card = bowl_card.merge(bowl_first, on="bowler")
        bowl_card = bowl_card.sort_values("first_over")

        st.dataframe(bowl_card[["bowler","overs","runs_c","wkts","dots","econ"]].rename(
            columns={"runs_c":"runs","wkts":"wickets"}),
            use_container_width=True, hide_index=True)
        st.markdown("---")

with tab2:
    fig = go.Figure()
    for inn in [1,2]:
        inn_data = md[md.innings==inn]
        if len(inn_data)==0: continue
        bt = inn_data.batting_team.iloc[0]
        btc = TEAM_COLORS.get(bt,{"primary":"#c9f34d"})["primary"]
        cum = inn_data.groupby("over")["total_runs"].sum().cumsum().reset_index()
        cum.columns = ["over","cum_runs"]
        fig.add_trace(go.Scatter(x=cum.over, y=cum.cum_runs, mode="lines",
                                  name=bt, line=dict(color=btc, width=3, shape="spline"),
                                  fill="tozeroy", fillcolor=f"{btc}11"))
    fig.update_layout(**PLOTLY_LAYOUT, title="WORM CHART", height=420,
                      xaxis_title="Over", yaxis_title="Cumulative Runs")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig2 = go.Figure()
    for inn in [1,2]:
        inn_data = md[md.innings==inn]
        if len(inn_data)==0: continue
        bt = inn_data.batting_team.iloc[0]
        btc = TEAM_COLORS.get(bt,{"primary":"#c9f34d"})["primary"]
        per_over = inn_data.groupby("over")["total_runs"].sum().reset_index()
        fig2.add_trace(go.Bar(x=per_over.over, y=per_over.total_runs, name=bt,
                               marker=dict(color=btc, opacity=0.8)))
    fig2.update_layout(**PLOTLY_LAYOUT, barmode="group", title="MANHATTAN CHART", height=420,
                        xaxis_title="Over", yaxis_title="Runs")
    st.plotly_chart(fig2, use_container_width=True)

with tab4:
    for inn in [1,2]:
        inn_data = md[(md.innings==inn)&(md.is_wicket==1)]
        if len(inn_data)==0: continue
        bt = md[md.innings==inn].batting_team.iloc[0]
        btc = TEAM_COLORS.get(bt,{"primary":"#c9f34d"})["primary"]
        st.markdown(f"**{bt}** — Fall of Wickets")
        inn_all = md[md.innings==inn].copy()
        inn_all["cum"] = inn_all["total_runs"].cumsum()
        fow = inn_all[inn_all.is_wicket==1][["over","ball","player_out","cum","bowler","wicket_kind"]].copy()
        fow["wicket_num"] = range(1, len(fow)+1)
        for _, r in fow.iterrows():
            over_ball = f"{r['over']-1}.{r['ball']}"
            st.markdown(f"""<span style='font-family:Share Tech Mono; color:{btc};'>
                {int(r.wicket_num)}-{int(r.cum)}</span>
                <span style='color:#7aaa8f;'>({r.player_out}, {r.wicket_kind} b {r.bowler}, {over_ball})</span>""",
                unsafe_allow_html=True)
        st.markdown("---")