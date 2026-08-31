"""Match Intelligence — Win Probability and Turning Points."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.models.win_probability import WinProbabilityModel
from src.analytics.turning_points import TurningPointEngine


from dashboard.components.style import inject_custom_css, PLOTLY_LAYOUT

st.title("🧠 Match Intelligence")
inject_custom_css()

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

with st.spinner("Training Win Probability model..."):
    wp_model = train_model(deliveries, matches)

# Model metrics
st.markdown("**Model Performance**")
met = wp_model.metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("ROC-AUC", f"{met['roc_auc']:.3f}")
col2.metric("Log Loss", f"{met['log_loss']:.3f}")
col3.metric("Accuracy", f"{met['accuracy']:.1%}")
col4.metric("Brier Score", f"{met['brier_score']:.3f}")

st.markdown("---")

# Match selector
decided = matches[matches.winner.notna()].sort_values("date", ascending=False)
decided["label"] = decided.apply(
    lambda r: f"{r.psl_edition} | {r.team1} vs {r.team2} | {r.date[:10]} | Winner: {r.winner}", axis=1
)
selected = st.selectbox("Select Match", decided["label"].values)
match_id = str(decided[decided.label == selected]["match_id"].values[0])

# Win Probability Timeline
tp_engine = TurningPointEngine(wp_model)
timeline = tp_engine.compute_probability_timeline(deliveries, matches, match_id)

if not timeline.empty:
    timeline["ball_number"] = range(1, len(timeline) + 1)
    batting_team = timeline.iloc[0]["batting_team"]
    bowling_team = timeline.iloc[0]["bowling_team"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timeline["ball_number"], y=timeline["win_probability"],
        mode="lines", fill="tozeroy",
        name=f"{batting_team} (chasing)",
        line=dict(color="#2196F3", width=2),
    ))
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig.update_layout(
        title=f"Win Probability — {batting_team} chasing",
        xaxis_title="Ball Number (Innings 2)",
        yaxis_title="Win Probability",
        yaxis=dict(range=[0, 1], tickformat=".0%"),
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Turning Points
    st.subheader("🔄 Turning Points")
    points = tp_engine.detect(deliveries, matches, match_id, top_n=5, min_swing=0.03)
    if not points.empty:
        for _, tp in points.iterrows():
            direction = "🔴" if tp.prob_change < 0 else "🟢"
            st.markdown(f"{direction} **{tp.description}**")
    else:
        st.info("No significant turning points detected.")
else:
    st.warning("No innings 2 data available for this match.")