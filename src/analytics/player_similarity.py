"""
PSL Analytics — Player Similarity & Clustering

Find players with similar profiles and group players into archetypes.

Features used:
    Batting:  avg, sr, boundary_pct, dot_pct, sr_powerplay, sr_middle, sr_death
    Bowling:  economy, bowling_sr, dot_pct, economy_powerplay, economy_middle, economy_death

Methods:
    - Cosine similarity for player-to-player comparison
    - K-Means clustering for archetype detection

Possible archetypes:
    Anchor, Aggressor, Finisher, Powerplay Specialist,
    Death Bowler, Spinner, All-rounder

Usage:
    from src.analytics.player_similarity import PlayerSimilarityEngine
    engine = PlayerSimilarityEngine()
    engine.fit(batting_stats, bowling_stats)
    similar = engine.find_similar("Babar Azam", top_n=5)
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.config import RANDOM_SEED


class PlayerSimilarityEngine:
    """Find similar players and detect player archetypes."""

    BATTING_FEATURES = [
        "avg", "sr", "boundary_pct", "dot_pct",
        "sr_powerplay", "sr_middle", "sr_death",
    ]
    BOWLING_FEATURES = [
        "economy", "dot_pct", "bowling_sr",
        "economy_powerplay", "economy_middle", "economy_death",
    ]

    def __init__(self):
        self.scaler = StandardScaler()
        self.batting_matrix = None
        self.bowling_matrix = None
        self.batting_players = None
        self.bowling_players = None
        self.batting_scaled = None
        self.bowling_scaled = None
        self.batting_clusters = None
        self.bowling_clusters = None
        self.fitted = False

    def fit_batting(
        self,
        batting_stats: pd.DataFrame,
        min_innings: int = 10,
        n_clusters: int = 5,
    ) -> pd.DataFrame:
        """
        Fit batting similarity model.

        Args:
            batting_stats: Output of compute_batting_stats().
            min_innings: Minimum innings to include player.
            n_clusters: Number of archetype clusters.

        Returns:
            DataFrame with player, cluster, and archetype columns.
        """
        df = batting_stats[batting_stats["innings"] >= min_innings].copy()

        # Ensure all feature columns exist
        for col in self.BATTING_FEATURES:
            if col not in df.columns:
                df[col] = 0

        features = df[self.BATTING_FEATURES].fillna(0)
        self.batting_players = df["batter"].values
        self.batting_scaled = self.scaler.fit_transform(features)
        self.batting_matrix = cosine_similarity(self.batting_scaled)

        # Clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_SEED, n_init=10)
        df["cluster"] = kmeans.fit_predict(self.batting_scaled)
        self.batting_clusters = df

        # Label archetypes based on cluster centers
        df["archetype"] = df["cluster"].map(
            self._label_batting_archetypes(kmeans, features.columns)
        )

        self.fitted = True
        return df[["batter", "innings", "runs", "avg", "sr", "cluster", "archetype"]]

    def fit_bowling(
        self,
        bowling_stats: pd.DataFrame,
        min_innings: int = 10,
        n_clusters: int = 4,
    ) -> pd.DataFrame:
        """Fit bowling similarity model."""
        df = bowling_stats[bowling_stats["innings"] >= min_innings].copy()

        for col in self.BOWLING_FEATURES:
            if col not in df.columns:
                df[col] = 0

        # bowling_sr can be NaN for bowlers with 0 wickets
        df["bowling_sr"] = df["bowling_sr"].fillna(999)

        features = df[self.BOWLING_FEATURES].fillna(0)
        scaler = StandardScaler()
        self.bowling_players = df["bowler"].values
        self.bowling_scaled = scaler.fit_transform(features)
        self.bowling_matrix = cosine_similarity(self.bowling_scaled)

        kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_SEED, n_init=10)
        df["cluster"] = kmeans.fit_predict(self.bowling_scaled)
        self.bowling_clusters = df

        df["archetype"] = df["cluster"].map(
            self._label_bowling_archetypes(kmeans, features.columns)
        )

        return df[["bowler", "innings", "wickets", "economy", "cluster", "archetype"]]

    def find_similar_batters(self, player_name: str, top_n: int = 5) -> pd.DataFrame:
        """Find the most similar batters to a given player."""
        if self.batting_matrix is None:
            raise RuntimeError("Call fit_batting() first.")

        idx = np.where(self.batting_players == player_name)[0]
        if len(idx) == 0:
            raise ValueError(f"Player '{player_name}' not found.")

        idx = idx[0]
        similarities = self.batting_matrix[idx]
        top_indices = np.argsort(similarities)[::-1][1:top_n + 1]  # skip self

        results = []
        for i in top_indices:
            results.append({
                "player": self.batting_players[i],
                "similarity": round(similarities[i], 4),
            })

        return pd.DataFrame(results)

    def find_similar_bowlers(self, player_name: str, top_n: int = 5) -> pd.DataFrame:
        """Find the most similar bowlers to a given player."""
        if self.bowling_matrix is None:
            raise RuntimeError("Call fit_bowling() first.")

        idx = np.where(self.bowling_players == player_name)[0]
        if len(idx) == 0:
            raise ValueError(f"Player '{player_name}' not found.")

        idx = idx[0]
        similarities = self.bowling_matrix[idx]
        top_indices = np.argsort(similarities)[::-1][1:top_n + 1]

        results = []
        for i in top_indices:
            results.append({
                "player": self.bowling_players[i],
                "similarity": round(similarities[i], 4),
            })

        return pd.DataFrame(results)

    @staticmethod
    def _label_batting_archetypes(kmeans, feature_names) -> dict:
        """
        Assign archetype labels to clusters based on center characteristics.

        Rules:
            High SR + High boundary% → Aggressor
            High avg + Low SR → Anchor
            High death SR → Finisher
            High PP SR → Powerplay Specialist
            Balanced → All-rounder Batter
        """
        centers = pd.DataFrame(kmeans.cluster_centers_, columns=feature_names)
        labels = {}

        for i, row in centers.iterrows():
            if row.get("sr", 0) > centers["sr"].median() and row.get("boundary_pct", 0) > centers["boundary_pct"].median():
                if row.get("sr_death", 0) > centers["sr_death"].median():
                    labels[i] = "Aggressor-Finisher"
                else:
                    labels[i] = "Aggressor"
            elif row.get("avg", 0) > centers["avg"].median() and row.get("sr", 0) <= centers["sr"].median():
                labels[i] = "Anchor"
            elif row.get("sr_death", 0) > centers["sr_death"].quantile(0.75):
                labels[i] = "Finisher"
            elif row.get("sr_powerplay", 0) > centers["sr_powerplay"].quantile(0.75):
                labels[i] = "Powerplay Specialist"
            else:
                labels[i] = "Batting All-rounder"

        return labels

    @staticmethod
    def _label_bowling_archetypes(kmeans, feature_names) -> dict:
        """
        Assign archetype labels to bowling clusters.

        Rules:
            Low death economy → Death Specialist
            Low PP economy → Powerplay Bowler
            Low overall economy + high dot% → Economical
            Otherwise → Stock Bowler
        """
        centers = pd.DataFrame(kmeans.cluster_centers_, columns=feature_names)
        labels = {}

        for i, row in centers.iterrows():
            if row.get("economy_death", 0) < centers["economy_death"].median():
                labels[i] = "Death Specialist"
            elif row.get("economy_powerplay", 0) < centers["economy_powerplay"].median():
                labels[i] = "Powerplay Bowler"
            elif row.get("dot_pct", 0) > centers["dot_pct"].median():
                labels[i] = "Economical"
            else:
                labels[i] = "Stock Bowler"

        return labels
