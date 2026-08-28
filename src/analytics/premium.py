"""
PSL Analytics — Premium Features

1. Optimal Playing XI — suggest best team based on venue + opponent
2. Season Awards — automatic best batter/bowler/allrounder per season
3. Player Comparison — side-by-side radar comparison

Usage:
    from src.analytics.premium import OptimalXI, SeasonAwards, PlayerComparison
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class OptimalXI:
    """Suggest best playing XI for a team based on venue and opponent."""

    @staticmethod
    def suggest(
        deliveries: pd.DataFrame,
        team: str,
        venue: str | None = None,
        opponent: str | None = None,
        top_batters: int = 6,
        top_bowlers: int = 5,
    ) -> dict:
        """
        Suggest optimal XI based on recent performance.

        Returns dict with suggested_batters, suggested_bowlers, and reasoning.
        """
        team_del = deliveries[deliveries.batting_team == team].copy()
        legal = team_del[team_del.is_legal == 1]

        # Filter by venue if specified
        if venue:
            venue_del = legal[legal.venue == venue]
            if len(venue_del) > 100:
                legal = venue_del

        # Batting candidates
        bat_stats = legal.groupby("batter").agg(
            innings=("match_id", "nunique"),
            runs=("batter_runs", "sum"),
            balls=("batter_runs", "count"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
        ).reset_index()
        bat_stats = bat_stats[bat_stats.innings >= 3].copy()
        bat_stats["sr"] = (bat_stats.runs / bat_stats.balls * 100).round(1)
        bat_stats["avg"] = (bat_stats.runs / bat_stats.innings).round(1)
        # Score: weighted combination
        bat_stats["score"] = (
            bat_stats["avg"] * 0.4 + bat_stats["sr"] * 0.3
            + (bat_stats["fours"] + bat_stats["sixes"]) / bat_stats["innings"] * 10 * 0.3
        ).round(1)
        top_bats = bat_stats.nlargest(top_batters, "score")

        # Bowling candidates
        bowl_del = deliveries[deliveries.bowling_team != team].copy()
        if venue:
            venue_bowl = bowl_del[bowl_del.venue == venue]
            if len(venue_bowl) > 100:
                bowl_del = venue_bowl

        bowl_team_del = deliveries[deliveries.bowling_team == team]
        bowl_stats = bowl_team_del.groupby("bowler").agg(
            innings=("match_id", "nunique"),
            legal_balls=("is_legal", "sum"),
            runs_conceded=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
            dots=("is_dot", "sum"),
        ).reset_index()
        bowl_stats = bowl_stats[bowl_stats.innings >= 3].copy()
        bowl_stats["overs"] = bowl_stats.legal_balls / 6
        bowl_stats["economy"] = np.where(
            bowl_stats.overs > 0, (bowl_stats.runs_conceded / bowl_stats.overs).round(2), 99
        )
        bowl_stats["dot_pct"] = (bowl_stats.dots / bowl_stats.legal_balls * 100).round(1)
        # Score: wickets + economy (inverted) + dots
        bowl_stats["score"] = (
            bowl_stats["wickets"] / bowl_stats["innings"] * 40
            + (1 - bowl_stats["economy"] / 12) * 30
            + bowl_stats["dot_pct"] / 100 * 30
        ).round(1)
        top_bowls = bowl_stats.nlargest(top_bowlers, "score")

        return {
            "team": team,
            "venue": venue,
            "opponent": opponent,
            "suggested_batters": top_bats[["batter", "innings", "runs", "avg", "sr", "score"]].to_dict("records"),
            "suggested_bowlers": top_bowls[["bowler", "innings", "wickets", "economy", "dot_pct", "score"]].to_dict("records"),
        }


class SeasonAwards:
    """Automatic season awards — best performers per PSL season."""

    @staticmethod
    def compute(deliveries: pd.DataFrame) -> pd.DataFrame:
        """Compute awards for each season."""
        legal = deliveries[deliveries.is_legal == 1]
        awards = []

        for edition in sorted(deliveries.psl_edition.unique()):
            season = deliveries[deliveries.psl_edition == edition]
            season_legal = legal[legal.psl_edition == edition]

            # Best Batter — most runs
            bat = season_legal.groupby("batter").agg(
                runs=("batter_runs", "sum"), balls=("batter_runs", "count"),
                innings=("match_id", "nunique"),
            ).reset_index()
            bat["sr"] = (bat.runs / bat.balls * 100).round(1)
            if len(bat) > 0:
                best_bat = bat.nlargest(1, "runs").iloc[0]
            else:
                continue

            # Best Bowler — most wickets
            bowl = season.groupby("bowler").agg(
                wickets=("is_wicket", "sum"),
                legal_balls=("is_legal", "sum"),
                runs_conceded=("total_runs", "sum"),
                innings=("match_id", "nunique"),
            ).reset_index()
            bowl["overs"] = bowl.legal_balls / 6
            bowl["economy"] = np.where(bowl.overs > 0, (bowl.runs_conceded / bowl.overs).round(2), 0)
            best_bowl = bowl.nlargest(1, "wickets").iloc[0] if len(bowl) > 0 else None

            # Best All-rounder — runs + wickets combined score
            all_rounders = bat.merge(bowl, left_on="batter", right_on="bowler", how="inner",
                                      suffixes=("_bat", "_bowl"))
            if len(all_rounders) > 0:
                all_rounders["ar_score"] = all_rounders["runs"] + all_rounders["wickets"] * 25
                best_ar = all_rounders.nlargest(1, "ar_score").iloc[0]
                ar_name = best_ar["batter"]
                ar_runs = int(best_ar["runs"])
                ar_wickets = int(best_ar["wickets"])
            else:
                ar_name, ar_runs, ar_wickets = "—", 0, 0

            # Most Sixes
            sixes = season_legal.groupby("batter")["is_six"].sum().reset_index()
            best_six = sixes.nlargest(1, "is_six").iloc[0] if len(sixes) > 0 else None

            awards.append({
                "season": edition,
                "best_batter": best_bat["batter"],
                "batter_runs": int(best_bat["runs"]),
                "batter_sr": best_bat["sr"],
                "best_bowler": best_bowl["bowler"] if best_bowl is not None else "—",
                "bowler_wickets": int(best_bowl["wickets"]) if best_bowl is not None else 0,
                "bowler_economy": best_bowl["economy"] if best_bowl is not None else 0,
                "best_allrounder": ar_name,
                "ar_runs": ar_runs,
                "ar_wickets": ar_wickets,
                "most_sixes_player": best_six["batter"] if best_six is not None else "—",
                "most_sixes": int(best_six["is_six"]) if best_six is not None else 0,
            })

        return pd.DataFrame(awards)


class PlayerComparison:
    """Side-by-side player comparison with radar data."""

    @staticmethod
    def compare_batters(
        deliveries: pd.DataFrame,
        player1: str,
        player2: str,
    ) -> dict:
        """Compare two batters across all dimensions."""
        legal = deliveries[deliveries.is_legal == 1]

        def _stats(name):
            p = legal[legal.batter == name]
            if len(p) == 0:
                return None
            runs = p.batter_runs.sum()
            balls = len(p)
            innings = p.match_id.nunique()
            fours = p.is_four.sum()
            sixes = p.is_six.sum()

            pp = p[p.phase == "powerplay"]
            mid = p[p.phase == "middle"]
            death = p[p.phase == "death"]

            return {
                "player": name,
                "innings": innings,
                "runs": int(runs),
                "balls": int(balls),
                "avg": round(runs / innings, 1) if innings > 0 else 0,
                "sr": round(runs / balls * 100, 1) if balls > 0 else 0,
                "fours": int(fours),
                "sixes": int(sixes),
                "boundary_pct": round((fours + sixes) / balls * 100, 1) if balls > 0 else 0,
                "dot_pct": round(p.is_dot.sum() / balls * 100, 1) if balls > 0 else 0,
                "sr_powerplay": round(pp.batter_runs.sum() / len(pp) * 100, 1) if len(pp) > 0 else 0,
                "sr_middle": round(mid.batter_runs.sum() / len(mid) * 100, 1) if len(mid) > 0 else 0,
                "sr_death": round(death.batter_runs.sum() / len(death) * 100, 1) if len(death) > 0 else 0,
            }

        s1 = _stats(player1)
        s2 = _stats(player2)

        return {"player1": s1, "player2": s2}

    @staticmethod
    def compare_bowlers(
        deliveries: pd.DataFrame,
        player1: str,
        player2: str,
    ) -> dict:
        """Compare two bowlers."""
        def _stats(name):
            p = deliveries[deliveries.bowler == name]
            if len(p) == 0:
                return None
            legal_balls = p.is_legal.sum()
            overs = legal_balls / 6
            return {
                "player": name,
                "innings": p.match_id.nunique(),
                "wickets": int(p.is_wicket.sum()),
                "runs_conceded": int(p.total_runs.sum()),
                "overs": round(overs, 1),
                "economy": round(p.total_runs.sum() / overs, 2) if overs > 0 else 0,
                "dot_pct": round(p.is_dot.sum() / legal_balls * 100, 1) if legal_balls > 0 else 0,
                "bowling_sr": round(legal_balls / p.is_wicket.sum(), 1) if p.is_wicket.sum() > 0 else 999,
            }

        return {"player1": _stats(player1), "player2": _stats(player2)}
