"""
PSL Analytics — CricSheet JSON Ingestion

Reads CricSheet JSON match files and produces two DataFrames:
  1. matches  — one row per match (metadata, toss, result)
  2. deliveries — one row per ball (batter, bowler, runs, wickets, extras)

Usage:
    from src.ingestion.cricsheet_loader import load_all_matches
    matches_df, deliveries_df = load_all_matches("data/raw/cricsheet")
"""

import json
import os
from pathlib import Path
from typing import Tuple

import pandas as pd


def parse_match_info(filepath: str, match_data: dict) -> dict:
    """Extract match-level metadata from a CricSheet JSON file."""
    info = match_data["info"]
    match_id = Path(filepath).stem

    teams = info.get("teams", [])
    outcome = info.get("outcome", {})
    toss = info.get("toss", {})
    event = info.get("event", {})

    # Winner and margin
    winner = outcome.get("winner", None)
    win_by = outcome.get("by", {})
    win_by_runs = win_by.get("runs", None)
    win_by_wickets = win_by.get("wickets", None)
    result_method = outcome.get("method", None)
    result_type = outcome.get("result", None)  # "no result", "tie", etc.

    # Player of match
    pom = info.get("player_of_match", [])
    player_of_match = pom[0] if pom else None

    return {
        "match_id": match_id,
        "season": info.get("season", None),
        "date": info["dates"][0] if info.get("dates") else None,
        "match_number": event.get("match_number", None),
        "venue": info.get("venue", None),
        "city": info.get("city", None),
        "team1": teams[0] if len(teams) > 0 else None,
        "team2": teams[1] if len(teams) > 1 else None,
        "toss_winner": toss.get("winner", None),
        "toss_decision": toss.get("decision", None),
        "winner": winner,
        "win_by_runs": win_by_runs,
        "win_by_wickets": win_by_wickets,
        "result_method": result_method,
        "result_type": result_type,
        "player_of_match": player_of_match,
        "overs_per_side": info.get("overs", 20),
        "balls_per_over": info.get("balls_per_over", 6),
        "match_type": info.get("match_type", "T20"),
        "gender": info.get("gender", "male"),
    }


def parse_deliveries(filepath: str, match_data: dict) -> list[dict]:
    """Extract ball-by-ball data from a CricSheet JSON file."""
    match_id = Path(filepath).stem
    info = match_data["info"]
    season = info.get("season", None)
    venue = info.get("venue", None)
    date = info["dates"][0] if info.get("dates") else None
    teams = info.get("teams", [])

    rows = []
    for innings_idx, innings in enumerate(match_data.get("innings", []), start=1):
        batting_team = innings.get("team", None)
        bowling_team = None
        if batting_team and len(teams) == 2:
            bowling_team = teams[1] if batting_team == teams[0] else teams[0]

        for over_data in innings.get("overs", []):
            over_num = over_data["over"]  # 0-indexed in CricSheet

            for ball_idx, delivery in enumerate(over_data.get("deliveries", [])):
                runs = delivery.get("runs", {})
                extras = delivery.get("extras", {})

                # Wicket info
                wickets_data = delivery.get("wickets", [])
                is_wicket = 1 if wickets_data else 0
                wicket_kind = wickets_data[0]["kind"] if wickets_data else None
                player_out = wickets_data[0]["player_out"] if wickets_data else None
                fielder = None
                if wickets_data and wickets_data[0].get("fielders"):
                    fielder = wickets_data[0]["fielders"][0].get("name", None)

                # Extras breakdown
                wide_runs = extras.get("wides", 0)
                noball_runs = extras.get("noballs", 0)
                bye_runs = extras.get("byes", 0)
                legbye_runs = extras.get("legbyes", 0)
                penalty_runs = extras.get("penalty", 0)

                is_wide = 1 if wide_runs > 0 else 0
                is_noball = 1 if noball_runs > 0 else 0
                is_bye = 1 if bye_runs > 0 else 0
                is_legbye = 1 if legbye_runs > 0 else 0

                # Legal ball check (wides and noballs are not legal deliveries)
                is_legal = 0 if (is_wide or is_noball) else 1

                row = {
                    "match_id": match_id,
                    "season": season,
                    "date": date,
                    "venue": venue,
                    "innings": innings_idx,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "over": over_num + 1,  # Convert to 1-indexed
                    "ball": ball_idx + 1,
                    "batter": delivery.get("batter", None),
                    "non_striker": delivery.get("non_striker", None),
                    "bowler": delivery.get("bowler", None),
                    "batter_runs": runs.get("batter", 0),
                    "extras_runs": runs.get("extras", 0),
                    "total_runs": runs.get("total", 0),
                    "is_wide": is_wide,
                    "is_noball": is_noball,
                    "is_bye": is_bye,
                    "is_legbye": is_legbye,
                    "wide_runs": wide_runs,
                    "noball_runs": noball_runs,
                    "bye_runs": bye_runs,
                    "legbye_runs": legbye_runs,
                    "penalty_runs": penalty_runs,
                    "is_legal": is_legal,
                    "is_wicket": is_wicket,
                    "wicket_kind": wicket_kind,
                    "player_out": player_out,
                    "fielder": fielder,
                    "is_four": 1 if runs.get("batter", 0) == 4 else 0,
                    "is_six": 1 if runs.get("batter", 0) == 6 else 0,
                    "is_dot": 1 if (runs.get("total", 0) == 0 and is_legal) else 0,
                }
                rows.append(row)

    return rows


def load_all_matches(raw_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load all CricSheet JSON files from a directory.

    Args:
        raw_dir: Path to directory containing .json match files.

    Returns:
        (matches_df, deliveries_df)
    """
    match_rows = []
    delivery_rows = []
    errors = []

    json_files = sorted(
        [f for f in os.listdir(raw_dir) if f.endswith(".json")]
    )

    for filename in json_files:
        filepath = os.path.join(raw_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                match_data = json.load(f)

            match_rows.append(parse_match_info(filepath, match_data))
            delivery_rows.extend(parse_deliveries(filepath, match_data))
        except Exception as e:
            errors.append({"file": filename, "error": str(e)})

    if errors:
        print(f"WARNING: {len(errors)} files had errors:")
        for err in errors:
            print(f"  {err['file']}: {err['error']}")

    matches_df = pd.DataFrame(match_rows)
    deliveries_df = pd.DataFrame(delivery_rows)

    # Sort
    if not matches_df.empty:
        matches_df["date"] = pd.to_datetime(matches_df["date"])
        matches_df = matches_df.sort_values("date").reset_index(drop=True)

    if not deliveries_df.empty:
        deliveries_df["date"] = pd.to_datetime(deliveries_df["date"])
        deliveries_df = deliveries_df.sort_values(
            ["date", "match_id", "innings", "over", "ball"]
        ).reset_index(drop=True)

    return matches_df, deliveries_df


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.config import RAW_DATA_DIR

    cricsheet_dir = RAW_DATA_DIR / "cricsheet"
    print(f"Loading from: {cricsheet_dir}")

    matches, deliveries = load_all_matches(str(cricsheet_dir))

    print(f"\nMatches: {len(matches)} rows, {len(matches.columns)} columns")
    print(f"Deliveries: {len(deliveries)} rows, {len(deliveries.columns)} columns")

    # Save to processed
    processed_dir = RAW_DATA_DIR.parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    matches.to_csv(processed_dir / "psl_matches.csv", index=False)
    deliveries.to_csv(processed_dir / "psl_deliveries.csv", index=False)
    print(f"\nSaved to {processed_dir}")
