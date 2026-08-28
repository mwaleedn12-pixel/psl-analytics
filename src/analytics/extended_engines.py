"""
PSL Analytics — Extended Analytics Engines

Quick Wins:
    - Season Rankings (top scorers, wicket-takers per season)
    - Venue-specific H2H Records
    - Powerplay Aggression Index
    - Death Over Specialist Rankings

Advanced:
    - Player Value Index (consistency metric)
    - Pressure Performance (close-match stats)
    - Clutch Players (high required RR performance)
    - Season Improvement Tracker

Usage:
    from src.analytics.extended_engines import (
        SeasonRankings, PowerplayIndex, DeathSpecialists,
        PlayerValueIndex, PressurePerformance, ClutchAnalysis,
        SeasonImprovement,
    )
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ════════════════════════════════════════════════════════════
# QUICK WIN 1: SEASON RANKINGS
# ════════════════════════════════════════════════════════════

class SeasonRankings:
    """Top performers per season."""

    @staticmethod
    def top_run_scorers(deliveries: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """Top run scorers per PSL season."""
        legal = deliveries[deliveries["is_legal"] == 1]
        stats = legal.groupby(["psl_edition", "season_year", "batter"]).agg(
            innings=("match_id", "nunique"),
            runs=("batter_runs", "sum"),
            balls=("batter_runs", "count"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
        ).reset_index()

        stats["sr"] = (stats["runs"] / stats["balls"] * 100).round(1)
        stats["avg"] = (stats["runs"] / stats["innings"]).round(1)

        # Rank within each season
        stats["rank"] = stats.groupby("psl_edition")["runs"].rank(
            ascending=False, method="min"
        ).astype(int)

        return (
            stats[stats["rank"] <= top_n]
            .sort_values(["season_year", "rank"])
            .reset_index(drop=True)
        )

    @staticmethod
    def top_wicket_takers(deliveries: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """Top wicket takers per PSL season."""
        stats = deliveries.groupby(["psl_edition", "season_year", "bowler"]).agg(
            innings=("match_id", "nunique"),
            legal_balls=("is_legal", "sum"),
            runs_conceded=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
        ).reset_index()

        stats["overs"] = stats["legal_balls"] / 6
        stats["economy"] = np.where(
            stats["overs"] > 0, (stats["runs_conceded"] / stats["overs"]).round(2), 0
        )

        stats["rank"] = stats.groupby("psl_edition")["wickets"].rank(
            ascending=False, method="min"
        ).astype(int)

        return (
            stats[stats["rank"] <= top_n]
            .sort_values(["season_year", "rank"])
            .reset_index(drop=True)
        )


# ════════════════════════════════════════════════════════════
# QUICK WIN 2: POWERPLAY AGGRESSION INDEX
# ════════════════════════════════════════════════════════════

class PowerplayIndex:
    """Measure opener aggression in powerplay overs (1-6)."""

    @staticmethod
    def compute(deliveries: pd.DataFrame, min_innings: int = 5) -> pd.DataFrame:
        """
        Powerplay Aggression Index per batter.

        Index = (SR * 0.4) + (Boundary% * 0.3) + ((100 - Dot%) * 0.3)
        Normalized to 0-100 scale.
        """
        pp = deliveries[(deliveries["phase"] == "powerplay") & (deliveries["is_legal"] == 1)]

        stats = pp.groupby("batter").agg(
            innings=("match_id", "nunique"),
            runs=("batter_runs", "sum"),
            balls=("batter_runs", "count"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            dots=("is_dot", "sum"),
        ).reset_index()

        stats = stats[stats["innings"] >= min_innings].copy()
        stats["sr"] = stats["runs"] / stats["balls"] * 100
        stats["boundary_pct"] = (stats["fours"] + stats["sixes"]) / stats["balls"] * 100
        stats["dot_pct"] = stats["dots"] / stats["balls"] * 100

        # Normalize components to 0-100
        sr_norm = np.clip(stats["sr"] / 200 * 100, 0, 100)
        bnd_norm = np.clip(stats["boundary_pct"] / 30 * 100, 0, 100)
        dot_inv = np.clip((100 - stats["dot_pct"]) / 100 * 100, 0, 100)

        stats["aggression_index"] = (
            sr_norm * 0.4 + bnd_norm * 0.3 + dot_inv * 0.3
        ).round(1)

        return (
            stats[["batter", "innings", "runs", "sr", "boundary_pct", "dot_pct", "aggression_index"]]
            .sort_values("aggression_index", ascending=False)
            .reset_index(drop=True)
        )


# ════════════════════════════════════════════════════════════
# QUICK WIN 3: DEATH OVER SPECIALISTS
# ════════════════════════════════════════════════════════════

class DeathSpecialists:
    """Rank best finishers (batters) and death bowlers (overs 16-20)."""

    @staticmethod
    def best_finishers(deliveries: pd.DataFrame, min_innings: int = 5) -> pd.DataFrame:
        """Top death-overs batters by SR and boundary%."""
        death = deliveries[(deliveries["phase"] == "death") & (deliveries["is_legal"] == 1)]

        stats = death.groupby("batter").agg(
            innings=("match_id", "nunique"),
            runs=("batter_runs", "sum"),
            balls=("batter_runs", "count"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            dots=("is_dot", "sum"),
        ).reset_index()

        stats = stats[stats["innings"] >= min_innings].copy()
        stats["sr"] = (stats["runs"] / stats["balls"] * 100).round(1)
        stats["boundary_pct"] = (
            (stats["fours"] + stats["sixes"]) / stats["balls"] * 100
        ).round(1)
        stats["avg"] = (stats["runs"] / stats["innings"]).round(1)

        # Finisher score: SR weighted heavily
        stats["finisher_score"] = (
            np.clip(stats["sr"] / 200, 0, 1) * 50
            + np.clip(stats["boundary_pct"] / 30, 0, 1) * 30
            + np.clip(stats["avg"] / 30, 0, 1) * 20
        ).round(1)

        return stats.sort_values("finisher_score", ascending=False).reset_index(drop=True)

    @staticmethod
    def best_death_bowlers(deliveries: pd.DataFrame, min_innings: int = 5) -> pd.DataFrame:
        """Top death-overs bowlers by economy and dot%."""
        death = deliveries[deliveries["phase"] == "death"]

        stats = death.groupby("bowler").agg(
            innings=("match_id", "nunique"),
            legal_balls=("is_legal", "sum"),
            runs_conceded=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
            dots=("is_dot", "sum"),
        ).reset_index()

        stats = stats[stats["innings"] >= min_innings].copy()
        stats["overs"] = stats["legal_balls"] / 6
        stats["economy"] = np.where(
            stats["overs"] > 0, (stats["runs_conceded"] / stats["overs"]).round(2), 0
        )
        stats["dot_pct"] = (stats["dots"] / stats["legal_balls"] * 100).round(1)

        # Death bowling score: low economy + high dots + wickets
        stats["death_score"] = (
            np.clip(1 - stats["economy"] / 15, 0, 1) * 40
            + np.clip(stats["dot_pct"] / 50, 0, 1) * 30
            + np.clip(stats["wickets"] / stats["innings"] / 1.5, 0, 1) * 30
        ).round(1) * 100

        return stats.sort_values("death_score", ascending=False).reset_index(drop=True)


# ════════════════════════════════════════════════════════════
# ADVANCED 1: PLAYER VALUE INDEX
# ════════════════════════════════════════════════════════════

class PlayerValueIndex:
    """
    Consistency metric: high impact + low variance = valuable player.

    Value Index = avg_impact * (1 - cv_impact)
    where cv = std / mean (coefficient of variation)
    """

    @staticmethod
    def compute(impact_scores: pd.DataFrame, min_matches: int = 10) -> pd.DataFrame:
        """Compute Player Value Index from match-level impact scores."""
        stats = impact_scores.groupby("player").agg(
            matches=("match_id", "nunique"),
            avg_impact=("impact_score", "mean"),
            std_impact=("impact_score", "std"),
            max_impact=("impact_score", "max"),
            min_impact=("impact_score", "min"),
            median_impact=("impact_score", "median"),
        ).reset_index()

        stats = stats[stats["matches"] >= min_matches].copy()
        stats["std_impact"] = stats["std_impact"].fillna(0)

        # Coefficient of variation (lower = more consistent)
        stats["cv"] = np.where(
            stats["avg_impact"] > 0,
            stats["std_impact"] / stats["avg_impact"],
            1,
        )
        stats["consistency"] = np.clip(1 - stats["cv"], 0, 1).round(3)

        # Value Index
        stats["value_index"] = (stats["avg_impact"] * stats["consistency"]).round(2)

        for col in ["avg_impact", "std_impact", "max_impact", "min_impact", "median_impact"]:
            stats[col] = stats[col].round(2)

        return stats.sort_values("value_index", ascending=False).reset_index(drop=True)


# ════════════════════════════════════════════════════════════
# ADVANCED 2: PRESSURE PERFORMANCE
# ════════════════════════════════════════════════════════════

class PressurePerformance:
    """How players perform in close/high-pressure matches."""

    @staticmethod
    def batting_under_pressure(
        deliveries: pd.DataFrame,
        matches: pd.DataFrame,
        min_innings: int = 5,
        margin_threshold: int = 15,
    ) -> pd.DataFrame:
        """
        Batting stats in close matches only.

        Close match = won by ≤15 runs or ≤3 wickets.
        """
        # Identify close matches
        close = matches[
            (matches["winner"].notna())
            & (
                ((matches["win_by_runs"].notna()) & (matches["win_by_runs"] <= margin_threshold))
                | ((matches["win_by_wickets"].notna()) & (matches["win_by_wickets"] <= 3))
            )
        ]["match_id"].astype(str).values

        close_del = deliveries[deliveries["match_id"].astype(str).isin(close)]
        legal = close_del[close_del["is_legal"] == 1]

        stats = legal.groupby("batter").agg(
            pressure_innings=("match_id", "nunique"),
            pressure_runs=("batter_runs", "sum"),
            pressure_balls=("batter_runs", "count"),
            pressure_fours=("is_four", "sum"),
            pressure_sixes=("is_six", "sum"),
        ).reset_index()

        stats = stats[stats["pressure_innings"] >= min_innings].copy()
        stats["pressure_sr"] = (stats["pressure_runs"] / stats["pressure_balls"] * 100).round(1)
        stats["pressure_avg"] = (stats["pressure_runs"] / stats["pressure_innings"]).round(1)

        return stats.sort_values("pressure_runs", ascending=False).reset_index(drop=True)


# ════════════════════════════════════════════════════════════
# ADVANCED 3: CLUTCH ANALYSIS
# ════════════════════════════════════════════════════════════

class ClutchAnalysis:
    """Identify players who perform best when required RR is high."""

    @staticmethod
    def clutch_batters(
        deliveries: pd.DataFrame,
        rr_threshold: float = 10.0,
        min_balls: int = 30,
    ) -> pd.DataFrame:
        """
        Batting stats when required RR > threshold (high pressure chases).
        """
        from src.features.match_features import add_match_state_features

        df = deliveries.copy()
        if "required_rr" not in df.columns:
            df = add_match_state_features(df)

        high_pressure = df[
            (df["innings"] == 2)
            & (df["required_rr"] > rr_threshold)
            & (df["is_legal"] == 1)
        ]

        stats = high_pressure.groupby("batter").agg(
            clutch_innings=("match_id", "nunique"),
            clutch_balls=("batter_runs", "count"),
            clutch_runs=("batter_runs", "sum"),
            clutch_fours=("is_four", "sum"),
            clutch_sixes=("is_six", "sum"),
        ).reset_index()

        stats = stats[stats["clutch_balls"] >= min_balls].copy()
        stats["clutch_sr"] = (stats["clutch_runs"] / stats["clutch_balls"] * 100).round(1)
        stats["clutch_boundary_pct"] = (
            (stats["clutch_fours"] + stats["clutch_sixes"]) / stats["clutch_balls"] * 100
        ).round(1)

        return stats.sort_values("clutch_sr", ascending=False).reset_index(drop=True)

    @staticmethod
    def clutch_bowlers(
        deliveries: pd.DataFrame,
        rr_threshold: float = 10.0,
        min_balls: int = 30,
    ) -> pd.DataFrame:
        """Bowling stats when batting team's required RR > threshold (defending pressure)."""
        from src.features.match_features import add_match_state_features

        df = deliveries.copy()
        if "required_rr" not in df.columns:
            df = add_match_state_features(df)

        high_pressure = df[
            (df["innings"] == 2)
            & (df["required_rr"] > rr_threshold)
        ]

        stats = high_pressure.groupby("bowler").agg(
            clutch_innings=("match_id", "nunique"),
            clutch_legal=("is_legal", "sum"),
            clutch_runs=("total_runs", "sum"),
            clutch_wickets=("is_wicket", "sum"),
            clutch_dots=("is_dot", "sum"),
        ).reset_index()

        stats = stats[stats["clutch_legal"] >= min_balls].copy()
        stats["clutch_overs"] = stats["clutch_legal"] / 6
        stats["clutch_economy"] = np.where(
            stats["clutch_overs"] > 0,
            (stats["clutch_runs"] / stats["clutch_overs"]).round(2), 0
        )
        stats["clutch_dot_pct"] = (
            stats["clutch_dots"] / stats["clutch_legal"] * 100
        ).round(1)

        return stats.sort_values("clutch_wickets", ascending=False).reset_index(drop=True)


# ════════════════════════════════════════════════════════════
# ADVANCED 4: SEASON IMPROVEMENT TRACKER
# ════════════════════════════════════════════════════════════

class SeasonImprovement:
    """Track player improvement or decline across seasons."""

    @staticmethod
    def batting_trend(deliveries: pd.DataFrame, min_seasons: int = 3) -> pd.DataFrame:
        """
        Season-by-season batting progression.

        Computes trend direction (improving/declining/stable)
        based on linear regression slope of SR across seasons.
        """
        legal = deliveries[deliveries["is_legal"] == 1]

        season_stats = legal.groupby(["batter", "psl_edition", "season_year"]).agg(
            innings=("match_id", "nunique"),
            runs=("batter_runs", "sum"),
            balls=("batter_runs", "count"),
        ).reset_index()

        season_stats["sr"] = (season_stats["runs"] / season_stats["balls"] * 100).round(1)
        season_stats["avg"] = (season_stats["runs"] / season_stats["innings"]).round(1)

        # Filter players with enough seasons
        season_counts = season_stats.groupby("batter")["psl_edition"].nunique()
        qualified = season_counts[season_counts >= min_seasons].index
        season_stats = season_stats[season_stats["batter"].isin(qualified)].copy()

        # Compute trend per player
        trends = []
        for batter in qualified:
            player_data = season_stats[season_stats["batter"] == batter].sort_values("season_year")
            if len(player_data) < min_seasons:
                continue

            # Simple linear regression on SR
            x = np.arange(len(player_data))
            y = player_data["sr"].values
            slope = np.polyfit(x, y, 1)[0]

            recent_sr = player_data.iloc[-1]["sr"]
            career_sr = (player_data["runs"].sum() / player_data["balls"].sum() * 100)

            trends.append({
                "batter": batter,
                "seasons": len(player_data),
                "career_sr": round(career_sr, 1),
                "recent_sr": recent_sr,
                "sr_trend_slope": round(slope, 2),
                "trend": "Improving" if slope > 2 else ("Declining" if slope < -2 else "Stable"),
                "total_runs": player_data["runs"].sum(),
            })

        return pd.DataFrame(trends).sort_values("sr_trend_slope", ascending=False).reset_index(drop=True)
