"""
PSL Analytics — Pre-Match Predictor

Predict match winner BEFORE the match starts based on:
- Teams, venue, toss winner, toss decision
- Historical team strength, venue record, H2H record

Usage:
    from src.models.match_predictor import MatchPredictor
    mp = MatchPredictor()
    mp.train(matches_df)
    result = mp.predict("Lahore Qalandars", "Karachi Kings", "National Stadium, Karachi", "Lahore Qalandars", "field")
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.config import RANDOM_SEED


class MatchPredictor:
    """Pre-match winner prediction using historical team/venue/toss data."""

    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.1,
            random_state=RANDOM_SEED,
        )
        self.team_encoder = LabelEncoder()
        self.venue_encoder = LabelEncoder()
        self.trained = False
        self.metrics = {}
        self.team_strength = {}
        self.venue_advantage = {}

    def _compute_team_strength(self, matches: pd.DataFrame) -> dict:
        """Rolling win percentage per team (proxy for strength)."""
        strength = {}
        for team in set(matches.team1) | set(matches.team2):
            team_matches = matches[(matches.team1 == team) | (matches.team2 == team)]
            wins = len(team_matches[team_matches.winner == team])
            total = len(team_matches)
            strength[team] = wins / total if total > 0 else 0.5
        return strength

    def _compute_venue_chase_pct(self, matches: pd.DataFrame) -> dict:
        """Chasing win % per venue."""
        venue_stats = {}
        decided = matches[matches.winner.notna()]
        for venue in decided.venue.unique():
            v_matches = decided[decided.venue == venue]
            chase_wins = v_matches.win_by_wickets.notna().sum()
            total = len(v_matches)
            venue_stats[venue] = chase_wins / total if total > 0 else 0.5
        return venue_stats

    def _prepare_features(self, matches: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Build feature matrix from match data."""
        df = matches.copy()
        df = df[df.winner.notna()].copy()

        # Team strength
        self.team_strength = self._compute_team_strength(df)
        self.venue_advantage = self._compute_venue_chase_pct(df)

        df["team1_strength"] = df["team1"].map(self.team_strength).fillna(0.5)
        df["team2_strength"] = df["team2"].map(self.team_strength).fillna(0.5)
        df["strength_diff"] = df["team1_strength"] - df["team2_strength"]

        df["venue_chase_pct"] = df["venue"].map(self.venue_advantage).fillna(0.5)

        # Toss features
        df["toss_winner_is_team1"] = (df["toss_winner"] == df["team1"]).astype(int)
        df["chose_field"] = (df["toss_decision"] == "field").astype(int)

        # Encode
        if fit:
            df["team1_enc"] = self.team_encoder.fit_transform(df["team1"].astype(str))
            df["venue_enc"] = self.venue_encoder.fit_transform(df["venue"].astype(str))
        else:
            df["team1_enc"] = df["team1"].astype(str).map(
                dict(zip(self.team_encoder.classes_, self.team_encoder.transform(self.team_encoder.classes_)))
            ).fillna(-1).astype(int)
            df["venue_enc"] = df["venue"].astype(str).map(
                dict(zip(self.venue_encoder.classes_, self.venue_encoder.transform(self.venue_encoder.classes_)))
            ).fillna(-1).astype(int)

        # Target: team1 wins
        df["team1_won"] = (df["winner"] == df["team1"]).astype(int)

        features = ["team1_strength", "team2_strength", "strength_diff",
                     "venue_chase_pct", "toss_winner_is_team1", "chose_field",
                     "team1_enc", "venue_enc"]

        return df, features

    def train(self, matches: pd.DataFrame) -> dict:
        """Train the match predictor with chronological split."""
        df, features = self._prepare_features(matches, fit=True)
        df = df.sort_values("date").reset_index(drop=True)

        X = df[features]
        y = df["team1_won"]

        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]

        self.metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
            "train_size": len(X_train),
            "test_size": len(X_test),
        }
        self.trained = True
        return self.metrics

    def predict(self, team1: str, team2: str, venue: str,
                toss_winner: str, toss_decision: str) -> dict:
        """Predict match outcome before the match."""
        if not self.trained:
            raise RuntimeError("Model not trained.")

        t1_str = self.team_strength.get(team1, 0.5)
        t2_str = self.team_strength.get(team2, 0.5)
        v_chase = self.venue_advantage.get(venue, 0.5)

        t1_enc_map = dict(zip(self.team_encoder.classes_, self.team_encoder.transform(self.team_encoder.classes_)))
        v_enc_map = dict(zip(self.venue_encoder.classes_, self.venue_encoder.transform(self.venue_encoder.classes_)))

        features = pd.DataFrame([{
            "team1_strength": t1_str,
            "team2_strength": t2_str,
            "strength_diff": t1_str - t2_str,
            "venue_chase_pct": v_chase,
            "toss_winner_is_team1": 1 if toss_winner == team1 else 0,
            "chose_field": 1 if toss_decision == "field" else 0,
            "team1_enc": t1_enc_map.get(team1, -1),
            "venue_enc": v_enc_map.get(venue, -1),
        }])

        proba = self.model.predict_proba(features)[0]
        team1_win_pct = round(proba[1] * 100, 1)
        team2_win_pct = round(proba[0] * 100, 1)
        predicted_winner = team1 if proba[1] > 0.5 else team2

        factors = []
        if t1_str > t2_str:
            factors.append(f"+ {team1} has stronger historical record ({t1_str:.0%} win rate)")
        else:
            factors.append(f"+ {team2} has stronger historical record ({t2_str:.0%} win rate)")

        if toss_decision == "field" and v_chase > 0.55:
            factors.append(f"+ Chasing favored at this venue ({v_chase:.0%} chase win rate)")
        elif toss_decision == "bat" and v_chase < 0.45:
            factors.append(f"+ Defending favored at this venue ({1-v_chase:.0%} defend win rate)")

        if toss_winner == predicted_winner:
            factors.append(f"+ Toss won by predicted winner")

        return {
            "team1": team1,
            "team2": team2,
            "team1_win_pct": team1_win_pct,
            "team2_win_pct": team2_win_pct,
            "predicted_winner": predicted_winner,
            "confidence": max(team1_win_pct, team2_win_pct),
            "factors": factors,
        }
