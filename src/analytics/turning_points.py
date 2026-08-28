"""
PSL Analytics — Turning Point Engine

Detects match-changing moments by tracking win probability swings.

A turning point = a delivery/event that caused a large shift in
win probability (e.g. a key wicket dropping probability from 68% to 41%).

Usage:
    from src.analytics.turning_points import TurningPointEngine
    tp = TurningPointEngine(win_prob_model)
    points = tp.detect(deliveries_df, matches_df, match_id="1075986")
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TurningPointEngine:
    """
    Detect match turning points using win probability changes.

    For each delivery in innings 2:
        prob_before → event → prob_after → swing = prob_after - prob_before

    Turning points are the deliveries with the largest absolute swings.
    """

    def __init__(self, win_prob_model=None):
        """
        Args:
            win_prob_model: Trained WinProbabilityModel instance.
                           If None, must be set before calling detect().
        """
        self.model = win_prob_model

    def compute_probability_timeline(
        self,
        deliveries: pd.DataFrame,
        matches: pd.DataFrame,
        match_id: str | None = None,
    ) -> pd.DataFrame:
        """
        Compute ball-by-ball win probability for innings 2.

        Returns DataFrame with win_probability and probability_change columns.
        """
        if self.model is None or not self.model.trained:
            raise RuntimeError("Win probability model not trained.")

        preds = self.model.predict_proba(deliveries, matches)

        if match_id is not None:
            preds = preds[preds["match_id"].astype(str) == str(match_id)].copy()

        preds = preds.sort_values(["match_id", "innings", "over", "ball"]).reset_index(drop=True)

        # Probability change per delivery
        preds["prob_change"] = preds.groupby("match_id")["win_probability"].diff().fillna(0)
        preds["prob_change"] = preds["prob_change"].round(4)

        return preds

    def detect(
        self,
        deliveries: pd.DataFrame,
        matches: pd.DataFrame,
        match_id: str | None = None,
        top_n: int = 5,
        min_swing: float = 0.05,
    ) -> pd.DataFrame:
        """
        Detect top turning points in a match or across all matches.

        Args:
            deliveries: Cleaned deliveries DataFrame.
            matches: Cleaned matches DataFrame.
            match_id: If provided, analyze a single match.
            top_n: Number of top turning points to return per match.
            min_swing: Minimum absolute probability change to qualify.

        Returns:
            DataFrame of turning points with columns:
                match_id, over, ball, batter, bowler, event_type,
                prob_before, prob_after, swing, description
        """
        timeline = self.compute_probability_timeline(deliveries, matches, match_id)

        # Compute prob_before and prob_after
        timeline["prob_before"] = (
            timeline["win_probability"] - timeline["prob_change"]
        ).round(4)
        timeline["prob_after"] = timeline["win_probability"]
        timeline["abs_swing"] = timeline["prob_change"].abs()

        # Event type
        timeline["event_type"] = "dot/run"
        timeline.loc[timeline["is_wicket"] == 1, "event_type"] = "wicket"
        timeline.loc[timeline["is_six"] == 1, "event_type"] = "six"
        timeline.loc[timeline["is_four"] == 1, "event_type"] = "four"

        # Filter by minimum swing
        turning = timeline[timeline["abs_swing"] >= min_swing].copy()

        # Top N per match
        if match_id is not None:
            turning = turning.nlargest(top_n, "abs_swing")
        else:
            turning = (
                turning.groupby("match_id", group_keys=False)
                .apply(lambda x: x.nlargest(top_n, "abs_swing"))
                .reset_index(drop=True)
            )

        # Build description
        turning["description"] = turning.apply(self._describe_turning_point, axis=1)

        cols = [
            "match_id", "over", "ball", "batter", "bowler",
            "event_type", "prob_before", "prob_after", "prob_change",
            "abs_swing", "batting_team", "bowling_team", "description",
        ]
        available_cols = [c for c in cols if c in turning.columns]

        return turning[available_cols].sort_values(
            ["match_id", "abs_swing"], ascending=[True, False]
        ).reset_index(drop=True)

    @staticmethod
    def _describe_turning_point(row) -> str:
        """Generate a human-readable description of a turning point."""
        # Cricket notation: overs_completed.ball (e.g. 19.4 = 20th over, 4th ball)
        over_ball = f"{row['over'] - 1}.{row['ball']}"
        direction = "↑" if row["prob_change"] > 0 else "↓"
        pct_before = f"{row['prob_before'] * 100:.1f}%"
        pct_after = f"{row['prob_after'] * 100:.1f}%"
        swing_pct = f"{row['abs_swing'] * 100:.1f}%"

        event = row["event_type"]
        if event == "wicket":
            desc = f"Over {over_ball}: WICKET — {row.get('player_out', row['batter'])} out"
        elif event == "six":
            desc = f"Over {over_ball}: SIX by {row['batter']}"
        elif event == "four":
            desc = f"Over {over_ball}: FOUR by {row['batter']}"
        else:
            desc = f"Over {over_ball}: {row['batter']} vs {row['bowler']}"

        desc += f" | {pct_before} {direction} {pct_after} (swing: {swing_pct})"
        return desc

    def match_summary(
        self,
        deliveries: pd.DataFrame,
        matches: pd.DataFrame,
        match_id: str,
    ) -> dict:
        """
        Full turning point summary for a single match.

        Returns:
            dict with timeline, turning_points, and match_info.
        """
        timeline = self.compute_probability_timeline(deliveries, matches, match_id)
        turning = self.detect(deliveries, matches, match_id)

        match_row = matches[matches["match_id"].astype(str) == str(match_id)]
        match_info = {}
        if not match_row.empty:
            row = match_row.iloc[0]
            match_info = {
                "match_id": str(match_id),
                "date": str(row.get("date", "")),
                "venue": row.get("venue", ""),
                "team1": row.get("team1", ""),
                "team2": row.get("team2", ""),
                "winner": row.get("winner", ""),
            }

        return {
            "match_info": match_info,
            "timeline": timeline,
            "turning_points": turning,
            "biggest_swing": turning.iloc[0].to_dict() if len(turning) > 0 else None,
        }
