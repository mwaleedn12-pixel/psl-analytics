# Data Directory

## Structure

```
data/
├── raw/          ← Original source data (NEVER modify)
├── processed/    ← Cleaned & transformed datasets
├── external/     ← Third-party reference data
└── README.md
```

## Rules

1. **`raw/` is immutable.** Never edit, overwrite, or delete raw source files.
2. All cleaning and transformation outputs go into `processed/`.
3. External reference datasets (e.g. stadium coordinates, team logos) go into `external/`.
4. Keep file names descriptive: `psl_ball_by_ball.csv`, not `data2.csv`.

## Required Datasets (Phase 1)

| File | Description |
|------|-------------|
| `psl_matches.csv` | Match-level metadata (teams, venue, toss, result) |
| `psl_deliveries.csv` | Ball-by-ball data (batter, bowler, runs, wickets, extras) |

## Data Sources

- Kaggle PSL datasets
- ESPN Cricinfo (manual / scraped)
- HowStat
- CricSheet (if PSL data available)
