# PSL Analytics & Match Intelligence — Architecture

## 1. High-Level Architecture

```text
DATA SOURCES
     ↓
DATA INGESTION
     ↓
DATA VALIDATION
     ↓
DATA CLEANING
     ↓
FEATURE ENGINEERING
     ↓
ANALYTICS ENGINE
     ↓
ML MODEL LAYER
     ↓
DASHBOARD
```

## 2. Project Structure

```text
psl-analytics/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── external/
│   └── README.md
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_impact_score.ipynb
│   ├── 04_win_probability.ipynb
│   └── 05_model_evaluation.ipynb
├── src/
│   ├── ingestion/
│   ├── cleaning/
│   ├── features/
│   ├── analytics/
│   ├── models/
│   ├── evaluation/
│   └── utils/
├── dashboard/
│   ├── app.py
│   ├── pages/
│   ├── components/
│   └── assets/
├── models/
├── tests/
├── docs/
├── requirements.txt
├── README.md
└── .gitignore
```

## 3. Data Model

```text
Match
 ├── Season
 ├── Venue
 ├── Team
 ├── Toss
 ├── Innings
 │    └── Delivery
 ├── Player
 └── Result
```

## 4. Data Flow

```text
Raw Data
   ↓
Validation
   ↓
Cleaning
   ↓
Processed Dataset
   ↓
Feature Store
   ↓
Analytics / ML
   ↓
Dashboard
```

## 5. Feature Layers

### Batting
runs, balls, strike_rate, boundary_rate, dot_ball_rate, phase_runs, phase_sr

### Bowling
wickets, runs_conceded, economy, dot_ball_rate, boundary_conceded_rate, phase_economy

### Context
required_runs, required_rr, wickets_remaining, balls_remaining, current_rr, pressure_index

## 6. Analytics Modules
- impact_engine
- form_engine
- venue_engine
- phase_engine
- matchup_engine
- team_engine
- toss_engine
- turning_point_engine

## 7. ML Layer
- Expected Runs model
- Expected Wickets model
- Win Probability model
- Optional Player Clustering model

## 8. Dashboard
Streamlit pages should consume analytics/model outputs rather than contain core analytical logic.

## 9. Architecture Principles
1. Raw data remains immutable.
2. Analytics logic stays outside the UI.
3. ML training stays separate from dashboard execution.
4. Metrics are reproducible.
5. Data leakage is prevented.
6. Major metrics are documented.
