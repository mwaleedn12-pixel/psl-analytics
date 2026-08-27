# ---
# jupyter:
#   title: PSL Analytics — Exploratory Data Analysis
# ---

"""
PSL Analytics — 01 Data Exploration

Exploratory analysis of PSL ball-by-ball data covering:
1. Dataset Overview
2. Season Trends
3. Team Performance
4. Batting Analysis
5. Bowling Analysis
6. Venue Analysis
7. Toss Analysis
8. Phase Analysis
9. Chasing vs Defending

Run: python notebooks/01_data_exploration.py
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Load Data ──
PROCESSED = PROJECT_ROOT / "data" / "processed"
matches = pd.read_csv(PROCESSED / "psl_matches_clean.csv", parse_dates=["date"])
deliveries = pd.read_csv(PROCESSED / "psl_deliveries_clean.csv", parse_dates=["date"], low_memory=False)

print("=" * 60)
print("PSL ANALYTICS — EXPLORATORY DATA ANALYSIS")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. DATASET OVERVIEW
# ════════════════════════════════════════════════════════════
print("\n📊 1. DATASET OVERVIEW")
print("-" * 40)
print(f"Total matches:      {len(matches)}")
print(f"Total deliveries:   {len(deliveries)}")
print(f"Seasons:            {matches.psl_edition.nunique()} (PSL 1 → PSL 11)")
print(f"Date range:         {matches.date.min().date()} → {matches.date.max().date()}")
print(f"Teams:              {matches.team1.nunique()}")
print(f"Venues:             {matches.venue.nunique()}")
print(f"Unique batters:     {deliveries.batter.nunique()}")
print(f"Unique bowlers:     {deliveries.bowler.nunique()}")
print(f"Total runs scored:  {deliveries.total_runs.sum():,}")
print(f"Total wickets:      {deliveries.is_wicket.sum():,}")
print(f"Total fours:        {deliveries.is_four.sum():,}")
print(f"Total sixes:        {deliveries.is_six.sum():,}")


# ════════════════════════════════════════════════════════════
# 2. SEASON TRENDS
# ════════════════════════════════════════════════════════════
print("\n📅 2. SEASON TRENDS")
print("-" * 40)

season_stats = matches.groupby(["psl_edition", "season_year"]).agg(
    matches=("match_id", "count"),
    teams=("team1", "nunique"),
).sort_values("season_year").reset_index()

# Average score per season
innings_totals = deliveries.groupby(["match_id", "innings", "psl_edition", "season_year"]).agg(
    total=("total_runs", "sum")
).reset_index()

season_avg_score = innings_totals.groupby(["psl_edition", "season_year"])["total"].mean().reset_index()
season_avg_score.columns = ["psl_edition", "season_year", "avg_innings_score"]
season_stats = season_stats.merge(season_avg_score, on=["psl_edition", "season_year"])

print(f"{'Season':<10} {'Matches':>8} {'Avg Score':>10}")
print("-" * 30)
for _, row in season_stats.iterrows():
    print(f"{row.psl_edition:<10} {int(row.matches):>8} {row.avg_innings_score:>10.1f}")


# ════════════════════════════════════════════════════════════
# 3. TEAM PERFORMANCE
# ════════════════════════════════════════════════════════════
print("\n🏏 3. TEAM PERFORMANCE")
print("-" * 40)

# Get all team appearances
team_matches = []
for _, row in matches.iterrows():
    for team in [row.team1, row.team2]:
        won = 1 if team == row.winner else 0
        team_matches.append({"team": team, "won": won, "match_id": row.match_id})

team_df = pd.DataFrame(team_matches)
team_perf = team_df.groupby("team").agg(
    played=("match_id", "count"),
    won=("won", "sum"),
).reset_index()
team_perf["lost"] = team_perf["played"] - team_perf["won"]
team_perf["win_pct"] = (team_perf["won"] / team_perf["played"] * 100).round(1)
team_perf = team_perf.sort_values("win_pct", ascending=False)

print(f"{'Team':<25} {'P':>4} {'W':>4} {'L':>4} {'Win%':>6}")
print("-" * 45)
for _, row in team_perf.iterrows():
    print(f"{row.team:<25} {int(row.played):>4} {int(row.won):>4} {int(row.lost):>4} {row.win_pct:>6.1f}")


# ════════════════════════════════════════════════════════════
# 4. TOP BATTERS
# ════════════════════════════════════════════════════════════
print("\n🏏 4. TOP BATTERS (by runs)")
print("-" * 40)

batter_stats = deliveries[deliveries.is_legal == 1].groupby("batter").agg(
    innings=("match_id", "nunique"),
    balls=("batter_runs", "count"),
    runs=("batter_runs", "sum"),
    fours=("is_four", "sum"),
    sixes=("is_six", "sum"),
    dots=("is_dot", "sum"),
).reset_index()

batter_stats["sr"] = (batter_stats["runs"] / batter_stats["balls"] * 100).round(1)
batter_stats["avg"] = (batter_stats["runs"] / batter_stats["innings"]).round(1)
batter_stats["boundary_pct"] = (
    (batter_stats["fours"] + batter_stats["sixes"]) / batter_stats["balls"] * 100
).round(1)

top_batters = batter_stats[batter_stats.innings >= 10].sort_values("runs", ascending=False).head(15)

print(f"{'Batter':<25} {'Inn':>4} {'Runs':>5} {'Avg':>6} {'SR':>7} {'4s':>4} {'6s':>4} {'Bnd%':>5}")
print("-" * 62)
for _, r in top_batters.iterrows():
    print(f"{r.batter:<25} {int(r.innings):>4} {int(r.runs):>5} {r.avg:>6.1f} {r.sr:>7.1f} {int(r.fours):>4} {int(r.sixes):>4} {r.boundary_pct:>5.1f}")


# ════════════════════════════════════════════════════════════
# 5. TOP BOWLERS
# ════════════════════════════════════════════════════════════
print("\n🎳 5. TOP BOWLERS (by wickets)")
print("-" * 40)

bowler_stats = deliveries.groupby("bowler").agg(
    innings=("match_id", "nunique"),
    balls_total=("bowler", "count"),
    legal_balls=("is_legal", "sum"),
    runs_conceded=("total_runs", "sum"),
    wickets=("is_wicket", "sum"),
    dots=("is_dot", "sum"),
    wides=("is_wide", "sum"),
    noballs=("is_noball", "sum"),
).reset_index()

bowler_stats["overs"] = bowler_stats["legal_balls"] / 6
bowler_stats["economy"] = (bowler_stats["runs_conceded"] / bowler_stats["overs"]).round(2)
bowler_stats["dot_pct"] = (bowler_stats["dots"] / bowler_stats["legal_balls"] * 100).round(1)

top_bowlers = bowler_stats[bowler_stats.innings >= 10].sort_values("wickets", ascending=False).head(15)

print(f"{'Bowler':<25} {'Inn':>4} {'Wkts':>5} {'Econ':>6} {'Dot%':>5}")
print("-" * 47)
for _, r in top_bowlers.iterrows():
    print(f"{r.bowler:<25} {int(r.innings):>4} {int(r.wickets):>5} {r.economy:>6.2f} {r.dot_pct:>5.1f}")


# ════════════════════════════════════════════════════════════
# 6. VENUE ANALYSIS
# ════════════════════════════════════════════════════════════
print("\n🏟️ 6. VENUE ANALYSIS")
print("-" * 40)

# Average score per venue
venue_scores = innings_totals.merge(
    matches[["match_id", "venue"]].drop_duplicates(), on="match_id"
)
venue_avg = venue_scores.groupby("venue").agg(
    matches=("match_id", "nunique"),
    avg_score=("total", "mean"),
).reset_index()

# Chasing win % per venue
chasing_matches = matches[matches.winner.notna()].copy()
chasing_matches["batting_first"] = chasing_matches["team1"]  # team1 bats first in CricSheet
chasing_matches["chasing_won"] = (chasing_matches["winner"] != chasing_matches["team1"]).astype(int)

venue_chase = chasing_matches.groupby("venue").agg(
    total=("match_id", "count"),
    chase_wins=("chasing_won", "sum"),
).reset_index()
venue_chase["chase_win_pct"] = (venue_chase["chase_wins"] / venue_chase["total"] * 100).round(1)

venue_analysis = venue_avg.merge(venue_chase[["venue", "chase_win_pct"]], on="venue", how="left")
venue_analysis = venue_analysis.sort_values("avg_score", ascending=False)

print(f"{'Venue':<40} {'Mat':>4} {'Avg':>6} {'Chase%':>7}")
print("-" * 59)
for _, r in venue_analysis.iterrows():
    chase = f"{r.chase_win_pct:.1f}" if pd.notna(r.chase_win_pct) else "N/A"
    print(f"{r.venue:<40} {int(r.matches):>4} {r.avg_score:>6.1f} {chase:>7}")


# ════════════════════════════════════════════════════════════
# 7. TOSS ANALYSIS
# ════════════════════════════════════════════════════════════
print("\n🪙 7. TOSS ANALYSIS")
print("-" * 40)

toss_matches = matches[matches.winner.notna()].copy()
toss_matches["toss_winner_won"] = (toss_matches["toss_winner"] == toss_matches["winner"]).astype(int)

toss_overall = toss_matches["toss_winner_won"].mean() * 100
print(f"Toss winner wins match: {toss_overall:.1f}%")

toss_by_decision = toss_matches.groupby("toss_decision").agg(
    total=("match_id", "count"),
    toss_winner_won=("toss_winner_won", "sum"),
).reset_index()
toss_by_decision["win_pct"] = (toss_by_decision["toss_winner_won"] / toss_by_decision["total"] * 100).round(1)

print(f"\nToss decision breakdown:")
print(f"  Field first chosen: {len(toss_matches[toss_matches.toss_decision=='field'])}/{len(toss_matches)} ({len(toss_matches[toss_matches.toss_decision=='field'])/len(toss_matches)*100:.0f}%)")
for _, r in toss_by_decision.iterrows():
    print(f"  Chose to {r.toss_decision}: won {r.win_pct:.1f}% ({int(r.toss_winner_won)}/{int(r.total)})")


# ════════════════════════════════════════════════════════════
# 8. PHASE ANALYSIS
# ════════════════════════════════════════════════════════════
print("\n⏱️ 8. PHASE ANALYSIS")
print("-" * 40)

phase_stats = deliveries.groupby("phase").agg(
    balls=("is_legal", "sum"),
    runs=("total_runs", "sum"),
    wickets=("is_wicket", "sum"),
    fours=("is_four", "sum"),
    sixes=("is_six", "sum"),
    dots=("is_dot", "sum"),
).reset_index()

phase_stats["rpo"] = (phase_stats["runs"] / (phase_stats["balls"] / 6)).round(2)
phase_stats["sr"] = (phase_stats["runs"] / phase_stats["balls"] * 100).round(1)
phase_stats["dot_pct"] = (phase_stats["dots"] / phase_stats["balls"] * 100).round(1)
phase_stats["boundary_pct"] = ((phase_stats["fours"] + phase_stats["sixes"]) / phase_stats["balls"] * 100).round(1)
phase_stats["wkt_per_over"] = (phase_stats["wickets"] / (phase_stats["balls"] / 6)).round(2)

phase_order = {"powerplay": 0, "middle": 1, "death": 2}
phase_stats["order"] = phase_stats["phase"].map(phase_order)
phase_stats = phase_stats.sort_values("order")

print(f"{'Phase':<12} {'RPO':>6} {'SR':>6} {'Dot%':>6} {'Bnd%':>6} {'Wkt/Ov':>7}")
print("-" * 45)
for _, r in phase_stats.iterrows():
    print(f"{r.phase:<12} {r.rpo:>6.2f} {r.sr:>6.1f} {r.dot_pct:>6.1f} {r.boundary_pct:>6.1f} {r.wkt_per_over:>7.2f}")


# ════════════════════════════════════════════════════════════
# 9. CHASING VS DEFENDING
# ════════════════════════════════════════════════════════════
print("\n🎯 9. CHASING VS DEFENDING")
print("-" * 40)

result_matches = matches[matches.winner.notna()].copy()
chase_wins = result_matches["win_by_wickets"].notna().sum()
defend_wins = result_matches["win_by_runs"].notna().sum()
total_decided = chase_wins + defend_wins

print(f"Chasing wins:   {chase_wins}/{total_decided} ({chase_wins/total_decided*100:.1f}%)")
print(f"Defending wins: {defend_wins}/{total_decided} ({defend_wins/total_decided*100:.1f}%)")

# By season
print(f"\nChasing win % by season:")
season_chase = result_matches.copy()
season_chase["chase_won"] = season_chase["win_by_wickets"].notna().astype(int)
by_season = season_chase.groupby(["psl_edition", "season_year"]).agg(
    total=("match_id", "count"),
    chase_wins=("chase_won", "sum"),
).reset_index().sort_values("season_year")
by_season["chase_pct"] = (by_season["chase_wins"] / by_season["total"] * 100).round(1)

for _, r in by_season.iterrows():
    print(f"  {r.psl_edition:<10} {r.chase_pct:>5.1f}% ({int(r.chase_wins)}/{int(r.total)})")


# ════════════════════════════════════════════════════════════
# 10. KEY FINDINGS SUMMARY
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("📋 KEY FINDINGS SUMMARY")
print("=" * 60)

top_batter = top_batters.iloc[0]
top_bowler = top_bowlers.iloc[0]
best_team = team_perf.iloc[0]
highest_avg_venue = venue_analysis.iloc[0]

print(f"""
1. Dataset: {len(matches)} matches, {len(deliveries):,} deliveries across 11 PSL seasons
2. Top run scorer: {top_batter.batter} ({int(top_batter.runs)} runs, SR {top_batter.sr})
3. Top wicket taker: {top_bowler.bowler} ({int(top_bowler.wickets)} wickets, Econ {top_bowler.economy})
4. Best win%: {best_team.team} ({best_team.win_pct}%)
5. Highest avg score venue: {highest_avg_venue.venue} ({highest_avg_venue.avg_score:.0f})
6. Toss winner wins: {toss_overall:.1f}% of matches
7. Chasing wins: {chase_wins/total_decided*100:.1f}% overall
8. Death overs RPO: {phase_stats[phase_stats.phase=='death'].rpo.values[0]:.2f} (highest phase)
9. Powerplay dot%: {phase_stats[phase_stats.phase=='powerplay'].dot_pct.values[0]:.1f}%
""")

print("EDA Complete! ✅")
