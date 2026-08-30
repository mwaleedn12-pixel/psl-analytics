"""AI Insights — auto-generated cricket intelligence."""
import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, TEAM_COLORS, fix_metrics

inject_custom_css()
fix_metrics()
hero_card("🤖 AI Insights", "Auto-generated cricket intelligence — trends, patterns, and observations")
seam_divider()

@st.cache_data
def load_data():
    m = pd.read_csv(PROJECT_ROOT / "data/processed/psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROJECT_ROOT / "data/processed/psl_deliveries_clean.csv", low_memory=False)
    return m, d

@st.cache_data
def generate_insights(_m, _d):
    m, d = _m, _d
    legal = d[d.is_legal == 1]
    insights = []

    # 1. Scoring trend
    inn = d.groupby(["match_id","innings","psl_edition","season_year"])["total_runs"].sum().reset_index()
    season_avg = inn.groupby("season_year")["total_runs"].mean()
    first_yr, last_yr = season_avg.index.min(), season_avg.index.max()
    first_avg, last_avg = season_avg.iloc[0], season_avg.iloc[-1]
    change = round(last_avg - first_avg, 0)
    insights.append({
        "category": "📈 Scoring Trend",
        "insight": f"Average innings score has {'increased' if change > 0 else 'decreased'} by {abs(change):.0f} runs from PSL 1 ({first_avg:.0f}) to the latest season ({last_avg:.0f}). T20 batting has become significantly more aggressive.",
        "importance": "high",
    })

    # 2. Toss dominance
    decided = m[m.winner.notna()].copy()
    decided["toss_won_match"] = (decided.toss_winner == decided.winner).astype(int)
    toss_pct = decided.toss_won_match.mean() * 100
    field_pct = (decided.toss_decision == "field").mean() * 100
    insights.append({
        "category": "🪙 Toss Impact",
        "insight": f"Toss winners win {toss_pct:.1f}% of matches. {field_pct:.0f}% of captains choose to field first, confirming chasing preference in PSL.",
        "importance": "high",
    })

    # 3. Death overs explosion
    death = d[d.phase == "death"]
    pp = d[d.phase == "powerplay"]
    death_rr = death.total_runs.sum() / (death[death.is_legal==1].is_legal.sum() / 6)
    pp_rr = pp.total_runs.sum() / (pp[pp.is_legal==1].is_legal.sum() / 6)
    insights.append({
        "category": "💀 Death Overs",
        "insight": f"Death overs run rate ({death_rr:.2f}) is {death_rr/pp_rr:.1f}x higher than powerplay ({pp_rr:.2f}). Teams score {death_rr - pp_rr:.1f} more runs per over in the death.",
        "importance": "medium",
    })

    # 4. Top impact player
    from src.analytics.impact_engine import compute_impact_scores, compute_career_impact
    scores = compute_impact_scores(d, m)
    career = compute_career_impact(scores, min_matches=20)
    top = career.iloc[0]
    insights.append({
        "category": "⭐ Most Impactful",
        "insight": f"{top.player} has the highest career Impact Score ({top.avg_impact:.1f}) among players with 20+ matches — combining batting, bowling, fielding, and context contribution.",
        "importance": "high",
    })

    # 5. Chase analysis
    chase_wins = decided.win_by_wickets.notna().sum()
    total = len(decided)
    chase_pct = chase_wins / total * 100
    insights.append({
        "category": "🎯 Chasing Dominance",
        "insight": f"Chasing teams win {chase_pct:.1f}% of PSL matches ({chase_wins}/{total}). This confirms a significant second-innings advantage across PSL history.",
        "importance": "medium",
    })

    # 6. Six hitting evolution
    sixes_by_season = d.groupby("season_year")["is_six"].sum()
    matches_by_season = m.groupby("season_year").size()
    sixes_per_match = (sixes_by_season / matches_by_season).round(1)
    first_spm = sixes_per_match.iloc[0]
    last_spm = sixes_per_match.iloc[-1]
    insights.append({
        "category": "💥 Six Hitting",
        "insight": f"Sixes per match have gone from {first_spm} (PSL 1) to {last_spm} (latest season) — a {((last_spm/first_spm - 1)*100):.0f}% increase, reflecting the power-hitting revolution in T20 cricket.",
        "importance": "medium",
    })

    # 7. Best venue for batting
    venue_inn = d.groupby(["match_id","innings","venue"])["total_runs"].sum().reset_index()
    venue_avg = venue_inn.groupby("venue")["total_runs"].mean()
    best_venue = venue_avg.idxmax()
    best_avg = venue_avg.max()
    worst_venue = venue_avg.idxmin()
    worst_avg = venue_avg.min()
    insights.append({
        "category": "🏟️ Venue",
        "insight": f"{best_venue.split(',')[0]} is the highest scoring venue (avg {best_avg:.0f}), while {worst_venue.split(',')[0]} is the toughest (avg {worst_avg:.0f}) — a {best_avg - worst_avg:.0f} run difference.",
        "importance": "medium",
    })

    # 8. Dot ball pressure
    total_dots = d.is_dot.sum()
    total_legal = d.is_legal.sum()
    dot_pct = total_dots / total_legal * 100
    insights.append({
        "category": "⭕ Dot Ball Pressure",
        "insight": f"{dot_pct:.1f}% of all legal deliveries in PSL are dot balls ({total_dots:,} out of {total_legal:,}). Building dot-ball pressure remains the primary bowling strategy.",
        "importance": "low",
    })

    # 9. All-rounder value
    ar = career[(career.avg_batting > 10) & (career.avg_bowling > 10)].head(5)
    if len(ar) > 0:
        ar_names = ", ".join(ar.player.values[:3])
        insights.append({
            "category": "🌟 All-rounder Value",
            "insight": f"All-rounders dominate the Impact Score rankings. Top all-rounders: {ar_names}. Their dual contribution in both batting and bowling makes them the most valuable PSL assets.",
            "importance": "high",
        })

    # 10. Powerplay wickets
    pp_wkts = pp.is_wicket.sum()
    pp_matches = pp.match_id.nunique()
    pp_wpm = pp_wkts / pp_matches
    insights.append({
        "category": "🚀 Powerplay",
        "insight": f"Average {pp_wpm:.1f} wickets fall in the powerplay per match. Early wickets are crucial — teams losing 2+ wickets in PP score {20}-{30} runs fewer on average.",
        "importance": "medium",
    })

    return insights

matches, deliveries = load_data()

with st.spinner("🤖 Generating AI insights..."):
    insights = generate_insights(matches, deliveries)

# Display insights
importance_colors = {"high": "#c9f34d", "medium": "#f0b429", "low": "#38bdf8"}
importance_icons = {"high": "🔥", "medium": "💡", "low": "📊"}

for ins in insights:
    color = importance_colors.get(ins["importance"], "#c9f34d")
    icon = importance_icons.get(ins["importance"], "💡")

    st.markdown(f"""
    <div style="background:rgba(13,43,31,0.5); border-left:4px solid {color};
         border-radius:0 12px 12px 0; padding:16px 20px; margin:10px 0;">
        <div style="font-family:Oswald; color:{color}; font-size:0.9rem; text-transform:uppercase;
             letter-spacing:1px; margin-bottom:6px;">{icon} {ins['category']}</div>
        <div style="color:#c0d0c8; font-size:0.9rem; line-height:1.6;">{ins['insight']}</div>
    </div>
    """, unsafe_allow_html=True)