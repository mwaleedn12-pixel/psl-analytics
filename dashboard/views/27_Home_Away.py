"""Home vs Away Analysis."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, get_team_bar_colors, fix_metrics

inject_custom_css()
fix_metrics()
hero_card("🏠 Home vs Away", "Team performance at home venues vs away/neutral venues")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv")
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()

# Home venue mapping
HOME_VENUES = {
    "Lahore Qalandars": "Gaddafi Stadium, Lahore",
    "Karachi Kings": "National Stadium, Karachi",
    "Islamabad United": "Rawalpindi Cricket Stadium",
    "Peshawar Zalmi": "Rawalpindi Cricket Stadium",
    "Quetta Gladiators": "National Stadium, Karachi",
    "Multan Sultans": "Multan Cricket Stadium",
    "Rawalpindiz": "Rawalpindi Cricket Stadium",
    "Hyderabad Kingsmen": "National Stadium, Karachi",
}

teams = sorted(set(matches.team1) | set(matches.team2))
records = []

for team in teams:
    home_venue = HOME_VENUES.get(team, "")
    team_m = matches[(matches.team1 == team) | (matches.team2 == team)].copy()
    team_m["won"] = (team_m.winner == team).astype(int)
    team_m["is_home"] = team_m.venue == home_venue

    home = team_m[team_m.is_home]
    away = team_m[~team_m.is_home]

    records.append({
        "team": team,
        "home_venue": home_venue.split(",")[0] if home_venue else "—",
        "home_played": len(home),
        "home_won": int(home.won.sum()),
        "home_win_pct": round(home.won.mean() * 100, 1) if len(home) > 0 else 0,
        "away_played": len(away),
        "away_won": int(away.won.sum()),
        "away_win_pct": round(away.won.mean() * 100, 1) if len(away) > 0 else 0,
    })

df = pd.DataFrame(records).sort_values("home_win_pct", ascending=False)

# Chart
fig = go.Figure()
fig.add_trace(go.Bar(name="Home Win%", x=df.team, y=df.home_win_pct,
                     marker=dict(color="#c9f34d")))
fig.add_trace(go.Bar(name="Away Win%", x=df.team, y=df.away_win_pct,
                     marker=dict(color="#38bdf8")))
fig.add_hline(y=50, line_dash="dot", line_color="rgba(201,243,77,0.2)")
fig.update_layout(**PLOTLY_LAYOUT, barmode="group", title="HOME vs AWAY WIN %", height=450,
                  xaxis=dict(tickangle=-30))
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df[["team", "home_venue", "home_played", "home_won", "home_win_pct",
                  "away_played", "away_won", "away_win_pct"]],
             use_container_width=True, hide_index=True)
