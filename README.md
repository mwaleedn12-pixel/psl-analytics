# 🏏 PSL Analytics & Match Intelligence Platform

An end-to-end cricket analytics platform built on historical Pakistan Super League (PSL) data. Combines ball-by-ball data engineering, contextual player impact metrics, phase and venue analytics, and machine-learning-based win probability prediction.

---

## Features (Planned)

| Module | Description | Status |
|--------|-------------|--------|
| Data Pipeline | Ingestion, validation, cleaning, normalization | 🔲 |
| Player Analytics | Batting, bowling, phase performance, Impact Score | 🔲 |
| Team Analytics | Team strengths, chasing/defending, pace/spin | 🔲 |
| Phase Analytics | Powerplay, middle, death overs analysis | 🔲 |
| Venue Intelligence | Venue profiles, toss impact, scoring trends | 🔲 |
| Matchups | Batter vs Bowler, Team vs Team | 🔲 |
| Player Form | Rolling averages, recent performance trends | 🔲 |
| Impact Score | Custom contextual performance metric | 🔲 |
| Expected Performance | Expected Runs & Expected Wickets models | 🔲 |
| Win Probability | ML-based live win probability prediction | 🔲 |
| Turning Points | Detect match-changing moments | 🔲 |
| Player Similarity | Find similar players & player archetypes | 🔲 |
| Dashboard | Interactive Streamlit analytics dashboard | 🔲 |

## Tech Stack

- **Data:** Python, Pandas, NumPy
- **ML:** Scikit-learn, XGBoost
- **Visualization:** Plotly
- **Dashboard:** Streamlit
- **Storage:** CSV / Parquet

## Project Structure

```
psl-analytics/
├── data/              ← Raw, processed & external datasets
├── notebooks/         ← Jupyter exploration & analysis
├── src/               ← Core Python modules
│   ├── ingestion/
│   ├── cleaning/
│   ├── features/
│   ├── analytics/
│   ├── models/
│   ├── evaluation/
│   └── utils/
├── dashboard/         ← Streamlit app
├── models/            ← Trained ML models
├── tests/             ← Unit & integration tests
├── docs/              ← Project documentation
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# Clone
git clone https://github.com/<your-username>/psl-analytics.git
cd psl-analytics

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run dashboard/app.py
```

## Development Phases

See [docs/Phases.md](docs/Phases.md) for the full roadmap.

## Documentation

- [Project Requirements](docs/Project_Requirements.md)
- [Architecture](docs/Architecture.md)
- [Development Rules](docs/Rules.md)
- [Development Phases](docs/Phases.md)
- [Project Memory](docs/Memory.md)

## License

This project is for portfolio and educational purposes.

---

*Built with data, cricket knowledge, and a lot of chai.* ☕
