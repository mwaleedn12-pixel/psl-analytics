# PSL Analytics & Match Intelligence Platform

## 1. Project Overview
**Project Name:** PSL Analytics & Match Intelligence Platform  
**Type:** Sports Data Analytics + Machine Learning + Interactive Dashboard

The platform analyzes historical PSL and ball-by-ball data to provide player, team, venue, matchup, contextual performance, and ML-based match intelligence.

## 2. Objectives
- Identify impactful players using a custom Impact Score.
- Analyze powerplay, middle-overs, and death-overs performance.
- Compare venues and toss effects.
- Analyze team and batter-vs-bowler matchups.
- Track player form.
- Estimate expected runs/wickets.
- Predict live win probability.
- Detect match turning points.
- Find similar players and player archetypes.

## 3. Core Features
### Player Analytics
Matches, innings, runs, average, strike rate, boundaries, dot-ball %, wickets, economy, phase performance, form, and Impact Score.

### Player Impact Score
Combine batting, bowling, fielding, and match-context contribution. The formula must be documented, validated, and versioned.

### Phase Analytics
- Powerplay: overs 1–6
- Middle: overs 7–15
- Death: overs 16–20

### Venue Analytics
Average scores, chasing/defending win %, toss impact, scoring rates, pace/spin performance, boundaries, and sixes.

### Matchups
Team-vs-team and batter-vs-bowler historical performance.

### Form
Last 5/10 matches, rolling averages, strike rate, wickets, economy, and Impact Score.

### Expected Performance
Expected Runs and Expected Wickets, plus actual-vs-expected values.

### Win Probability
Predict team win probability using score, wickets, overs, required RR, venue, teams, players, phase, and other available contextual features.

### Turning Points
Detect major win-probability swings caused by wickets, boundaries, or other events.

### Player Similarity
Find similar players using standardized performance features and similarity/clustering methods.

### Team Intelligence
Batting, bowling, phase, chasing, defending, pace, and spin strengths.

## 4. Dashboard Pages
1. Overview
2. Player Analytics
3. Team Analytics
4. Match Explorer
5. Matchups
6. Phase Analytics
7. Venue Intelligence
8. Player Form
9. Match Intelligence
10. Predictions

## 5. Technology
- Python
- Pandas
- NumPy
- Scikit-learn
- Plotly
- Streamlit
- CSV/Parquet initially
- SQLite/PostgreSQL optionally
- Git/GitHub

## 6. Non-Functional Requirements
The system should be reproducible, modular, maintainable, responsive, documented, and version controlled.

## 7. Success Criteria
- Reproducible data pipeline
- Accurate analytical metrics
- Explainable custom metrics
- Properly evaluated ML models
- Leakage-free prediction
- Interactive dashboard
- Professional documentation and GitHub repository

## 8. Initial Out of Scope
- Full commercial live-score infrastructure
- Betting recommendations
- Fantasy recommendations
- Automated social posting
