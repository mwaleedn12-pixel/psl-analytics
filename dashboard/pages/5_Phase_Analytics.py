"""Phase Analytics — Powerplay, Middle, Death analysis."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.analytics.engines import PhaseEngine
from src.analytics.extended_engines import PowerplayIndex, DeathSpecialists


from dashboard.components.style import inject_custom_css, PLOTLY_LAYOUT

st.title("⏱️ Phase Analytics")
inject_custom_css()

@st.cache_data
def load_data():
    P = PROJECT_ROOT / "data" / "processed"
    return pd.read_csv(P / "psl_deliveries_clean.csv", low_memory=False)

deliveries = load_data()
summary = PhaseEngine.phase_summary(deliveries)

# KPIs
col1, col2, col3 = st.columns(3)
for i, (_, row) in enumerate(summary.iterrows()):
    [col1, col2, col3][i].metric(
        f"{row.phase.title()} RPO", f"{row.rpo}",
        delta=f"SR {row.sr} | Dot {row.dot_pct}%"
    )

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(summary, x="phase", y="rpo", title="Runs Per Over by Phase",
                 color="phase", color_discrete_map={
                     "powerplay": "#2196F3", "middle": "#4CAF50", "death": "#F44336"})
    fig.update_layout(**PLOTLY_LAYOUT, height=350)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = px.bar(summary, x="phase", y="wickets_per_over", title="Wickets Per Over",
                  color="phase", color_discrete_map={
                      "powerplay": "#2196F3", "middle": "#4CAF50", "death": "#F44336"})
    fig2.update_layout(**PLOTLY_LAYOUT, height=350)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
tab1, tab2 = st.tabs(["Powerplay Aggressors", "Death Specialists"])

with tab1:
    pp = PowerplayIndex.compute(deliveries, min_innings=10)
    st.dataframe(pp.head(20), use_container_width=True, hide_index=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Best Finishers**")
        fin = DeathSpecialists.best_finishers(deliveries, min_innings=10)
        st.dataframe(fin[["batter", "innings", "runs", "sr", "boundary_pct", "finisher_score"]].head(15),
                     use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**Best Death Bowlers**")
        db = DeathSpecialists.best_death_bowlers(deliveries, min_innings=10)
        st.dataframe(db[["bowler", "innings", "wickets", "economy", "dot_pct", "death_score"]].head(15),
                     use_container_width=True, hide_index=True)