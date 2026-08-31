"""PSL Player Rankings — weighted composite ranking like ICC."""
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
hero_card("🏅 PSL Player Rankings", "Weighted composite rankings — batting, bowling, all-rounder indexes")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
deliveries = load_data()

tab1, tab2, tab3 = st.tabs(["🏏 Batting Rankings", "🎯 Bowling Rankings", "⭐ All-Rounder Rankings"])

with tab1:
    bat = StatsEngine.full_batting_stats(deliveries, min_innings=15)
    # Batting Index = (Avg * 0.3) + (SR * 0.25) + (Boundary% * 0.15) + (100-Dot% * 0.1) + (Consistency * 0.2)
    max_avg = bat.batting_avg.quantile(0.95)
    max_sr = bat.sr.quantile(0.95)
    max_bp = bat.boundary_pct.quantile(0.95)

    bat["avg_norm"] = np.clip(bat.batting_avg / max_avg * 100, 0, 100)
    bat["sr_norm"] = np.clip(bat.sr / max_sr * 100, 0, 100)
    bat["bp_norm"] = np.clip(bat.boundary_pct / max_bp * 100, 0, 100)
    bat["dot_inv"] = np.clip((100 - bat.dot_pct), 0, 100)

    bat["batting_index"] = (
        bat.avg_norm * 0.30 + bat.sr_norm * 0.25 +
        bat.bp_norm * 0.15 + bat.dot_inv * 0.10 +
        np.clip(bat.innings / bat.innings.max() * 100, 0, 100) * 0.20
    ).round(1)
    bat = bat.sort_values("batting_index", ascending=False).reset_index(drop=True)
    bat["rank"] = range(1, len(bat) + 1)

    top20 = bat.head(20)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top20.batting_index, y=top20.batter, orientation="h",
        marker=dict(color=top20.batting_index, colorscale=[[0,"#1a1a2e"],[0.5,"#c9f34d"],[1,"#f0b429"]]),
        text=[f"#{r} — {v}" for r, v in zip(top20["rank"], top20.batting_index)],
        textposition="outside", textfont=dict(color="#c9f34d", family="Share Tech Mono", size=11),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, title="BATTING RANKING INDEX", height=600, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='color:#5a8a6f; font-size:0.75rem;'>Index = Avg(30%) + SR(25%) + Experience(20%) + Boundary%(15%) + Non-Dot%(10%)</div>", unsafe_allow_html=True)
    st.dataframe(bat.head(30)[["rank","batter","innings","runs","batting_avg","sr","highest_score","fifties","hundreds","batting_index"]],
                 use_container_width=True, hide_index=True)

with tab2:
    bowl = StatsEngine.full_bowling_stats(deliveries, min_innings=15)
    max_wkts = bowl.wickets.quantile(0.95)
    min_econ = bowl.economy.quantile(0.05)

    bowl["wkt_norm"] = np.clip(bowl.wickets / max_wkts * 100, 0, 100)
    bowl["econ_norm"] = np.clip((1 - bowl.economy / 12) * 100, 0, 100)
    bowl["dot_norm"] = np.clip(bowl.dot_pct / 50 * 100, 0, 100)
    bowl["sr_norm"] = np.clip((1 - bowl.bowling_sr / 30) * 100, 0, 100) if bowl.bowling_sr.max() > 0 else 0

    bowl["bowling_index"] = (
        bowl.wkt_norm * 0.30 + bowl.econ_norm * 0.25 +
        bowl.dot_norm * 0.15 + bowl.sr_norm * 0.10 +
        np.clip(bowl.innings / bowl.innings.max() * 100, 0, 100) * 0.20
    ).round(1)
    bowl = bowl.sort_values("bowling_index", ascending=False).reset_index(drop=True)
    bowl["rank"] = range(1, len(bowl) + 1)

    top20b = bowl.head(20)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=top20b.bowling_index, y=top20b.bowler, orientation="h",
        marker=dict(color=top20b.bowling_index, colorscale=[[0,"#1a1a2e"],[0.5,"#38bdf8"],[1,"#c084fc"]]),
        text=[f"#{r} — {v}" for r, v in zip(top20b["rank"], top20b.bowling_index)],
        textposition="outside", textfont=dict(color="#38bdf8", family="Share Tech Mono", size=11),
    ))
    fig2.update_layout(**PLOTLY_LAYOUT, title="BOWLING RANKING INDEX", height=600, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(bowl.head(30)[["rank","bowler","innings","wickets","economy","bowling_avg","best_figures","bowling_index"]],
                 use_container_width=True, hide_index=True)

with tab3:
    # Merge batting + bowling
    ar = bat[["batter","innings","runs","batting_avg","sr","batting_index"]].rename(columns={"batter":"player","innings":"bat_inn"})
    ar_bowl = bowl[["bowler","innings","wickets","economy","bowling_index"]].rename(columns={"bowler":"player","innings":"bowl_inn"})
    ar_merged = ar.merge(ar_bowl, on="player")
    ar_merged = ar_merged[(ar_merged.bat_inn >= 10) & (ar_merged.bowl_inn >= 10)]

    ar_merged["allrounder_index"] = ((ar_merged.batting_index + ar_merged.bowling_index) / 2).round(1)
    ar_merged = ar_merged.sort_values("allrounder_index", ascending=False).reset_index(drop=True)
    ar_merged["rank"] = range(1, len(ar_merged) + 1)

    if len(ar_merged) > 0:
        top15 = ar_merged.head(15)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Batting Index", x=top15.player, y=top15.batting_index,
                              marker=dict(color="#c9f34d")))
        fig3.add_trace(go.Bar(name="Bowling Index", x=top15.player, y=top15.bowling_index,
                              marker=dict(color="#38bdf8")))
        fig3.update_layout(**PLOTLY_LAYOUT, barmode="group", title="ALL-ROUNDER INDEX", height=450,
                           xaxis=dict(tickangle=-35))
        st.plotly_chart(fig3, use_container_width=True)

        st.dataframe(ar_merged.head(20)[["rank","player","runs","batting_index","wickets","bowling_index","allrounder_index"]],
                     use_container_width=True, hide_index=True)
