"""Predictions — Live Win Probability Simulator."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.models.win_probability import WinProbabilityModel


from dashboard.components.style import inject_custom_css, PLOTLY_LAYOUT

st.title("🔮 Win Probability Simulator")
inject_custom_css()
st.markdown("Simulate match situations and see predicted win probability.")

@st.cache_data
def load_data():
    P = PROJECT_ROOT / "data" / "processed"
    m = pd.read_csv(P / "psl_matches_clean.csv")
    d = pd.read_csv(P / "psl_deliveries_clean.csv", low_memory=False)
    return m, d

@st.cache_resource
def train_model(_d, _m):
    wp = WinProbabilityModel("logistic")
    wp.train(_d, _m)
    return wp

matches, deliveries = load_data()
wp_model = train_model(deliveries, matches)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    target = st.number_input("Target Score", 100, 250, 175)
    current_score = st.number_input("Current Score", 0, 250, 85)
    wickets_lost = st.slider("Wickets Lost", 0, 9, 2)
    overs_completed = st.slider("Overs Completed", 1, 19, 10)
with col2:
    venue = st.selectbox("Venue", sorted(deliveries.venue.unique()))
    teams = sorted(deliveries.batting_team.unique())
    batting_team = st.selectbox("Batting Team (Chasing)", teams)
    bowling_team = st.selectbox("Bowling Team", [t for t in teams if t != batting_team])

required_runs = target - current_score
balls_remaining = (20 - overs_completed) * 6
overs_remaining = 20 - overs_completed
current_rr = current_score / overs_completed if overs_completed > 0 else 0
required_rr = required_runs / overs_remaining if overs_remaining > 0 else 999
rr_ratio = current_rr / required_rr if required_rr > 0 else 0

phase = "powerplay" if overs_completed <= 6 else ("middle" if overs_completed <= 15 else "death")

# Encode features
phase_enc = dict(zip(wp_model.phase_encoder.classes_,
                      wp_model.phase_encoder.transform(wp_model.phase_encoder.classes_)))
venue_enc = dict(zip(wp_model.venue_encoder.classes_,
                      wp_model.venue_encoder.transform(wp_model.venue_encoder.classes_)))

features = pd.DataFrame([{
    "cumulative_runs": current_score,
    "cumulative_wickets": wickets_lost,
    "balls_remaining": balls_remaining,
    "required_runs": required_runs,
    "required_rr": required_rr,
    "current_rr": round(current_rr, 2),
    "rr_ratio": round(rr_ratio, 3),
    "over": overs_completed,
    "phase_encoded": phase_enc.get(phase, 0),
    "venue_encoded": venue_enc.get(venue, 0),
}])

if wp_model.scaler:
    features_scaled = pd.DataFrame(
        wp_model.scaler.transform(features), columns=wp_model.FEATURES
    )
else:
    features_scaled = features

win_prob = wp_model.model.predict_proba(features_scaled[wp_model.FEATURES])[0][1]

st.markdown("---")

# Results
col1, col2, col3 = st.columns(3)
col1.metric("Chasing Win Probability", f"{win_prob:.1%}")
col2.metric("Required Runs", f"{required_runs}")
col3.metric("Required RR", f"{required_rr:.2f}")

# Gauge chart
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=win_prob * 100,
    title={"text": f"{batting_team} Win Probability"},
    number={"suffix": "%"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "#2196F3"},
        "steps": [
            {"range": [0, 30], "color": "#FFCDD2"},
            {"range": [30, 70], "color": "#FFF9C4"},
            {"range": [70, 100], "color": "#C8E6C9"},
        ],
    }
))
fig.update_layout(**PLOTLY_LAYOUT, height=350)
st.plotly_chart(fig, use_container_width=True)

# Factors
st.markdown("**Key Factors:**")
if required_rr < 7:
    st.markdown("✅ Low required run rate — comfortable position")
elif required_rr > 12:
    st.markdown("⚠️ Very high required run rate — under pressure")
if wickets_lost >= 6:
    st.markdown("⚠️ Many wickets down — tail exposed")
elif wickets_lost <= 2:
    st.markdown("✅ Wickets in hand — strong position")
if balls_remaining < 30:
    st.markdown("⏰ Limited balls remaining — need acceleration")