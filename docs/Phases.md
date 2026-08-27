# PSL Analytics — Development Phases

## Phase 0 — Project Setup
- Repository
- Python environment
- Folder structure
- Git
- Documentation

**Deliverables:** README.md, Architecture.md, Rules.md, Project_Requirements.md

## Phase 1 — Data Acquisition
- Acquire historical PSL data
- Acquire ball-by-ball data
- Collect match metadata
- Map players, teams, venues

**Output:** data/raw/

## Phase 2 — Data Cleaning
- Missing values
- Duplicate matches
- Invalid deliveries
- Name normalization
- Date normalization

**Output:** data/processed/

## Phase 3 — Exploratory Data Analysis
Analyze:
- Team performance
- Player performance
- Scoring trends
- Bowling trends
- Venue trends
- Toss
- Chasing
- Phase performance

**Deliverable:** 01_data_exploration.ipynb

## Phase 4 — Feature Engineering
Create:
- Player features
- Match-state features
- Required RR
- Current RR
- Wickets remaining
- Balls remaining
- Pressure Index
- Team/opponent strength
- Phase features

## Phase 5 — Impact Score
Develop:
- Batting Impact
- Bowling Impact
- Fielding Impact where data supports it
- Context Impact

Combine into PSL Impact Score.

Deliverables:
- Formula
- Documentation
- Validation
- Rankings

## Phase 6 — Advanced Analytics
Implement:
- Player form
- Venue analysis
- Phase analysis
- H2H
- Toss analysis
- Batter vs bowler
- Team strength

## Phase 7 — Expected Performance
Build:
- Expected Runs model
- Expected Wickets model

Evaluate performance and document limitations.

## Phase 8 — Win Probability
Start with Logistic Regression baseline, then compare stronger models such as Random Forest and Gradient Boosting/XGBoost where appropriate.

Evaluate both discrimination and probability calibration.

## Phase 9 — Turning Points
Track probability before and after important events and rank major swings.

## Phase 10 — Player Similarity
- Feature scaling
- Similarity
- Clustering
- Player archetypes

Possible archetypes:
- Anchor
- Aggressor
- Finisher
- Powerplay Bowler
- Death Bowler
- Spinner
- All-rounder

## Phase 11 — Dashboard
Build:
- Overview
- Players
- Teams
- Matchups
- Venues
- Phases
- Form
- Match Intelligence
- Predictions

## Phase 12 — Testing
Test:
- Data pipeline
- Metric calculations
- Impact Score
- Features
- ML predictions
- Dashboard filters

## Phase 13 — Optimization
Improve caching, data access, model loading, and chart rendering.

## Phase 14 — Deployment
Potential platforms:
- Streamlit Community Cloud
- Render
- Railway
- VPS

## Phase 15 — Portfolio Polish
Finalize:
- README
- Screenshots
- Architecture diagram
- Model explanation
- Analytical insights
- Limitations
- Future roadmap
- Demo link
