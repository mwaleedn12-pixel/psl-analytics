# PSL Analytics — Development Rules

## 1. Data Rules
1. Never modify raw source data.
2. Create processed datasets after cleaning.
3. Detect and remove duplicate matches.
4. Normalize player, team, and venue names.
5. Keep a mapping/version history when normalization changes.

## 2. Cricket Rules
- Powerplay: overs 1–6
- Middle overs: overs 7–15
- Death overs: overs 16–20
- Calculations must respect the actual match format and available deliveries.

## 3. Metric Rules
Every custom metric must document:
- Purpose
- Formula
- Inputs
- Weights
- Assumptions
- Edge cases
- Validation results
- Version

## 4. Impact Score
Impact Score must not rely only on raw runs/wickets. It should incorporate context, difficulty, phase, and match contribution where data supports it.

## 5. ML Rules
### No Data Leakage
No future information may be included in prediction features.

### Time-Aware Evaluation
Prefer chronological train/test splits for historical match prediction.

### Evaluation
Use appropriate metrics such as:
- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- Log Loss
- Calibration

For win probability, Log Loss and calibration are especially important.

## 6. Visualization Rules
Prefer:
- Line charts
- Bar charts
- Heatmaps
- Scatter plots
- Box plots
- KPI cards

Avoid:
- Unnecessary 3D charts
- Excessive colors
- Decorative charts
- Misleading axes

## 7. Dashboard Rules
- Consistent filters
- Clear metric definitions
- Empty states
- No crashes on invalid selections
- Reasonable loading time

## 8. Code Rules
Follow PEP 8. Use meaningful names, modular functions, type hints where useful, and docstrings for important analytical functions.

## 9. Git Rules
Recommended branches:
- main
- develop
- feature/impact-score
- feature/win-probability
- feature/venue-analysis

Commit examples:
- feat: add player impact score
- feat: add venue analytics
- fix: handle missing bowling data
- docs: update architecture
- test: add impact score tests

## 10. Accuracy Rule
Statistical correctness has priority over visual presentation. Approximate metrics must be clearly labeled as estimated.
