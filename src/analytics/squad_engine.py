"""
PSL Analytics — Squad Engine

Extract team squads per season from match data.
Detect player roles (batter/bowler/allrounder/keeper) from performance data.
"""

import pandas as pd
import numpy as np


class SquadEngine:
    """Extract and analyze team squads."""

    @staticmethod
    def get_all_squads(deliveries: pd.DataFrame) -> pd.DataFrame:
        """Get all players who played for each team in each season."""
        batters = deliveries[["psl_edition", "season_year", "batting_team", "batter"]].rename(
            columns={"batter": "player", "batting_team": "team"})
        bowlers = deliveries[["psl_edition", "season_year", "bowling_team", "bowler"]].rename(
            columns={"bowler": "player", "bowling_team": "team"})

        all_p = pd.concat([batters, bowlers]).drop_duplicates()
        return all_p

    @staticmethod
    def get_team_squad(
        deliveries: pd.DataFrame,
        team: str,
        season: str = None,
    ) -> pd.DataFrame:
        """Get squad for a specific team with player stats and detected role."""
        legal = deliveries[deliveries.is_legal == 1]

        if season:
            d = deliveries[deliveries.psl_edition == season]
            l = legal[legal.psl_edition == season]
        else:
            d = deliveries
            l = legal

        # Players who batted for this team
        bat_players = l[l.batting_team == team].groupby("batter").agg(
            bat_inn=("match_id", "nunique"),
            runs=("batter_runs", "sum"),
            balls_faced=("batter_runs", "count"),
        ).reset_index().rename(columns={"batter": "player"})
        bat_players["bat_sr"] = (bat_players.runs / bat_players.balls_faced * 100).round(1)
        bat_players["bat_avg"] = (bat_players.runs / bat_players.bat_inn).round(1)

        # Players who bowled for this team
        bowl_players = d[d.bowling_team == team].groupby("bowler").agg(
            bowl_inn=("match_id", "nunique"),
            legal_balls=("is_legal", "sum"),
            runs_conceded=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
        ).reset_index().rename(columns={"bowler": "player"})
        bowl_players["overs"] = (bowl_players.legal_balls / 6).round(1)
        bowl_players["economy"] = np.where(
            bowl_players.overs > 0, (bowl_players.runs_conceded / bowl_players.overs).round(2), 0
        )

        # Merge
        squad = bat_players.merge(bowl_players, on="player", how="outer")
        for col in ["bat_inn", "runs", "balls_faced", "bowl_inn", "wickets", "legal_balls"]:
            if col in squad.columns:
                squad[col] = squad[col].fillna(0).astype(int)

        # Detect role
        squad["role"] = squad.apply(SquadEngine._detect_role, axis=1)

        # Total matches
        bat_matches = l[l.batting_team == team].groupby("batter")["match_id"].nunique().reset_index()
        bat_matches.columns = ["player", "bat_matches"]
        bowl_matches = d[d.bowling_team == team].groupby("bowler")["match_id"].nunique().reset_index()
        bowl_matches.columns = ["player", "bowl_matches"]
        squad = squad.merge(bat_matches, on="player", how="left")
        squad = squad.merge(bowl_matches, on="player", how="left")
        squad["matches"] = squad[["bat_matches", "bowl_matches"]].max(axis=1).fillna(0).astype(int)

        # Sort by matches played
        squad = squad.sort_values("matches", ascending=False).reset_index(drop=True)

        return squad

    @staticmethod
    def _detect_role(row) -> str:
        """Detect player role based on batting/bowling contribution."""
        bat_inn = row.get("bat_inn", 0)
        bowl_inn = row.get("bowl_inn", 0)
        runs = row.get("runs", 0)
        wickets = row.get("wickets", 0)
        balls_faced = row.get("balls_faced", 0)
        legal_balls = row.get("legal_balls", 0)

        if bat_inn == 0 and bowl_inn > 0:
            return "🎯 Bowler"
        if bowl_inn == 0 and bat_inn > 0:
            return "🏏 Batter"
        if bat_inn > 0 and bowl_inn > 0:
            bat_ratio = runs / max(bat_inn, 1)
            bowl_ratio = wickets / max(bowl_inn, 1)
            if bat_ratio > 15 and bowl_ratio > 0.5:
                return "⭐ All-Rounder"
            elif bat_ratio > 15:
                return "🏏 Batter"
            elif bowl_ratio > 0.5:
                return "🎯 Bowler"
            else:
                return "⭐ All-Rounder"
        return "❓ Unknown"

    @staticmethod
    def get_seasons_for_team(deliveries: pd.DataFrame, team: str) -> list:
        """Get list of seasons a team participated in, sorted by year."""
        seasons = deliveries[
            (deliveries.batting_team == team) | (deliveries.bowling_team == team)
        ].groupby("psl_edition")["season_year"].first().sort_values()
        return seasons.index.tolist()
