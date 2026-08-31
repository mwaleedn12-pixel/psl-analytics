"""Player Analytics — Premium Edition with match filters & advanced charts."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.style import inject_custom_css, accent_line, hero_card, PLOTLY_LAYOUT
from src.features.player_features import compute_batting_stats, compute_bowling_stats
from src.analytics.impact_engine import compute_impact_scores, compute_career_impact
from src.analytics.player_similarity import PlayerSimilarityEngine

inject_custom_css()

hero_card("🏏 Player Analytics", "Batting, bowling, Impact Score, similarity & archetypes")
accent_line()

@st.cache_data
def load_data():
    P = PROJECT_ROOT / "data" / "processed"
    m = pd.read_csv(P / "psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(P / "psl_deliveries_clean.csv", parse_dates=["date"], low_memory=False)
    return m, d

matches, deliveries = load_data()

# ── Match Window Filter (global) ──
st.markdown("##### 🔎 Filter by Recent Matches")
filter_col1, filter_col2 = st.columns([1, 3])
with filter_col1:
    match_window = st.selectbox("Show stats for", ["All Time", "Last 5", "Last 10", "Last 15", "Last 20", "Custom Range"])

with filter_col2:
    if match_window == "Custom Range":
        seasons = sorted(matches.psl_edition.unique())
        sel_seasons = st.multiselect("Select Seasons", seasons, default=seasons[-3:])
    else:
        sel_seasons = None

# Apply filter
if match_window != "All Time":
    if match_window == "Custom Range" and sel_seasons:
        filtered_matches = matches[matches.psl_edition.isin(sel_seasons)]
    else:
        n = int(match_window.split()[-1])
        recent_ids = matches.sort_values("date", ascending=False).match_id.unique()[:n]
        # Per-player: get last N matches each player appeared in
        # For simplicity, filter by most recent N matches globally
        filtered_matches = matches[matches.match_id.isin(recent_ids)]

    match_ids = filtered_matches.match_id.values
    del_filtered = deliveries[deliveries.match_id.isin(match_ids)]
    st.caption(f"📊 Showing **{len(filtered_matches)}** matches | {filtered_matches.date.min().strftime('%b %Y')} → {filtered_matches.date.max().strftime('%b %Y')}")
else:
    del_filtered = deliveries
    filtered_matches = matches

st.markdown("---")

@st.cache_data
def get_batting(_d):
    return compute_batting_stats(_d, min_innings=1)

@st.cache_data
def get_bowling(_d):
    return compute_bowling_stats(_d, min_innings=1)

batting = get_batting(del_filtered)
bowling = get_bowling(del_filtered)

tab1, tab2, tab3, tab4 = st.tabs(["⚡ Batting", "🎯 Bowling", "💎 Impact Score", "🔗 Player Similarity"])

# ═══════════════════════════════════════════════
# BATTING TAB
# ═══════════════════════════════════════════════
with tab1:
    min_inn = st.slider("Min Innings", 3, 50, 10, key="bat_inn")
    bat = batting[batting.innings >= min_inn].reset_index(drop=True)

    # Top 3 KPIs
    if len(bat) > 0:
        top = bat.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("🥇 Top Scorer", f"{top.batter}", f"{int(top.runs)} runs")
        best_sr = bat.nlargest(1, "sr").iloc[0]
        c2.metric("⚡ Highest SR", f"{best_sr.batter}", f"SR {best_sr.sr}")
        best_avg = bat.nlargest(1, "avg").iloc[0]
        c3.metric("📊 Best Average", f"{best_avg.batter}", f"Avg {best_avg.avg}")

    col1, col2 = st.columns(2)

    with col1:
        top15 = bat.head(15)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top15["runs"], y=top15["batter"],
            orientation="h",
            marker=dict(
                color=top15["sr"],
                colorscale=[[0, "#38bdf8"], [0.5, "#a3e635"], [1, "#f87171"]],
                colorbar=dict(title="SR", tickfont=dict(color="#888")),
                line=dict(width=0),
            ),
            text=[f'{int(r)}' for r in top15["runs"]],
            textposition="outside",
            textfont=dict(color="#888", size=11),
            hovertemplate="<b>%{y}</b><br>Runs: %{x}<br>SR: %{marker.color:.1f}<extra></extra>",
        ))
        fig.update_layout(**PLOTLY_LAYOUT, title="Top Run Scorers", height=520,
                          yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Scatter: Avg vs SR with bubble size = runs
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=bat["avg"], y=bat["sr"],
            mode="markers",
            marker=dict(
                size=np.clip(bat["runs"] / bat["runs"].max() * 40, 6, 40),
                color=bat["boundary_pct"],
                colorscale="Viridis",
                colorbar=dict(title="Bnd%", tickfont=dict(color="#888")),
                line=dict(width=1, color="rgba(255,255,255,0.1)"),
                opacity=0.85,
            ),
            text=bat["batter"],
            hovertemplate="<b>%{text}</b><br>Avg: %{x:.1f}<br>SR: %{y:.1f}<extra></extra>",
        ))
        # Quadrant lines
        avg_med = bat["avg"].median()
        sr_med = bat["sr"].median()
        fig2.add_hline(y=sr_med, line_dash="dot", line_color="rgba(255,255,255,0.1)")
        fig2.add_vline(x=avg_med, line_dash="dot", line_color="rgba(255,255,255,0.1)")
        fig2.add_annotation(x=avg_med*1.6, y=sr_med*1.15, text="Elite", showarrow=False,
                            font=dict(color="#a3e635", size=11))
        fig2.update_layout(**PLOTLY_LAYOUT, title="Average vs Strike Rate",
                           xaxis_title="Average", yaxis_title="Strike Rate", height=520)
        st.plotly_chart(fig2, use_container_width=True)

    # Player Profile Card
    st.markdown("---")
    st.markdown("##### 🔍 Player Profile")
    player = st.selectbox("Select Batter", bat["batter"].values, key="bat_profile")
    p = bat[bat.batter == player].iloc[0]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Innings", int(p.innings))
    c2.metric("Runs", int(p.runs))
    c3.metric("Average", f"{p.avg}")
    c4.metric("Strike Rate", f"{p.sr}")
    c5.metric("Boundary %", f"{p.boundary_pct}%")
    c6.metric("Dot %", f"{p.dot_pct}%")

    # Radar Chart
    col1, col2 = st.columns(2)
    with col1:
        # Normalize stats for radar
        max_vals = bat[["avg", "sr", "boundary_pct"]].max()
        max_vals["sr_powerplay"] = bat["sr_powerplay"].max() if "sr_powerplay" in bat.columns else 1
        max_vals["sr_middle"] = bat["sr_middle"].max() if "sr_middle" in bat.columns else 1
        max_vals["sr_death"] = bat["sr_death"].max() if "sr_death" in bat.columns else 1

        categories = ["Average", "Strike Rate", "Boundary%", "PP SR", "Middle SR", "Death SR"]
        values = [
            p.avg / max_vals["avg"] * 100 if max_vals["avg"] > 0 else 0,
            p.sr / max_vals["sr"] * 100 if max_vals["sr"] > 0 else 0,
            p.boundary_pct / max_vals["boundary_pct"] * 100 if max_vals["boundary_pct"] > 0 else 0,
            (p.sr_powerplay / max_vals["sr_powerplay"] * 100) if "sr_powerplay" in bat.columns and max_vals["sr_powerplay"] > 0 else 0,
            (p.sr_middle / max_vals["sr_middle"] * 100) if "sr_middle" in bat.columns and max_vals["sr_middle"] > 0 else 0,
            (p.sr_death / max_vals["sr_death"] * 100) if "sr_death" in bat.columns and max_vals["sr_death"] > 0 else 0,
        ]
        values.append(values[0])  # close the polygon
        categories.append(categories[0])

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values, theta=categories,
            fill="toself",
            fillcolor="rgba(163, 230, 53, 0.15)",
            line=dict(color="#a3e635", width=2),
            marker=dict(size=6, color="#a3e635"),
            name=player,
        ))
        fig_radar.update_layout(
            **PLOTLY_LAYOUT,
            title=f"{player} — Batting Profile",
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.05)",
                                tickfont=dict(size=9, color="#555")),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.05)",
                                 tickfont=dict(size=11, color="#aaa")),
            ),
            height=420,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        # Phase breakdown bar
        phase_data = {"Phase": ["Powerplay", "Middle", "Death"]}
        phase_data["SR"] = [
            getattr(p, "sr_powerplay", 0),
            getattr(p, "sr_middle", 0),
            getattr(p, "sr_death", 0),
        ]
        phase_data["Runs"] = [
            getattr(p, "runs_powerplay", 0),
            getattr(p, "runs_middle", 0),
            getattr(p, "runs_death", 0),
        ]
        pdf = pd.DataFrame(phase_data)

        fig_phase = go.Figure()
        fig_phase.add_trace(go.Bar(
            x=pdf["Phase"], y=pdf["SR"], name="Strike Rate",
            marker=dict(color=["#38bdf8", "#a3e635", "#f87171"]),
            text=[f"{v:.0f}" for v in pdf["SR"]],
            textposition="outside", textfont=dict(color="#ccc"),
        ))
        fig_phase.update_layout(**PLOTLY_LAYOUT, title=f"{player} — Phase Strike Rate",
                                height=420, yaxis_title="Strike Rate")
        st.plotly_chart(fig_phase, use_container_width=True)

# ═══════════════════════════════════════════════
# BOWLING TAB
# ═══════════════════════════════════════════════
with tab2:
    min_inn_b = st.slider("Min Innings", 3, 50, 10, key="bowl_inn")
    bowl = bowling[bowling.innings >= min_inn_b].reset_index(drop=True)

    if len(bowl) > 0:
        top_b = bowl.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("🥇 Top Wickets", f"{top_b.bowler}", f"{int(top_b.wickets)} wkts")
        best_econ = bowl[bowl.wickets >= 10].nsmallest(1, "economy")
        if not best_econ.empty:
            c2.metric("🎯 Best Economy", f"{best_econ.iloc[0].bowler}", f"Econ {best_econ.iloc[0].economy}")
        best_dot = bowl.nlargest(1, "dot_pct")
        c3.metric("⭕ Best Dot%", f"{best_dot.iloc[0].bowler}", f"{best_dot.iloc[0].dot_pct}%")

    col1, col2 = st.columns(2)
    with col1:
        top15b = bowl.head(15)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top15b["wickets"], y=top15b["bowler"],
            orientation="h",
            marker=dict(
                color=top15b["economy"],
                colorscale=[[0, "#a3e635"], [0.5, "#fbbf24"], [1, "#f87171"]],
                colorbar=dict(title="Econ", tickfont=dict(color="#888")),
            ),
            text=[f'{int(w)}' for w in top15b["wickets"]],
            textposition="outside", textfont=dict(color="#888", size=11),
            hovertemplate="<b>%{y}</b><br>Wkts: %{x}<br>Econ: %{marker.color:.2f}<extra></extra>",
        ))
        fig.update_layout(**PLOTLY_LAYOUT, title="Top Wicket Takers", height=520,
                          yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=bowl["economy"], y=bowl["dot_pct"],
            mode="markers",
            marker=dict(
                size=np.clip(bowl["wickets"] / bowl["wickets"].max() * 35, 6, 35),
                color=bowl["wickets"],
                colorscale="Purples",
                colorbar=dict(title="Wkts", tickfont=dict(color="#888")),
                line=dict(width=1, color="rgba(255,255,255,0.1)"),
            ),
            text=bowl["bowler"],
            hovertemplate="<b>%{text}</b><br>Econ: %{x:.2f}<br>Dot%: %{y:.1f}<extra></extra>",
        ))
        econ_med = bowl["economy"].median()
        dot_med = bowl["dot_pct"].median()
        fig2.add_hline(y=dot_med, line_dash="dot", line_color="rgba(255,255,255,0.1)")
        fig2.add_vline(x=econ_med, line_dash="dot", line_color="rgba(255,255,255,0.1)")
        fig2.add_annotation(x=econ_med*0.75, y=dot_med*1.2, text="Elite", showarrow=False,
                            font=dict(color="#c084fc", size=11))
        fig2.update_layout(**PLOTLY_LAYOUT, title="Economy vs Dot Ball %",
                           xaxis_title="Economy", yaxis_title="Dot %", height=520)
        st.plotly_chart(fig2, use_container_width=True)

    # Bowler Profile
    st.markdown("---")
    st.markdown("##### 🔍 Bowler Profile")
    bowler_sel = st.selectbox("Select Bowler", bowl["bowler"].values, key="bowl_profile")
    b = bowl[bowl.bowler == bowler_sel].iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Innings", int(b.innings))
    c2.metric("Wickets", int(b.wickets))
    c3.metric("Economy", f"{b.economy}")
    c4.metric("Dot %", f"{b.dot_pct}%")
    c5.metric("Bowling SR", f"{b.bowling_sr}" if pd.notna(b.bowling_sr) else "—")

    col1, col2 = st.columns(2)
    with col1:
        max_b = bowl[["economy", "dot_pct", "wickets"]].max()
        b_categories = ["Low Economy", "Dot Ball%", "Wickets", "PP Econ", "Mid Econ", "Death Econ"]
        b_values = [
            (1 - b.economy / max_b["economy"]) * 100 if max_b["economy"] > 0 else 0,
            b.dot_pct / max_b["dot_pct"] * 100 if max_b["dot_pct"] > 0 else 0,
            b.wickets / max_b["wickets"] * 100 if max_b["wickets"] > 0 else 0,
            max(0, (1 - getattr(b, "economy_powerplay", 8) / 12) * 100),
            max(0, (1 - getattr(b, "economy_middle", 8) / 12) * 100),
            max(0, (1 - getattr(b, "economy_death", 10) / 15) * 100),
        ]
        b_values.append(b_values[0])
        b_categories.append(b_categories[0])

        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(
            r=b_values, theta=b_categories, fill="toself",
            fillcolor="rgba(192, 132, 252, 0.15)",
            line=dict(color="#c084fc", width=2),
            marker=dict(size=6, color="#c084fc"),
        ))
        fig_r.update_layout(**PLOTLY_LAYOUT, title=f"{bowler_sel} — Bowling Profile",
                            polar=dict(bgcolor="rgba(0,0,0,0)",
                                       radialaxis=dict(visible=True, range=[0, 100],
                                                       gridcolor="rgba(255,255,255,0.05)",
                                                       tickfont=dict(size=9, color="#555")),
                                       angularaxis=dict(gridcolor="rgba(255,255,255,0.05)",
                                                        tickfont=dict(size=11, color="#aaa"))),
                            height=420)
        st.plotly_chart(fig_r, use_container_width=True)

    with col2:
        phase_econ = pd.DataFrame({
            "Phase": ["Powerplay", "Middle", "Death"],
            "Economy": [getattr(b, "economy_powerplay", 0),
                        getattr(b, "economy_middle", 0),
                        getattr(b, "economy_death", 0)],
        })
        fig_pe = go.Figure()
        fig_pe.add_trace(go.Bar(
            x=phase_econ["Phase"], y=phase_econ["Economy"],
            marker=dict(color=["#38bdf8", "#a3e635", "#f87171"]),
            text=[f"{v:.1f}" for v in phase_econ["Economy"]],
            textposition="outside", textfont=dict(color="#ccc"),
        ))
        fig_pe.update_layout(**PLOTLY_LAYOUT, title=f"{bowler_sel} — Phase Economy",
                             height=420, yaxis_title="Economy")
        st.plotly_chart(fig_pe, use_container_width=True)

# ═══════════════════════════════════════════════
# IMPACT SCORE TAB
# ═══════════════════════════════════════════════
with tab3:
    @st.cache_data
    def get_impact(_d, _m):
        scores = compute_impact_scores(_d, _m)
        career = compute_career_impact(scores, min_matches=3)
        return scores, career

    impact_scores, career_impact = get_impact(del_filtered, filtered_matches)
    min_m = st.slider("Min Matches", 3, 50, 15, key="impact_min")
    ci = career_impact[career_impact.matches >= min_m].reset_index(drop=True)

    if len(ci) > 0:
        c1, c2, c3 = st.columns(3)
        c1.metric("🥇 Top Impact", ci.iloc[0].player, f"Score: {ci.iloc[0].avg_impact:.1f}")
        c2.metric("🥈 2nd", ci.iloc[1].player if len(ci) > 1 else "—",
                   f"Score: {ci.iloc[1].avg_impact:.1f}" if len(ci) > 1 else "")
        c3.metric("🥉 3rd", ci.iloc[2].player if len(ci) > 2 else "—",
                   f"Score: {ci.iloc[2].avg_impact:.1f}" if len(ci) > 2 else "")

    top20 = ci.head(20)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top20["avg_impact"], y=top20["player"],
        orientation="h",
        marker=dict(
            color=top20["avg_impact"],
            colorscale=[[0, "#1a1a2e"], [0.5, "#a3e635"], [1, "#fbbf24"]],
        ),
        text=[f'{v:.1f}' for v in top20["avg_impact"]],
        textposition="outside", textfont=dict(color="#888"),
        hovertemplate="<b>%{y}</b><br>Impact: %{x:.2f}<br><extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, title="Career Impact Score Rankings", height=620,
                      yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        ci[["player", "matches", "avg_impact", "max_impact", "avg_batting",
            "avg_bowling", "total_runs", "total_wickets"]].head(25),
        use_container_width=True, hide_index=True,
    )

# ═══════════════════════════════════════════════
# SIMILARITY TAB
# ═══════════════════════════════════════════════
with tab4:
    @st.cache_data
    def fit_similarity(_bat):
        engine = PlayerSimilarityEngine()
        arch = engine.fit_batting(_bat, min_innings=15)
        return engine, arch

    engine, bat_arch = fit_similarity(batting)
    player_sim = st.selectbox("Select Player", sorted(engine.batting_players), key="sim_sel")

    col1, col2 = st.columns(2)
    with col1:
        similar = engine.find_similar_batters(player_sim, top_n=8)
        st.markdown(f"**Players most similar to {player_sim}**")

        fig_sim = go.Figure()
        fig_sim.add_trace(go.Bar(
            x=similar["similarity"], y=similar["player"],
            orientation="h",
            marker=dict(
                color=similar["similarity"],
                colorscale=[[0, "#1a1a2e"], [1, "#a3e635"]],
            ),
            text=[f'{v:.2f}' for v in similar["similarity"]],
            textposition="outside", textfont=dict(color="#888"),
        ))
        fig_sim.update_layout(**PLOTLY_LAYOUT, title="Similarity Score",
                              height=400, yaxis=dict(autorange="reversed"),
                              xaxis=dict(range=[0, 1.1]))
        st.plotly_chart(fig_sim, use_container_width=True)

    with col2:
        archetype = bat_arch[bat_arch.batter == player_sim]["archetype"].values
        if len(archetype) > 0:
            st.metric("Player Archetype", archetype[0])

        arch_counts = bat_arch.archetype.value_counts().reset_index()
        arch_counts.columns = ["archetype", "count"]
        fig_pie = go.Figure(data=[go.Pie(
            labels=arch_counts["archetype"], values=arch_counts["count"],
            hole=0.55,
            marker=dict(colors=["#a3e635", "#38bdf8", "#c084fc", "#fb923c", "#f87171"]),
            textfont=dict(size=12, color="#fff"),
        )])
        fig_pie.update_layout(**PLOTLY_LAYOUT, title="Batting Archetypes", height=400, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)