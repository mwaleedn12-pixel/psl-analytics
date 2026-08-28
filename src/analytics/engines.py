"""
PSL Analytics — Advanced Analytics Engines

Modules:
    - FormEngine:    Player form (rolling averages)
    - VenueEngine:   Venue profiles & trends
    - MatchupEngine: Batter vs Bowler, Team vs Team
    - TeamEngine:    Team strengths
    - TossEngine:    Toss analysis
    - PhaseEngine:   Phase-level analytics

Usage:
    from src.analytics.engines import FormEngine, VenueEngine, ...
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FORM_WINDOW_SHORT, FORM_WINDOW_LONG


# ════════════════════════════════════════════════════════════
# FORM ENGINE
# ════════════════════════════════════════════════════════════

class FormEngine:
    """Track player form using recent match performance."""

    @staticmethod
    def batting_form(
        deliveries: pd.DataFrame,
        window: int = FORM_WINDOW_SHORT,
    ) -> pd.DataFrame:
        """
        Rolling batting stats over last N matches per player.
        Chronological order — no future data used.
        """
        legal = deliveries[deliveries["is_legal"] == 1].copy()
        legal["date"] = pd.to_datetime(legal["date"])

        per_match = legal.groupby(["batter", "match_id", "date"]).agg(
            runs=("batter_runs", "sum"),
            balls=("batter_runs", "count"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
        ).reset_index().sort_values(["batter", "date"])

        per_match["sr"] = np.where(per_match["balls"] > 0, per_match["runs"] / per_match["balls"] * 100, 0)

        # Rolling averages (chronological, no future leak)
        per_match["rolling_avg"] = (
            per_match.groupby("batter")["runs"]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
            .round(2)
        )
        per_match["rolling_sr"] = (
            per_match.groupby("batter")["sr"]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
            .round(2)
        )
        per_match["match_number"] = per_match.groupby("batter").cumcount() + 1

        return per_match

    @staticmethod
    def bowling_form(
        deliveries: pd.DataFrame,
        window: int = FORM_WINDOW_SHORT,
    ) -> pd.DataFrame:
        """Rolling bowling stats over last N matches per player."""
        deliveries["date"] = pd.to_datetime(deliveries["date"])

        per_match = deliveries.groupby(["bowler", "match_id", "date"]).agg(
            legal_balls=("is_legal", "sum"),
            runs_conceded=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
            dots=("is_dot", "sum"),
        ).reset_index().sort_values(["bowler", "date"])

        per_match["overs"] = per_match["legal_balls"] / 6
        per_match["economy"] = np.where(
            per_match["overs"] > 0, per_match["runs_conceded"] / per_match["overs"], 0
        )

        per_match["rolling_wickets"] = (
            per_match.groupby("bowler")["wickets"]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
            .round(2)
        )
        per_match["rolling_economy"] = (
            per_match.groupby("bowler")["economy"]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
            .round(2)
        )
        per_match["match_number"] = per_match.groupby("bowler").cumcount() + 1

        return per_match


# ════════════════════════════════════════════════════════════
# VENUE ENGINE
# ════════════════════════════════════════════════════════════

class VenueEngine:
    """Venue profiles and trends."""

    @staticmethod
    def venue_profile(deliveries: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
        """Compute per-venue statistics."""
        innings = deliveries.groupby(["match_id", "innings", "venue"]).agg(
            total_runs=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            legal_balls=("is_legal", "sum"),
        ).reset_index()

        venue = innings.groupby("venue").agg(
            innings_count=("match_id", "count"),
            matches=("match_id", "nunique"),
            avg_score=("total_runs", "mean"),
            avg_wickets=("wickets", "mean"),
            total_fours=("fours", "sum"),
            total_sixes=("sixes", "sum"),
            total_balls=("legal_balls", "sum"),
        ).reset_index()

        venue["avg_score"] = venue["avg_score"].round(1)
        venue["avg_wickets"] = venue["avg_wickets"].round(1)
        venue["boundary_pct"] = (
            (venue["total_fours"] + venue["total_sixes"]) / venue["total_balls"] * 100
        ).round(1)
        venue["six_pct"] = (venue["total_sixes"] / venue["total_balls"] * 100).round(2)

        # Chasing win %
        decided = matches[matches["winner"].notna()].copy()
        decided["chase_won"] = (decided["win_by_wickets"].notna()).astype(int)
        chase_by_venue = decided.groupby("venue").agg(
            decided_matches=("match_id", "count"),
            chase_wins=("chase_won", "sum"),
        ).reset_index()
        chase_by_venue["chase_win_pct"] = (
            chase_by_venue["chase_wins"] / chase_by_venue["decided_matches"] * 100
        ).round(1)

        venue = venue.merge(chase_by_venue[["venue", "chase_win_pct"]], on="venue", how="left")

        # Innings 1 vs 2 avg
        inn1_avg = innings[innings["innings"] == 1].groupby("venue")["total_runs"].mean().round(1)
        inn2_avg = innings[innings["innings"] == 2].groupby("venue")["total_runs"].mean().round(1)
        venue = venue.merge(inn1_avg.rename("avg_1st_innings"), on="venue", how="left")
        venue = venue.merge(inn2_avg.rename("avg_2nd_innings"), on="venue", how="left")

        return venue.sort_values("avg_score", ascending=False).reset_index(drop=True)


# ════════════════════════════════════════════════════════════
# MATCHUP ENGINE
# ════════════════════════════════════════════════════════════

class MatchupEngine:
    """Batter vs Bowler and Team vs Team matchups."""

    @staticmethod
    def batter_vs_bowler(deliveries: pd.DataFrame, min_balls: int = 6) -> pd.DataFrame:
        """Head-to-head batter vs bowler stats."""
        legal = deliveries[deliveries["is_legal"] == 1].copy()

        matchup = legal.groupby(["batter", "bowler"]).agg(
            balls=("batter_runs", "count"),
            runs=("batter_runs", "sum"),
            dots=("is_dot", "sum"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            dismissals=("is_wicket", "sum"),
        ).reset_index()

        matchup["sr"] = (matchup["runs"] / matchup["balls"] * 100).round(1)
        matchup["dot_pct"] = (matchup["dots"] / matchup["balls"] * 100).round(1)

        if min_balls > 0:
            matchup = matchup[matchup["balls"] >= min_balls]

        return matchup.sort_values("balls", ascending=False).reset_index(drop=True)

    @staticmethod
    def team_vs_team(matches: pd.DataFrame) -> pd.DataFrame:
        """Head-to-head team records."""
        decided = matches[matches["winner"].notna()].copy()
        records = []

        teams = sorted(set(decided["team1"].unique()) | set(decided["team2"].unique()))
        for i, t1 in enumerate(teams):
            for t2 in teams[i + 1:]:
                mask = (
                    ((decided["team1"] == t1) & (decided["team2"] == t2))
                    | ((decided["team1"] == t2) & (decided["team2"] == t1))
                )
                subset = decided[mask]
                if len(subset) == 0:
                    continue

                t1_wins = len(subset[subset["winner"] == t1])
                t2_wins = len(subset[subset["winner"] == t2])

                records.append({
                    "team1": t1,
                    "team2": t2,
                    "matches": len(subset),
                    "team1_wins": t1_wins,
                    "team2_wins": t2_wins,
                    "team1_win_pct": round(t1_wins / len(subset) * 100, 1),
                })

        return pd.DataFrame(records).sort_values("matches", ascending=False).reset_index(drop=True)


# ════════════════════════════════════════════════════════════
# TEAM ENGINE
# ════════════════════════════════════════════════════════════

class TeamEngine:
    """Team strength metrics."""

    @staticmethod
    def team_batting_strength(deliveries: pd.DataFrame) -> pd.DataFrame:
        """Batting strength per team — overall and by phase."""
        innings = deliveries.groupby(["match_id", "innings", "batting_team"]).agg(
            runs=("total_runs", "sum"),
            legal_balls=("is_legal", "sum"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            wickets=("is_wicket", "sum"),
        ).reset_index()

        team = innings.groupby("batting_team").agg(
            innings_count=("match_id", "count"),
            avg_score=("runs", "mean"),
            avg_sr=("runs", lambda x: (x.sum() / innings.loc[x.index, "legal_balls"].sum() * 100)),
            avg_wickets_lost=("wickets", "mean"),
        ).reset_index()

        team["avg_score"] = team["avg_score"].round(1)
        team["avg_sr"] = team["avg_sr"].round(1)
        team["avg_wickets_lost"] = team["avg_wickets_lost"].round(1)

        # Phase-level
        for phase in ["powerplay", "middle", "death"]:
            phase_data = deliveries[deliveries["phase"] == phase]
            phase_inn = phase_data.groupby(["match_id", "innings", "batting_team"]).agg(
                runs=("total_runs", "sum"),
                legal_balls=("is_legal", "sum"),
            ).reset_index()
            phase_avg = phase_inn.groupby("batting_team")["runs"].mean().round(1)
            team = team.merge(
                phase_avg.rename(f"avg_{phase}_score"), on="batting_team", how="left"
            )

        return team.sort_values("avg_score", ascending=False).reset_index(drop=True)

    @staticmethod
    def team_bowling_strength(deliveries: pd.DataFrame) -> pd.DataFrame:
        """Bowling strength per team."""
        innings = deliveries.groupby(["match_id", "innings", "bowling_team"]).agg(
            runs_conceded=("total_runs", "sum"),
            legal_balls=("is_legal", "sum"),
            wickets=("is_wicket", "sum"),
            dots=("is_dot", "sum"),
        ).reset_index()

        team = innings.groupby("bowling_team").agg(
            innings_count=("match_id", "count"),
            avg_conceded=("runs_conceded", "mean"),
            avg_wickets=("wickets", "mean"),
            avg_dots=("dots", "mean"),
        ).reset_index()

        team["avg_conceded"] = team["avg_conceded"].round(1)
        team["avg_wickets"] = team["avg_wickets"].round(1)
        team["avg_dots"] = team["avg_dots"].round(1)

        return team.sort_values("avg_conceded").reset_index(drop=True)


# ════════════════════════════════════════════════════════════
# TOSS ENGINE
# ════════════════════════════════════════════════════════════

class TossEngine:
    """Toss analysis."""

    @staticmethod
    def toss_analysis(matches: pd.DataFrame) -> dict:
        """Overall and per-venue toss analysis."""
        decided = matches[matches["winner"].notna()].copy()
        decided["toss_winner_won"] = (decided["toss_winner"] == decided["winner"]).astype(int)

        overall = {
            "total_matches": len(decided),
            "toss_win_match_win_pct": round(decided["toss_winner_won"].mean() * 100, 1),
            "field_first_pct": round(
                (decided["toss_decision"] == "field").mean() * 100, 1
            ),
        }

        # By decision
        by_decision = decided.groupby("toss_decision").agg(
            matches=("match_id", "count"),
            wins=("toss_winner_won", "sum"),
        ).reset_index()
        by_decision["win_pct"] = (by_decision["wins"] / by_decision["matches"] * 100).round(1)

        # By venue
        by_venue = decided.groupby(["venue", "toss_decision"]).agg(
            matches=("match_id", "count"),
            wins=("toss_winner_won", "sum"),
        ).reset_index()
        by_venue["win_pct"] = (by_venue["wins"] / by_venue["matches"] * 100).round(1)

        return {
            "overall": overall,
            "by_decision": by_decision,
            "by_venue": by_venue,
        }


# ════════════════════════════════════════════════════════════
# PHASE ENGINE
# ════════════════════════════════════════════════════════════

class PhaseEngine:
    """Phase-level analytics (powerplay, middle, death)."""

    @staticmethod
    def phase_summary(deliveries: pd.DataFrame) -> pd.DataFrame:
        """Overall scoring patterns by phase."""
        phase = deliveries.groupby("phase").agg(
            legal_balls=("is_legal", "sum"),
            runs=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            dots=("is_dot", "sum"),
        ).reset_index()

        phase["rpo"] = (phase["runs"] / (phase["legal_balls"] / 6)).round(2)
        phase["sr"] = (phase["runs"] / phase["legal_balls"] * 100).round(1)
        phase["dot_pct"] = (phase["dots"] / phase["legal_balls"] * 100).round(1)
        phase["boundary_pct"] = (
            (phase["fours"] + phase["sixes"]) / phase["legal_balls"] * 100
        ).round(1)
        phase["wickets_per_over"] = (phase["wickets"] / (phase["legal_balls"] / 6)).round(2)

        order = {"powerplay": 0, "middle": 1, "death": 2}
        phase["order"] = phase["phase"].map(order)
        return phase.sort_values("order").drop(columns="order").reset_index(drop=True)

    @staticmethod
    def team_phase_performance(deliveries: pd.DataFrame) -> pd.DataFrame:
        """Batting performance per team per phase."""
        team_phase = deliveries.groupby(["batting_team", "phase"]).agg(
            innings=("match_id", "nunique"),
            runs=("total_runs", "sum"),
            legal_balls=("is_legal", "sum"),
            wickets=("is_wicket", "sum"),
        ).reset_index()

        team_phase["avg_runs"] = (team_phase["runs"] / team_phase["innings"]).round(1)
        team_phase["sr"] = (team_phase["runs"] / team_phase["legal_balls"] * 100).round(1)
        team_phase["avg_wickets"] = (team_phase["wickets"] / team_phase["innings"]).round(2)

        return team_phase
