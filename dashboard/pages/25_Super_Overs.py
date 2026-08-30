"""Super Over Analytics."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, fix_metrics

inject_custom_css()
fix_metrics()
hero_card("⚡ Super Over Analytics", "All PSL super overs — teams, players, results")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv")
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()

# Super overs = innings 3 or 4
super_overs = deliveries[deliveries.innings > 2]
so_matches = super_overs.match_id.unique()

st.metric("Total Super Overs", len(so_matches))

if len(so_matches) > 0:
    for mid in so_matches:
        so = super_overs[super_overs.match_id == mid]
        match = matches[matches.match_id == mid]
        if len(match) == 0: continue
        m = match.iloc[0]
        winner = m.winner if pd.notna(m.winner) else "Tie"

        st.markdown(f"""
        <div style="background:rgba(13,43,31,0.5); border-radius:12px; padding:14px 20px; margin:8px 0;
             border-left: 3px solid #c9f34d;">
            <span style="font-family:Oswald; color:#c9f34d;">{m.psl_edition}</span> —
            <span style="color:#fff;">{m.team1} vs {m.team2}</span> |
            <span style="font-family:'Share Tech Mono'; color:#f0b429;">Winner: {winner}</span>
        </div>""", unsafe_allow_html=True)

        for inn in sorted(so.innings.unique()):
            inn_data = so[so.innings == inn]
            bt = inn_data.batting_team.iloc[0]
            runs = inn_data.total_runs.sum()
            wkts = inn_data.is_wicket.sum()
            batters = ", ".join(inn_data.batter.unique())
            bowler = inn_data.bowler.unique()[0] if len(inn_data.bowler.unique()) > 0 else "—"
            st.markdown(f"&nbsp;&nbsp; Inn {inn}: **{bt}** {runs}/{wkts} | Batters: {batters} | Bowler: {bowler}")
        st.markdown("---")
else:
    st.info("No super over data found in the dataset.")
