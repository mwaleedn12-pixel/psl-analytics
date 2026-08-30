"""PSL Titles & History Timeline."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, fix_metrics
from src.analytics.premium import SeasonAwards

inject_custom_css()
fix_metrics()
hero_card("👑 PSL Titles & History", "Champions, runners-up, top performers — season by season timeline")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()
awards = SeasonAwards.compute(deliveries)

# Known PSL Champions (hardcoded for accuracy — data's last match ≠ always final)
PSL_CHAMPIONS = {
    "PSL 1": "Islamabad United",
    "PSL 2": "Peshawar Zalmi",
    "PSL 3": "Islamabad United",
    "PSL 4": "Quetta Gladiators",
    "PSL 5": "Karachi Kings",
    "PSL 6": "Multan Sultans",
    "PSL 7": "Lahore Qalandars",
    "PSL 8": "Lahore Qalandars",
    "PSL 9": "Islamabad United",
    "PSL 10": "Lahore Qalandars",
    "PSL 11": "Peshawar Zalmi",
}

# Sort by season_year
season_order = matches.groupby("psl_edition")["season_year"].first().sort_values()
ordered_seasons = season_order.index.tolist()

for season in ordered_seasons:
    aw = awards[awards.season == season]
    if len(aw) == 0: continue
    aw = aw.iloc[0]

    s_matches = matches[matches.psl_edition == season].sort_values("date", ascending=False)
    final = s_matches.iloc[0] if len(s_matches) > 0 else None

    champion = PSL_CHAMPIONS.get(season, final.winner if final is not None and pd.notna(final.winner) else "—")
    tc = TEAM_COLORS.get(champion, {"primary": "#c9f34d"})

    teams_in_final = f"{final.team1} vs {final.team2}" if final is not None else "—"
    venue = final.venue.split(",")[0] if final is not None else "—"
    margin = ""
    if final is not None:
        if pd.notna(final.win_by_runs): margin = f"by {int(final.win_by_runs)} runs"
        elif pd.notna(final.win_by_wickets): margin = f"by {int(final.win_by_wickets)} wickets"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {tc['primary']}15, rgba(13,43,31,0.5));
         border: 1px solid {tc['primary']}33; border-radius:14px; padding:20px; margin:10px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-family:Oswald; font-size:1.3rem; color:#c9f34d; text-transform:uppercase;">{season}</div>
                <div style="font-family:Oswald; font-size:1.1rem; color:{tc['primary']}; margin-top:4px;">🏆 {champion}</div>
                <div style="color:#5a8a6f; font-size:0.8rem; margin-top:4px;">Final: {teams_in_final} | {venue} | {margin}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:'Share Tech Mono'; color:#7aaa8f; font-size:0.75rem;">
                    🏏 {aw.best_batter} ({aw.batter_runs}r)<br>
                    🎯 {aw.best_bowler} ({aw.bowler_wickets}w)<br>
                    ⭐ {aw.best_allrounder}<br>
                    💥 {aw.most_sixes_player} ({aw.most_sixes} 6s)
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

# Titles count
st.markdown("---")
st.markdown("##### 🏆 Title Count")
from collections import Counter
title_count = Counter(PSL_CHAMPIONS.values())
for team, count in sorted(title_count.items(), key=lambda x: -x[1]):
    tc = TEAM_COLORS.get(team, {"primary":"#c9f34d"})
    trophies = "🏆" * count
    st.markdown(f"<span style='font-family:Oswald; color:{tc['primary']}; font-size:1.1rem;'>{team}</span> — {trophies} ({count})", unsafe_allow_html=True)