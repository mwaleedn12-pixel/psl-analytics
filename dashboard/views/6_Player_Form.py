"""Player Form — rolling averages and trends."""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.analytics.engines import FormEngine
from src.analytics.extended_engines import SeasonImprovement


from dashboard.components.style import inject_custom_css, PLOTLY_LAYOUT

st.title("📈 Player Form")
inject_custom_css()

@st.cache_data
def load_data():
    P = PROJECT_ROOT / "data" / "processed"
    return pd.read_csv(P / "psl_deliveries_clean.csv", low_memory=False)

deliveries = load_data()

tab1, tab2, tab3 = st.tabs(["Batting Form", "Bowling Form", "Season Trends"])

with tab1:
    window = st.slider("Rolling Window", 3, 15, 5, key="bat_window")
    form = FormEngine.batting_form(deliveries, window=window)
    batters = form.groupby("batter")["match_number"].max()
    qualified = batters[batters >= 15].index.tolist()
    player = st.selectbox("Select Batter", sorted(qualified), key="bat_sel")
    pdata = form[form.batter == player]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(pdata, x="match_number", y="rolling_avg",
                      title=f"{player} — Rolling Average (last {window})",
                      labels={"match_number": "Match #", "rolling_avg": "Rolling Avg"})
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.line(pdata, x="match_number", y="rolling_sr",
                       title=f"{player} — Rolling Strike Rate",
                       labels={"match_number": "Match #", "rolling_sr": "Rolling SR"})
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    window_b = st.slider("Rolling Window", 3, 15, 5, key="bowl_window")
    bform = FormEngine.bowling_form(deliveries, window=window_b)
    bowlers_q = bform.groupby("bowler")["match_number"].max()
    qualified_b = bowlers_q[bowlers_q >= 15].index.tolist()
    bowler = st.selectbox("Select Bowler", sorted(qualified_b), key="bowl_sel")
    bdata = bform[bform.bowler == bowler]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(bdata, x="match_number", y="rolling_economy",
                      title=f"{bowler} — Rolling Economy",
                      labels={"match_number": "Match #", "rolling_economy": "Economy"})
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.line(bdata, x="match_number", y="rolling_wickets",
                       title=f"{bowler} — Rolling Wickets/Match",
                       labels={"match_number": "Match #", "rolling_wickets": "Wickets"})
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    trends = SeasonImprovement.batting_trend(deliveries, min_seasons=3)
    improving = trends[trends.trend == "Improving"].head(10)
    declining = trends[trends.trend == "Declining"].head(10)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📈 Most Improving**")
        st.dataframe(improving[["batter", "seasons", "career_sr", "recent_sr", "sr_trend_slope"]],
                     use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**📉 Declining**")
        st.dataframe(declining[["batter", "seasons", "career_sr", "recent_sr", "sr_trend_slope"]],
                     use_container_width=True, hide_index=True)