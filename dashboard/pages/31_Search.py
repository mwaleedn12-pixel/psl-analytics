"""Universal Search — search any player, team, venue, or match."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, fix_metrics
from src.analytics.stats_engine import StatsEngine

inject_custom_css()
fix_metrics()
hero_card("🔎 Universal Search", "Search any player, team, or venue — instant stats")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d
matches, deliveries = load_data()

query = st.text_input("🔍 Search (player name, team, or venue)", placeholder="e.g. Babar Azam, Lahore Qalandars, Gaddafi Stadium")

if query and len(query) >= 2:
    q = query.lower().strip()

    # ── Search Players ──
    all_batters = deliveries[deliveries.is_legal == 1].batter.unique()
    all_bowlers = deliveries.bowler.unique()
    all_players = sorted(set(all_batters) | set(all_bowlers))
    matched_players = [p for p in all_players if q in p.lower()]

    # ── Search Teams ──
    all_teams = sorted(set(matches.team1) | set(matches.team2))
    matched_teams = [t for t in all_teams if q in t.lower()]

    # ── Search Venues ──
    all_venues = sorted(matches.venue.unique())
    matched_venues = [v for v in all_venues if q in v.lower()]

    # ── Search Matches ──
    matched_matches = matches[
        matches.apply(lambda r: q in str(r.team1).lower() or q in str(r.team2).lower()
                      or q in str(r.winner).lower() or q in str(r.player_of_match).lower(), axis=1)
    ].sort_values("date", ascending=False).head(10)

    found = len(matched_players) + len(matched_teams) + len(matched_venues) + len(matched_matches)
    st.caption(f"Found **{found}** results for \"{query}\"")
    st.markdown("---")

    # ── Player Results ──
    if matched_players:
        st.markdown(f"##### 👤 Players ({len(matched_players)})")
        for player in matched_players[:10]:
            is_bat = player in all_batters
            is_bowl = player in all_bowlers

            with st.expander(f"{'🏏' if is_bat else '🎯'} **{player}**"):
                if is_bat:
                    legal = deliveries[(deliveries.is_legal == 1) & (deliveries.batter == player)]
                    runs = int(legal.batter_runs.sum())
                    balls = len(legal)
                    inn = legal.match_id.nunique()
                    sr = round(runs / balls * 100, 1) if balls > 0 else 0
                    avg = round(runs / inn, 1) if inn > 0 else 0
                    hs = int(legal.groupby("match_id")["batter_runs"].sum().max()) if inn > 0 else 0
                    fours = int(legal.is_four.sum())
                    sixes = int(legal.is_six.sum())
                    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
                    c1.metric("Inn", inn)
                    c2.metric("Runs", runs)
                    c3.metric("Avg", avg)
                    c4.metric("SR", sr)
                    c5.metric("HS", hs)
                    c6.metric("4s", fours)
                    c7.metric("6s", sixes)

                if is_bowl:
                    bd = deliveries[deliveries.bowler == player]
                    wkts = int(bd.is_wicket.sum())
                    legal_b = int(bd.is_legal.sum())
                    overs = round(legal_b / 6, 1)
                    runs_c = int(bd.total_runs.sum())
                    econ = round(runs_c / overs, 2) if overs > 0 else 0
                    inn_b = bd.match_id.nunique()
                    c1,c2,c3,c4,c5 = st.columns(5)
                    c1.metric("Inn", inn_b)
                    c2.metric("Wickets", wkts)
                    c3.metric("Economy", econ)
                    c4.metric("Overs", overs)
                    c5.metric("Runs Conceded", runs_c)

    # ── Team Results ──
    if matched_teams:
        st.markdown(f"##### 👥 Teams ({len(matched_teams)})")
        for team in matched_teams:
            tc = TEAM_COLORS.get(team, {"primary": "#c9f34d"})
            tm = matches[(matches.team1 == team) | (matches.team2 == team)]
            wins = len(tm[tm.winner == team])
            win_pct = round(wins / len(tm) * 100, 1) if len(tm) > 0 else 0

            st.markdown(f"""
            <div style="background:linear-gradient(135deg, {tc['primary']}15, rgba(13,43,31,0.5));
                 border:1px solid {tc['primary']}33; border-radius:12px; padding:14px 20px; margin:6px 0;">
                <span style="font-family:Oswald; color:{tc['primary']}; font-size:1.1rem;">{team}</span>
                <span style="font-family:'Share Tech Mono'; color:#7aaa8f; float:right;">
                    {len(tm)} matches | {wins}W | {win_pct}% win rate
                </span>
            </div>""", unsafe_allow_html=True)

    # ── Venue Results ──
    if matched_venues:
        st.markdown(f"##### 🏟️ Venues ({len(matched_venues)})")
        for venue in matched_venues:
            vm = matches[matches.venue == venue]
            innings = deliveries[deliveries.venue == venue].groupby(["match_id","innings"])["total_runs"].sum()
            avg_score = round(innings.mean(), 0) if len(innings) > 0 else 0
            st.markdown(f"🏟️ **{venue}** — {len(vm)} matches, Avg Score: {avg_score}")

    # ── Match Results ──
    if len(matched_matches) > 0:
        st.markdown(f"##### 📋 Matches")
        for _, m in matched_matches.iterrows():
            winner = m.winner if pd.notna(m.winner) else "No Result"
            st.markdown(f"📅 **{str(m.date)[:10]}** | {m.team1} vs {m.team2} | {m.psl_edition} | Winner: {winner}")

elif query:
    st.info("Type at least 2 characters to search.")
