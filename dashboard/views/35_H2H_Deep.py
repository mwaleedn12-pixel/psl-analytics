"""Head-to-Head Deep Dive — detailed batter vs bowler with phase breakdown."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, fix_metrics

inject_custom_css()
fix_metrics()
hero_card("⚔️ H2H Deep Dive", "Detailed batter vs bowler — phase breakdown, season trend, dismissal types")
seam_divider()

@st.cache_data
def load_data():
    return pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
deliveries = load_data()
legal = deliveries[deliveries.is_legal == 1]

batters = sorted(legal.batter.unique())
bowlers = sorted(deliveries.bowler.unique())

col1, col2 = st.columns(2)
with col1:
    batter = st.selectbox("Select Batter", batters, index=batters.index("Babar Azam") if "Babar Azam" in batters else 0)
with col2:
    bowler = st.selectbox("Select Bowler", bowlers, index=bowlers.index("Shaheen Shah Afridi") if "Shaheen Shah Afridi" in bowlers else 0)

# Filter matchup data
h2h = deliveries[(deliveries.batter == batter) & (deliveries.bowler == bowler)]
h2h_legal = h2h[h2h.is_legal == 1]

if len(h2h) == 0:
    st.warning(f"No head-to-head data between {batter} and {bowler}.")
else:
    balls = len(h2h_legal)
    runs = int(h2h_legal.batter_runs.sum())
    sr = round(runs / balls * 100, 1) if balls > 0 else 0
    fours = int(h2h_legal.is_four.sum())
    sixes = int(h2h_legal.is_six.sum())
    dots = int(h2h_legal.is_dot.sum())
    dismissals = int(h2h.is_wicket.sum())
    dot_pct = round(dots / balls * 100, 1) if balls > 0 else 0
    bnd_pct = round((fours + sixes) / balls * 100, 1) if balls > 0 else 0

    # KPIs
    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    c1.metric("Balls", balls)
    c2.metric("Runs", runs)
    c3.metric("SR", sr)
    c4.metric("4s", fours)
    c5.metric("6s", sixes)
    c6.metric("Dots", dots)
    c7.metric("Dismissed", dismissals)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["⏱️ Phase Breakdown", "📅 Season Trend", "💀 Dismissals"])

    with tab1:
        phase_data = []
        for phase in ["powerplay", "middle", "death"]:
            ph = h2h_legal[h2h_legal.phase == phase]
            if len(ph) == 0:
                phase_data.append({"Phase": phase.title(), "Balls": 0, "Runs": 0, "SR": 0, "Dots": 0, "Boundaries": 0})
            else:
                phase_data.append({
                    "Phase": phase.title(),
                    "Balls": len(ph),
                    "Runs": int(ph.batter_runs.sum()),
                    "SR": round(ph.batter_runs.sum() / len(ph) * 100, 1),
                    "Dots": int(ph.is_dot.sum()),
                    "Boundaries": int(ph.is_four.sum() + ph.is_six.sum()),
                })
        pdf = pd.DataFrame(phase_data)

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=pdf.Phase, y=pdf.SR,
                marker=dict(color=["#38bdf8","#c9f34d","#f87171"]),
                text=[f"{v}" for v in pdf.SR], textposition="outside",
                textfont=dict(color="#c9f34d", family="Share Tech Mono")))
            fig.update_layout(**PLOTLY_LAYOUT, title="STRIKE RATE BY PHASE", height=350)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=pdf.Phase, y=pdf.Runs,
                marker=dict(color=["#38bdf8","#c9f34d","#f87171"]),
                text=pdf.Runs, textposition="outside",
                textfont=dict(color="#c9f34d", family="Share Tech Mono")))
            fig2.update_layout(**PLOTLY_LAYOUT, title="RUNS BY PHASE", height=350)
            st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(pdf, use_container_width=True, hide_index=True)

    with tab2:
        season = h2h_legal.groupby("psl_edition").agg(
            balls=("batter_runs","count"), runs=("batter_runs","sum"),
            dismissed=("is_wicket","sum"),
        ).reset_index()
        season["sr"] = (season.runs / season.balls * 100).round(1)

        if len(season) > 0:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(x=season.psl_edition, y=season.runs, name="Runs",
                                   marker=dict(color="#c9f34d", opacity=0.6)))
            fig3.add_trace(go.Scatter(x=season.psl_edition, y=season.sr, name="SR",
                                      yaxis="y2", line=dict(color="#f0b429", width=3),
                                      mode="lines+markers"))
            fig3.update_layout(**PLOTLY_LAYOUT, title="SEASON-WISE MATCHUP", height=400,
                                yaxis2=dict(overlaying="y", side="right", title="SR",
                                            gridcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig3, use_container_width=True)
            st.dataframe(season, use_container_width=True, hide_index=True)

    with tab3:
        wkts = h2h[h2h.is_wicket == 1]
        if len(wkts) > 0:
            dis_types = wkts.wicket_kind.value_counts().reset_index()
            dis_types.columns = ["type", "count"]
            fig4 = go.Figure(data=[go.Pie(labels=dis_types.type, values=dis_types["count"], hole=0.5,
                  marker=dict(colors=["#c9f34d","#38bdf8","#f87171","#fb923c","#c084fc"]),
                  textfont=dict(color="#fff", family="Oswald"))])
            fig4.update_layout(**PLOTLY_LAYOUT, title="DISMISSAL TYPES", height=350, showlegend=True)
            st.plotly_chart(fig4, use_container_width=True)

            st.markdown("##### Dismissal Details")
            for _, w in wkts.iterrows():
                over_ball = f"{w['over']-1}.{w['ball']}"
                st.markdown(f"💀 **{w.psl_edition}** — {w.wicket_kind} at {over_ball}")
        else:
            st.info(f"{bowler} has never dismissed {batter}.")

    # Verdict
    st.markdown("---")
    if sr > 130 and dismissals == 0:
        verdict = f"🟢 **{batter} dominates** — SR {sr}, never dismissed"
    elif sr > 130:
        verdict = f"🟡 **{batter} attacks but risky** — SR {sr}, dismissed {dismissals}x"
    elif dismissals >= 3:
        verdict = f"🔴 **{bowler} dominates** — dismissed {batter} {dismissals}x, conceded SR {sr}"
    elif sr < 100:
        verdict = f"🔴 **{bowler} controls** — keeps {batter} to SR {sr}"
    else:
        verdict = f"🟡 **Even contest** — SR {sr}, {dismissals} dismissal(s)"

    st.markdown(f"""
    <div style="background:rgba(13,43,31,0.5); border-radius:12px; padding:16px 20px; text-align:center;
         border:1px solid rgba(201,243,77,0.15);">
        <div style="font-family:Oswald; color:#c9f34d; font-size:0.8rem; text-transform:uppercase; letter-spacing:2px;">Verdict</div>
        <div style="color:#fff; font-size:1rem; margin-top:8px;">{verdict}</div>
    </div>""", unsafe_allow_html=True)
