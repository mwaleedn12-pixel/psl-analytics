"""
PSL Analytics — Comprehensive Stats Engine

Complete cricket statistics covering:
- Full batting stats (50s, 100s, highest score, ducks, etc.)
- Full bowling stats (best figures, 3W, 4W, 5W, maidens, etc.)
- Fielding stats (catches, run-outs, stumpings)
- Dismissal analytics (how players get out)
- Partnership analytics
- Chase/Defence analytics
- Innings summary (scorecard-level)

Usage:
    from src.analytics.stats_engine import StatsEngine
"""

import pandas as pd
import numpy as np


class StatsEngine:
    """Complete cricket statistics calculator."""

    # ════════════════════════════════════════
    # BATTING — COMPLETE
    # ════════════════════════════════════════

    @staticmethod
    def full_batting_stats(deliveries: pd.DataFrame, min_innings: int = 1) -> pd.DataFrame:
        """Complete batting stats per player."""
        legal = deliveries[deliveries.is_legal == 1].copy()

        # Per-innings scores
        innings_scores = legal.groupby(["match_id", "batter"]).agg(
            runs=("batter_runs", "sum"),
            balls=("batter_runs", "count"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            dots=("is_dot", "sum"),
        ).reset_index()

        innings_scores["sr"] = (innings_scores.runs / innings_scores.balls * 100).round(1)

        # Career aggregates
        career = innings_scores.groupby("batter").agg(
            innings=("match_id", "nunique"),
            runs=("runs", "sum"),
            balls=("balls", "sum"),
            fours=("fours", "sum"),
            sixes=("sixes", "sum"),
            dots=("dots", "sum"),
            highest_score=("runs", "max"),
            fifties=("runs", lambda x: (x >= 50).sum()),
            hundreds=("runs", lambda x: (x >= 100).sum()),
            thirties=("runs", lambda x: ((x >= 30) & (x < 50)).sum()),
            ducks=("runs", lambda x: (x == 0).sum()),
        ).reset_index()

        career["avg"] = (career.runs / career.innings).round(2)
        career["sr"] = (career.runs / career.balls * 100).round(2)
        career["boundary_pct"] = ((career.fours + career.sixes) / career.balls * 100).round(2)
        career["dot_pct"] = (career.dots / career.balls * 100).round(2)
        career["runs_per_innings"] = (career.runs / career.innings).round(1)
        career["boundaries"] = career.fours + career.sixes
        career["boundary_runs"] = career.fours * 4 + career.sixes * 6
        career["boundary_runs_pct"] = (career.boundary_runs / career.runs * 100).round(1)

        # Not-outs (innings where player was NOT dismissed)
        dismissed = deliveries[deliveries.is_wicket == 1].groupby(["match_id", "player_out"]).size().reset_index()
        dismissed.columns = ["match_id", "batter", "times_out"]
        dismiss_career = dismissed.groupby("batter")["times_out"].sum().reset_index()
        dismiss_career.columns = ["batter", "times_dismissed"]
        career = career.merge(dismiss_career, on="batter", how="left")
        career["times_dismissed"] = career.times_dismissed.fillna(0).astype(int)
        career["not_outs"] = career.innings - career.times_dismissed
        career["batting_avg"] = np.where(
            career.times_dismissed > 0,
            (career.runs / career.times_dismissed).round(2),
            career.runs,
        )

        # Phase SR
        for phase in ["powerplay", "middle", "death"]:
            phase_data = legal[legal.phase == phase]
            phase_stats = phase_data.groupby("batter").agg(
                phase_runs=("batter_runs", "sum"),
                phase_balls=("batter_runs", "count"),
            ).reset_index()
            phase_stats[f"sr_{phase}"] = (phase_stats.phase_runs / phase_stats.phase_balls * 100).round(1)
            phase_stats[f"runs_{phase}"] = phase_stats.phase_runs
            career = career.merge(
                phase_stats[["batter", f"sr_{phase}", f"runs_{phase}"]],
                on="batter", how="left"
            )

        if min_innings > 1:
            career = career[career.innings >= min_innings]

        return career.sort_values("runs", ascending=False).reset_index(drop=True)

    # ════════════════════════════════════════
    # BOWLING — COMPLETE
    # ════════════════════════════════════════

    @staticmethod
    def full_bowling_stats(deliveries: pd.DataFrame, min_innings: int = 1) -> pd.DataFrame:
        """Complete bowling stats per player."""
        # Per-match bowling
        match_bowl = deliveries.groupby(["match_id", "bowler"]).agg(
            legal_balls=("is_legal", "sum"),
            runs_conceded=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
            dots=("is_dot", "sum"),
            fours_conceded=("is_four", "sum"),
            sixes_conceded=("is_six", "sum"),
            wides=("is_wide", "sum"),
            noballs=("is_noball", "sum"),
        ).reset_index()

        match_bowl["overs"] = match_bowl.legal_balls / 6

        # Best figures string
        match_bowl["figures"] = match_bowl.apply(
            lambda r: f"{int(r.wickets)}/{int(r.runs_conceded)}", axis=1
        )

        # Career aggregates
        career = match_bowl.groupby("bowler").agg(
            innings=("match_id", "nunique"),
            total_balls=("legal_balls", "sum"),
            runs_conceded=("runs_conceded", "sum"),
            wickets=("wickets", "sum"),
            dots=("dots", "sum"),
            fours_conceded=("fours_conceded", "sum"),
            sixes_conceded=("sixes_conceded", "sum"),
            wides=("wides", "sum"),
            noballs=("noballs", "sum"),
            three_wickets=("wickets", lambda x: (x >= 3).sum()),
            four_wickets=("wickets", lambda x: (x >= 4).sum()),
            five_wickets=("wickets", lambda x: (x >= 5).sum()),
        ).reset_index()

        career["overs"] = (career.total_balls / 6).round(1)
        career["economy"] = np.where(career.overs > 0, (career.runs_conceded / career.overs).round(2), 0)
        career["bowling_avg"] = np.where(career.wickets > 0, (career.runs_conceded / career.wickets).round(2), 0)
        career["bowling_sr"] = np.where(career.wickets > 0, (career.total_balls / career.wickets).round(1), 0)
        career["dot_pct"] = (career.dots / career.total_balls * 100).round(1)
        career["boundary_conceded_pct"] = (
            (career.fours_conceded + career.sixes_conceded) / career.total_balls * 100
        ).round(1)

        # Best figures
        best = match_bowl.sort_values(["wickets", "runs_conceded"], ascending=[False, True])
        best_per_bowler = best.groupby("bowler").first()[["figures"]].reset_index()
        best_per_bowler.columns = ["bowler", "best_figures"]
        career = career.merge(best_per_bowler, on="bowler", how="left")

        # Phase economy
        for phase in ["powerplay", "middle", "death"]:
            phase_data = deliveries[deliveries.phase == phase]
            ps = phase_data.groupby("bowler").agg(
                p_legal=("is_legal", "sum"), p_runs=("total_runs", "sum"),
                p_wickets=("is_wicket", "sum"),
            ).reset_index()
            ps["p_overs"] = ps.p_legal / 6
            ps[f"economy_{phase}"] = np.where(ps.p_overs > 0, (ps.p_runs / ps.p_overs).round(2), 0)
            ps[f"wickets_{phase}"] = ps.p_wickets
            career = career.merge(
                ps[["bowler", f"economy_{phase}", f"wickets_{phase}"]],
                on="bowler", how="left"
            )

        if min_innings > 1:
            career = career[career.innings >= min_innings]

        return career.sort_values("wickets", ascending=False).reset_index(drop=True)

    # ════════════════════════════════════════
    # FIELDING
    # ════════════════════════════════════════

    @staticmethod
    def fielding_stats(deliveries: pd.DataFrame) -> pd.DataFrame:
        """Fielding stats per player."""
        wickets = deliveries[deliveries.is_wicket == 1].copy()

        catches = wickets[(wickets.wicket_kind == "caught") & wickets.fielder.notna()]
        catch_counts = catches.groupby("fielder").size().reset_index(name="catches")

        runouts = wickets[(wickets.wicket_kind == "run out") & wickets.fielder.notna()]
        ro_counts = runouts.groupby("fielder").size().reset_index(name="run_outs")

        stumpings = wickets[(wickets.wicket_kind == "stumped") & wickets.fielder.notna()]
        st_counts = stumpings.groupby("fielder").size().reset_index(name="stumpings")

        # Caught & bowled
        cb = wickets[wickets.wicket_kind == "caught and bowled"]
        cb_counts = cb.groupby("bowler").size().reset_index(name="caught_bowled")
        cb_counts.columns = ["fielder", "caught_bowled"]

        # Merge all
        all_fielders = set()
        for df in [catch_counts, ro_counts, st_counts, cb_counts]:
            all_fielders.update(df.iloc[:, 0].values)

        result = pd.DataFrame({"player": sorted(all_fielders)})
        result = result.merge(catch_counts.rename(columns={"fielder": "player"}), on="player", how="left")
        result = result.merge(ro_counts.rename(columns={"fielder": "player"}), on="player", how="left")
        result = result.merge(st_counts.rename(columns={"fielder": "player"}), on="player", how="left")
        result = result.merge(cb_counts.rename(columns={"fielder": "player"}), on="player", how="left")

        for col in ["catches", "run_outs", "stumpings", "caught_bowled"]:
            result[col] = result[col].fillna(0).astype(int)

        result["total_dismissals"] = result.catches + result.run_outs + result.stumpings + result.caught_bowled
        result["innings"] = result.player.map(
            deliveries.groupby("batter")["match_id"].nunique().to_dict()
        ).fillna(deliveries.groupby("bowler")["match_id"].nunique().to_dict())

        return result.sort_values("total_dismissals", ascending=False).reset_index(drop=True)

    # ════════════════════════════════════════
    # DISMISSAL ANALYTICS
    # ════════════════════════════════════════

    @staticmethod
    def dismissal_analysis(deliveries: pd.DataFrame, player: str = None) -> pd.DataFrame:
        """How players get out — bowled, caught, LBW, run out, etc."""
        wickets = deliveries[deliveries.is_wicket == 1].copy()
        if player:
            wickets = wickets[wickets.player_out == player]

        dismissals = wickets.groupby("wicket_kind").size().reset_index(name="count")
        total = dismissals["count"].sum()
        dismissals["pct"] = (dismissals["count"] / total * 100).round(1)
        return dismissals.sort_values("count", ascending=False).reset_index(drop=True)

    @staticmethod
    def dismissal_by_player(deliveries: pd.DataFrame, min_innings: int = 5) -> pd.DataFrame:
        """Dismissal breakdown per player."""
        wickets = deliveries[deliveries.is_wicket == 1].copy()

        pivot = wickets.groupby(["player_out", "wicket_kind"]).size().unstack(fill_value=0).reset_index()
        pivot.columns.name = None
        pivot = pivot.rename(columns={"player_out": "player"})

        # Add innings count
        innings = deliveries[deliveries.is_legal == 1].groupby("batter")["match_id"].nunique().reset_index()
        innings.columns = ["player", "innings"]
        pivot = pivot.merge(innings, on="player", how="left")
        pivot["total_dismissals"] = pivot.drop(columns=["player", "innings"], errors="ignore").sum(axis=1)

        if min_innings > 1:
            pivot = pivot[pivot.innings >= min_innings]

        return pivot.sort_values("total_dismissals", ascending=False).reset_index(drop=True)

    # ════════════════════════════════════════
    # PARTNERSHIP ANALYTICS
    # ════════════════════════════════════════

    @staticmethod
    def partnerships(deliveries: pd.DataFrame, min_runs: int = 20) -> pd.DataFrame:
        """Calculate partnerships between batting pairs."""
        df = deliveries.copy()

        # Create a sorted pair key
        df["pair"] = df.apply(
            lambda r: tuple(sorted([r["batter"], r["non_striker"]])), axis=1
        )

        # Group by match + innings + pair, detect partnership breaks at wickets
        df = df.sort_values(["match_id", "innings", "over", "ball"])

        partnerships = []
        for (mid, inn), group in df.groupby(["match_id", "innings"]):
            current_pair = None
            p_runs = 0
            p_balls = 0

            for _, row in group.iterrows():
                pair = row["pair"]
                if pair != current_pair:
                    if current_pair and p_runs >= 0:
                        partnerships.append({
                            "match_id": mid, "innings": inn,
                            "batter1": current_pair[0], "batter2": current_pair[1],
                            "runs": p_runs, "balls": p_balls,
                        })
                    current_pair = pair
                    p_runs = 0
                    p_balls = 0

                p_runs += row["total_runs"]
                if row["is_legal"]:
                    p_balls += 1

            if current_pair and p_runs >= 0:
                partnerships.append({
                    "match_id": mid, "innings": inn,
                    "batter1": current_pair[0], "batter2": current_pair[1],
                    "runs": p_runs, "balls": p_balls,
                })

        pdf = pd.DataFrame(partnerships)
        if len(pdf) == 0:
            return pdf

        pdf["sr"] = np.where(pdf.balls > 0, (pdf.runs / pdf.balls * 100).round(1), 0)

        # Aggregate by pair
        pair_stats = pdf.groupby(["batter1", "batter2"]).agg(
            partnerships=("runs", "count"),
            total_runs=("runs", "sum"),
            avg_runs=("runs", "mean"),
            highest=("runs", "max"),
            total_balls=("balls", "sum"),
        ).reset_index()

        pair_stats["avg_runs"] = pair_stats.avg_runs.round(1)
        pair_stats["avg_sr"] = (pair_stats.total_runs / pair_stats.total_balls * 100).round(1)
        pair_stats["fifty_plus"] = pdf.groupby(["batter1", "batter2"]).apply(
            lambda x: (x.runs >= 50).sum()
        ).values

        pair_stats = pair_stats[pair_stats.total_runs >= min_runs]
        return pair_stats.sort_values("total_runs", ascending=False).reset_index(drop=True)

    # ════════════════════════════════════════
    # CHASE / DEFENCE ANALYTICS
    # ════════════════════════════════════════

    @staticmethod
    def chase_analytics(deliveries: pd.DataFrame, matches: pd.DataFrame) -> dict:
        """Chase success rate by target range."""
        decided = matches[matches.winner.notna()].copy()

        # Get innings 1 totals
        inn1 = deliveries[deliveries.innings == 1].groupby("match_id")["total_runs"].sum().reset_index()
        inn1.columns = ["match_id", "inn1_total"]
        inn1["match_id"] = inn1.match_id.astype(str)
        decided["match_id"] = decided.match_id.astype(str)
        decided = decided.merge(inn1, on="match_id", how="left")
        decided["target"] = decided.inn1_total + 1
        decided["chase_won"] = decided.win_by_wickets.notna().astype(int)

        # By target range
        bins = [0, 120, 140, 160, 180, 200, 300]
        labels = ["<120", "120-139", "140-159", "160-179", "180-199", "200+"]
        decided["target_range"] = pd.cut(decided.target, bins=bins, labels=labels, right=False)

        range_stats = decided.groupby("target_range", observed=True).agg(
            matches=("match_id", "count"),
            chase_wins=("chase_won", "sum"),
        ).reset_index()
        range_stats["chase_pct"] = (range_stats.chase_wins / range_stats.matches * 100).round(1)

        # Overall
        overall = {
            "total_chases": int(decided.chase_won.sum()),
            "total_defences": int((1 - decided.chase_won).sum()),
            "chase_pct": round(decided.chase_won.mean() * 100, 1),
            "highest_chase": int(decided[decided.chase_won == 1].target.max()) if decided.chase_won.sum() > 0 else 0,
            "lowest_defended": int(decided[decided.chase_won == 0].target.min()) if (1-decided.chase_won).sum() > 0 else 0,
        }

        return {"overall": overall, "by_range": range_stats}

    # ════════════════════════════════════════
    # TEAM COMPLETE STATS
    # ════════════════════════════════════════

    @staticmethod
    def team_complete_stats(
        deliveries: pd.DataFrame,
        matches: pd.DataFrame,
        team: str,
    ) -> dict:
        """Complete team statistics."""
        team_matches = matches[(matches.team1 == team) | (matches.team2 == team)].copy()
        team_matches["won"] = (team_matches.winner == team).astype(int)
        team_bat = deliveries[deliveries.batting_team == team]
        team_bowl = deliveries[deliveries.bowling_team == team]
        legal_bat = team_bat[team_bat.is_legal == 1]

        # Innings totals
        innings = team_bat.groupby(["match_id", "innings"]).agg(
            runs=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
            legal_balls=("is_legal", "sum"),
        ).reset_index()

        # Lowest total — only complete innings (all out or 20 overs)
        complete_innings = innings[(innings.wickets == 10) | (innings.legal_balls >= 120)]
        lowest = int(complete_innings.runs.min()) if len(complete_innings) > 0 else int(innings.runs.min())

        # Streaks
        results = team_matches.sort_values("date").won.values
        win_streak = max_streak(results, 1)
        lose_streak = max_streak(results, 0)

        return {
            "played": len(team_matches),
            "won": int(team_matches.won.sum()),
            "lost": len(team_matches) - int(team_matches.won.sum()),
            "win_pct": round(team_matches.won.mean() * 100, 1),
            "total_runs": int(team_bat.total_runs.sum()),
            "total_wickets_taken": int(team_bowl.is_wicket.sum()),
            "total_fours": int(team_bat.is_four.sum()),
            "total_sixes": int(team_bat.is_six.sum()),
            "avg_score": round(innings.runs.mean(), 1),
            "highest_score": int(innings.runs.max()),
            "lowest_score": lowest,
            "avg_conceded": round(
                team_bowl.groupby(["match_id", "innings"])["total_runs"].sum().mean(), 1
            ),
            "longest_win_streak": win_streak,
            "longest_lose_streak": lose_streak,
        }


def max_streak(arr, value):
    """Find longest consecutive streak of a value."""
    max_s = 0
    current = 0
    for v in arr:
        if v == value:
            current += 1
            max_s = max(max_s, current)
        else:
            current = 0
    return max_s
