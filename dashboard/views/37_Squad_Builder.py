"""
PSL Analytics — Squad Builder & AI Draft Assistant
Broadcast-style draft interface with player cards, tier badges,
role icons, price tags, phase coverage, and AI-powered pick recommendations.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.style import (
    inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT,
    TEAM_COLORS, fix_metrics,
)
from src.analytics.squad_builder import (
    SquadBuilder, PSL11_SQUADS, UNSOLD_POOL,
    TIER_COLORS, ROLE_ICONS, VENUE_CONDITIONS, TEAM_HOME_VENUES,
    PHASE_KEYWORDS,
)

inject_custom_css()
fix_metrics()

# ════════════════════════════════════════════════════════════
# CUSTOM CSS — Broadcast Draft Theme
# ════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700;800&family=Share+Tech+Mono&display=swap');

/* ── Draft Player Card ── */
.draft-card {
    background: linear-gradient(135deg, rgba(13, 43, 31, 0.8), rgba(6, 25, 18, 0.9));
    border: 1px solid rgba(201, 243, 77, 0.08);
    border-radius: 14px;
    padding: 16px;
    margin: 6px 0;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    animation: fadeUp 0.5s ease-out both;
}
.draft-card:hover {
    border-color: rgba(201, 243, 77, 0.3);
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
}
.draft-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 14px 14px 0 0;
}
.draft-card.tier-platinum::before { background: linear-gradient(90deg, #e02020, #ff4444); }
.draft-card.tier-diamond::before { background: linear-gradient(90deg, #2563eb, #60a5fa); }
.draft-card.tier-gold::before { background: linear-gradient(90deg, #f0b429, #fbbf24); }
.draft-card.tier-silver::before { background: linear-gradient(90deg, #6b7280, #9ca3af); }
.draft-card.tier-none::before { background: linear-gradient(90deg, rgba(201,243,77,0.3), rgba(201,243,77,0.1)); }

/* ── Player Name ── */
.player-name {
    font-family: 'Oswald', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
}

/* ── Tier Badge ── */
.tier-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-right: 6px;
}
.badge-platinum { background: rgba(224, 32, 32, 0.2); color: #ff6b6b; border: 1px solid rgba(224, 32, 32, 0.3); }
.badge-diamond  { background: rgba(37, 99, 235, 0.2); color: #60a5fa; border: 1px solid rgba(37, 99, 235, 0.3); }
.badge-gold     { background: rgba(240, 180, 41, 0.2); color: #fbbf24; border: 1px solid rgba(240, 180, 41, 0.3); }
.badge-silver   { background: rgba(107, 114, 128, 0.2); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.3); }

/* ── Role Chip ── */
.role-chip {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.7rem;
    color: #7aaa8f;
    background: rgba(201, 243, 77, 0.06);
    border: 1px solid rgba(201, 243, 77, 0.08);
}

/* ── Price Tag ── */
.price-tag {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #c9f34d, #f0b429);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ── Captain Badge ── */
.captain-badge {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 4px;
    font-size: 0.6rem;
    font-weight: 700;
    background: rgba(240, 180, 41, 0.15);
    color: #f0b429;
    border: 1px solid rgba(240, 180, 41, 0.3);
    letter-spacing: 1px;
    font-family: 'Oswald', sans-serif;
    text-transform: uppercase;
}

/* ── Photo Placeholder ── */
.player-photo {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(201, 243, 77, 0.1), rgba(240, 180, 41, 0.08));
    border: 2px solid rgba(201, 243, 77, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    flex-shrink: 0;
}

/* ── Section Panels ── */
.draft-section {
    background: rgba(13, 43, 31, 0.4);
    border: 1px solid rgba(201, 243, 77, 0.06);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
}
.draft-section-title {
    font-family: 'Oswald', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    color: #c9f34d;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(201, 243, 77, 0.08);
}

/* ── AI Recommendation Card ── */
.ai-rec-card {
    background: linear-gradient(135deg, rgba(201, 243, 77, 0.06), rgba(52, 211, 153, 0.04));
    border: 1px solid rgba(52, 211, 153, 0.15);
    border-radius: 12px;
    padding: 14px 16px;
    margin: 8px 0;
    position: relative;
}
.ai-rec-card .fit-score {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.4rem;
    font-weight: 700;
    color: #34d399;
}
.ai-rec-card .reasoning {
    font-size: 0.75rem;
    color: #5a8a6f;
    margin-top: 4px;
    font-style: italic;
}

/* ── Venue Condition Badge ── */
.venue-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 8px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    background: rgba(56, 189, 248, 0.1);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.2);
}

/* ── Overseas Indicator ── */
.overseas-flag {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.6rem;
    background: rgba(56, 189, 248, 0.1);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.15);
}

/* ── Score Bar ── */
.score-bar-bg {
    background: rgba(201, 243, 77, 0.06);
    border-radius: 4px;
    height: 8px;
    width: 100%;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.8s ease;
}

/* ── Phase Badge ── */
.phase-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.phase-strong { background: rgba(52, 211, 153, 0.12); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.2); }
.phase-adequate { background: rgba(251, 191, 36, 0.12); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.2); }
.phase-thin { background: rgba(248, 113, 113, 0.12); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.2); }
.phase-gap { background: rgba(248, 113, 113, 0.2); color: #fca5a5; border: 1px solid rgba(248, 113, 113, 0.3); }

/* ── Style DNA Card ── */
.dna-card {
    background: linear-gradient(135deg, rgba(192, 132, 252, 0.06), rgba(13, 43, 31, 0.5));
    border: 1px solid rgba(192, 132, 252, 0.12);
    border-radius: 12px;
    padding: 14px 16px;
}
</style>
""", unsafe_allow_html=True)

hero_card(
    "🏏 Squad Builder & AI Draft Assistant",
    "PSL 11 (2026) — First-ever player auction · Broadcast-style draft control room"
)

seam_divider()


# ════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════

def make_player_card(player: dict, show_score: bool = False, score_data: dict = None) -> str:
    """Generate HTML for a single broadcast-style player card."""
    name = player["name"]
    role = player.get("role", "")
    country = player.get("country", "")
    price = player.get("price", player.get("base"))
    tier = player.get("tier", "")
    captain = player.get("captain", False)
    specialty = player.get("specialty", "")
    is_overseas = country != "Pakistan"
    icon = ROLE_ICONS.get(role, "🏏")

    # Tier class
    tier_class = f"tier-{tier.lower()}" if tier else "tier-none"
    badge_class = f"badge-{tier.lower()}" if tier else ""
    tier_html = f'<span class="tier-badge {badge_class}">{tier}</span>' if tier else ""
    captain_html = '<span class="captain-badge">Captain</span>' if captain else ""
    overseas_html = f'<span class="overseas-flag">🌐 {country}</span>' if is_overseas else f'<span style="font-size:0.65rem; color:#5a8a6f;">🇵🇰 {country}</span>'

    price_display = f"{price:.2f} cr" if price is not None else "—"

    # Score section for AI recommendations
    score_html = ""
    if show_score and score_data:
        fit = score_data.get("fit_score", 0)
        reasoning = score_data.get("reasoning", "")
        bar_color = "#34d399" if fit >= 65 else "#f0b429" if fit >= 45 else "#f87171"
        score_html = f"""
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(201,243,77,0.06);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.7rem; color: #5a8a6f; text-transform: uppercase; letter-spacing: 1px;">AI Fit Score</span>
                <span class="fit-score">{fit:.0f}</span>
            </div>
            <div class="score-bar-bg" style="margin: 4px 0;">
                <div class="score-bar-fill" style="width: {min(fit, 100)}%; background: {bar_color};"></div>
            </div>
            <div class="reasoning">{reasoning}</div>
        </div>
        """

    return f"""
    <div class="draft-card {tier_class}">
        <div style="display: flex; gap: 14px; align-items: flex-start;">
            <div class="player-photo">{icon}</div>
            <div style="flex: 1; min-width: 0;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 4px;">
                    <div>
                        <div class="player-name">{name}</div>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 3px;">
                            {tier_html}{captain_html}{overseas_html}
                        </div>
                    </div>
                    <div class="price-tag">{price_display}</div>
                </div>
                <div style="margin-top: 6px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                    <span class="role-chip">{icon} {role}</span>
                    <span style="font-size: 0.7rem; color: #5a8a6f;">{specialty}</span>
                </div>
            </div>
        </div>
        {score_html}
    </div>
    """


def score_breakdown_chart(scores: dict) -> go.Figure:
    """Radar chart of AI scoring factors — 7 dimensions."""
    labels = ["Role Need", "Budget Fit", "Overseas", "Venue Match", "Value", "Phase Need", "Team Style"]
    keys = ["role_need", "budget_fit", "overseas_fit", "venue_match", "value_index", "phase_need", "team_style"]
    values = [scores.get(k, 0) for k in keys]
    values.append(values[0])  # close the polygon
    labels.append(labels[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=labels, fill="toself",
        fillcolor="rgba(52, 211, 153, 0.15)",
        line=dict(color="#34d399", width=2),
        marker=dict(size=6, color="#34d399"),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False,
                            gridcolor="rgba(201,243,77,0.06)"),
            angularaxis=dict(gridcolor="rgba(201,243,77,0.06)",
                             tickfont=dict(color="#7aaa8f", size=10)),
        ),
        showlegend=False,
        height=280,
    )
    return fig


# ════════════════════════════════════════════════════════════
# TEAM SELECTOR
# ════════════════════════════════════════════════════════════

team_names = list(PSL11_SQUADS.keys())
team_display = {name: f"{PSL11_SQUADS[name]['short']} — {name}" for name in team_names}

col_sel1, col_sel2 = st.columns([2, 1])
with col_sel1:
    selected_team = st.selectbox(
        "Select Franchise",
        team_names,
        format_func=lambda x: team_display[x],
    )
with col_sel2:
    view_mode = st.selectbox("View", ["Squad Overview", "AI Draft Assistant"])

builder = SquadBuilder(selected_team)
report = builder.generate_draft_report()
budget = report["budget"]
captain = builder.get_captain()

# ── Team Header ──
team_short = PSL11_SQUADS[selected_team]["short"]
captain_name = captain["name"] if captain else "TBD"
prefs = report.get("team_preferences", {})
st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(201,243,77,0.06), rgba(13,43,31,0.6));
     border: 1px solid rgba(201,243,77,0.1); border-radius: 16px;
     padding: 18px 24px; margin-bottom: 18px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div>
            <span style="font-family: 'Oswald', sans-serif; font-size: 1.6rem; font-weight: 800;
                  color: #fff; text-transform: uppercase; letter-spacing: 1px;">
                {selected_team}
            </span>
            <div style="font-size: 0.8rem; color: #5a8a6f; margin-top: 2px;">
                Captain: <b style="color:#c9f34d;">{captain_name}</b> · Home: {builder.home_venue()}
            </div>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span class="venue-badge">🏟️ {report['venue_conditions']['label']}</span>
            <span style="display:inline-block; padding:4px 12px; border-radius:8px; font-family:'Share Tech Mono'; font-size:0.75rem;
                  background:rgba(192,132,252,0.1); color:#c084fc; border:1px solid rgba(192,132,252,0.2);">
                🧬 {prefs.get('style', 'balanced').title()}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Row ──
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("💰 Total Purse", f"{budget['purse']:.1f} cr")
k2.metric("📉 Spent", f"{budget['spent']:.2f} cr")
k3.metric("📊 Remaining", f"{budget['remaining']:.2f} cr")
k4.metric("👥 Squad Size", budget["squad_size"])
k5.metric("👑 Retained", f"{len(builder.get_retained())} / 4")
k6.metric("🌐 Overseas", f"{builder.overseas_count()} / {builder.MAX_OVERSEAS_IN_SQUAD}")


# ════════════════════════════════════════════════════════════
# VIEW 1: SQUAD OVERVIEW
# ════════════════════════════════════════════════════════════

if view_mode == "Squad Overview":

    st.markdown("### 👑 Retained Players")
    retained = builder.get_retained()
    if retained:
        cols = st.columns(min(len(retained), 4))
        for i, p in enumerate(retained):
            with cols[i % 4]:
                st.markdown(make_player_card(p), unsafe_allow_html=True)
    else:
        st.info("No retained players for this team.")

    seam_divider()

    st.markdown("### 🎯 Auction Picks")
    auction = builder.get_auction_picks()
    # Sort by price descending (None at end)
    auction.sort(key=lambda x: (x.get("price") is None, -(x.get("price") or 0)))

    cols = st.columns(3)
    for i, p in enumerate(auction):
        with cols[i % 3]:
            st.markdown(make_player_card(p), unsafe_allow_html=True)

    seam_divider()

    # ── Analysis Row ──
    st.markdown("### 📊 Squad Composition Analysis")
    a1, a2, a3 = st.columns(3)

    with a1:
        # Role distribution pie
        rc = builder.role_counts()
        fig_role = go.Figure(go.Pie(
            labels=list(rc.keys()),
            values=list(rc.values()),
            hole=0.55,
            marker=dict(colors=["#c9f34d", "#f0b429", "#38bdf8", "#c084fc"]),
            textinfo="label+value",
            textfont=dict(size=12, color="#fff"),
        ))
        fig_role.update_layout(
            **PLOTLY_LAYOUT,
            title="Role Distribution",
            showlegend=False,
            height=300,
        )
        st.plotly_chart(fig_role, use_container_width=True)

    with a2:
        # Spend by role bar
        spend_role = builder.spend_by_role()
        fig_spend = go.Figure(go.Bar(
            x=list(spend_role.keys()),
            y=list(spend_role.values()),
            marker_color=["#c9f34d", "#f0b429", "#38bdf8", "#c084fc"][:len(spend_role)],
            text=[f"{v:.1f}" for v in spend_role.values()],
            textposition="outside",
            textfont=dict(color="#c9f34d", size=12, family="Share Tech Mono"),
        ))
        fig_spend.update_layout(
            **PLOTLY_LAYOUT,
            title="Spend by Role (cr)",
            height=300,
            yaxis_title="PKR Crores",
        )
        st.plotly_chart(fig_spend, use_container_width=True)

    with a3:
        # Price tier distribution
        tiers = builder.tier_distribution()
        tier_colors = ["#f0b429", "#38bdf8", "#c9f34d", "#5a8a6f"]
        fig_tier = go.Figure(go.Bar(
            x=list(tiers.keys()),
            y=list(tiers.values()),
            marker_color=tier_colors,
            text=list(tiers.values()),
            textposition="outside",
            textfont=dict(color="#c9f34d", size=13, family="Share Tech Mono"),
        ))
        fig_tier.update_layout(
            **PLOTLY_LAYOUT,
            title="Price Tiers",
            height=300,
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    seam_divider()

    # ── Phase Coverage + Bowling Balance + Intel Summary ──
    p1, p2 = st.columns([1, 1])

    with p1:
        # Phase Coverage Panel
        phase_cov = report["phase_coverage"]
        phase_html_items = ""
        for phase, info in phase_cov.items():
            strength = info["strength"]
            css_class = f"phase-{strength.lower()}"
            suffix = "" if info["count"] == 1 else "s"
            phase_html_items += (
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:8px 0;border-bottom:1px solid rgba(201,243,77,0.04);">'
                f'<div>'
                f'<div style="font-family:Oswald;font-size:0.85rem;color:#fff;text-transform:uppercase;">{phase.title()}</div>'
                f'<div style="font-size:0.7rem;color:#5a8a6f;margin-top:2px;">{info["count"]} specialist{suffix}</div>'
                f'</div>'
                f'<span class="phase-badge {css_class}">{strength}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="draft-section">'
            f'<div class="draft-section-title">📋 Phase Coverage</div>'
            f'{phase_html_items}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Bowling Balance
        balance = report["bowling_balance"]
        venue_label = report["venue_conditions"]["label"]
        pace_pct = f"{report['venue_conditions']['pace']:.0%}"
        spin_pct = f"{report['venue_conditions']['spin']:.0%}"
        st.markdown(
            f'<div class="draft-section">'
            f'<div class="draft-section-title">⚡ Bowling Attack Balance</div>'
            f'<div style="display:flex;gap:20px;justify-content:center;padding:10px 0;">'
            f'<div style="text-align:center;">'
            f'<div style="font-family:Share Tech Mono;font-size:2rem;color:#f0b429;">{balance["pace"]}</div>'
            f'<div style="font-size:0.7rem;color:#5a8a6f;text-transform:uppercase;letter-spacing:1px;">Pace</div>'
            f'</div>'
            f'<div style="font-size:1.5rem;color:#294438;align-self:center;">vs</div>'
            f'<div style="text-align:center;">'
            f'<div style="font-family:Share Tech Mono;font-size:2rem;color:#38bdf8;">{balance["spin"]}</div>'
            f'<div style="font-size:0.7rem;color:#5a8a6f;text-transform:uppercase;letter-spacing:1px;">Spin</div>'
            f'</div>'
            f'</div>'
            f'<div style="font-size:0.75rem;color:#5a8a6f;text-align:center;margin-top:6px;">'
            f'Home venue: {venue_label} (Pace {pace_pct} · Spin {spin_pct})'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with p2:
        # Franchise DNA
        desc = prefs.get("description", "Standard balanced approach")
        youth_label = "🌱 Youth" if prefs.get("prefers_youth") else "🏛️ Experience"
        style_label = prefs.get("style", "balanced").title()
        st.markdown(
            f'<div class="dna-card" style="margin-bottom:16px;">'
            f'<div style="font-family:Oswald;font-size:0.8rem;color:#c084fc;'
            f'text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;">🧬 Franchise DNA</div>'
            f'<div style="font-size:0.8rem;color:#7aaa8f;line-height:1.6;">{desc}</div>'
            f'<div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">'
            f'<span style="font-size:0.6rem;padding:2px 8px;border-radius:4px;'
            f'background:rgba(192,132,252,0.1);color:#c084fc;border:1px solid rgba(192,132,252,0.15);">'
            f'{youth_label}-first</span>'
            f'<span style="font-size:0.6rem;padding:2px 8px;border-radius:4px;'
            f'background:rgba(192,132,252,0.1);color:#c084fc;border:1px solid rgba(192,132,252,0.15);">'
            f'Style: {style_label}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Draft Intelligence Summary
        strengths_html = ''.join(f'<div style="font-size:0.78rem;color:#7aaa8f;padding:2px 0;">• {s}</div>' for s in report['strengths'])
        weaknesses_html = ''.join(f'<div style="font-size:0.78rem;color:#7aaa8f;padding:2px 0;">• {w}</div>' for w in report['weaknesses'])
        st.markdown(
            f'<div class="draft-section">'
            f'<div class="draft-section-title">📋 Draft Intelligence Summary</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'
            f'<div>'
            f'<div style="font-size:0.7rem;color:#34d399;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">✅ Strengths</div>'
            f'{strengths_html}'
            f'</div>'
            f'<div>'
            f'<div style="font-size:0.7rem;color:#f87171;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">⚠️ Weaknesses</div>'
            f'{weaknesses_html}'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════
# VIEW 2: AI DRAFT ASSISTANT
# ════════════════════════════════════════════════════════════

elif view_mode == "AI Draft Assistant":

    st.markdown("### 🤖 AI Draft Assistant")
    st.markdown(
        '<div style="font-size:0.8rem;color:#5a8a6f;margin-bottom:16px;">'
        'AI scores each available player across 7 dimensions — role gaps, budget, '
        'overseas slots, home venue conditions, value for money, phase coverage needs, '
        'and franchise DNA alignment.</div>',
        unsafe_allow_html=True,
    )

    # ── Gap Analysis ──
    gaps = report["role_gaps"]
    gap_cols = st.columns(4)
    for i, (role, info) in enumerate(gaps.items()):
        with gap_cols[i]:
            status = info["status"]
            if status == "SHORT":
                color = "#f87171"
                label = f"NEED {info['deficit']} MORE"
                bg = "rgba(248, 113, 113, 0.08)"
            elif status == "EXCESS":
                color = "#fbbf24"
                label = f"{info['surplus']} EXCESS"
                bg = "rgba(251, 191, 36, 0.08)"
            else:
                color = "#34d399"
                label = "BALANCED"
                bg = "rgba(52, 211, 153, 0.08)"
            icon = ROLE_ICONS.get(role, "🏏")
            st.markdown(
                f'<div style="background:{bg};border:1px solid {color}33;border-radius:10px;padding:12px;text-align:center;">'
                f'<div style="font-size:1.3rem;">{icon}</div>'
                f'<div style="font-family:Oswald;font-size:0.85rem;color:#fff;text-transform:uppercase;margin:4px 0;">{role}s</div>'
                f'<div style="font-family:Share Tech Mono;font-size:1.3rem;color:{color};">{info["current"]}</div>'
                f'<div style="font-size:0.65rem;color:{color};text-transform:uppercase;letter-spacing:1px;margin-top:2px;">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    seam_divider()

    # ── Phase Coverage Mini ──
    phase_cov = report["phase_coverage"]
    pc1, pc2, pc3 = st.columns(3)
    for col_widget, (phase, info) in zip([pc1, pc2, pc3], phase_cov.items()):
        with col_widget:
            strength = info["strength"]
            color = {"Strong": "#34d399", "Adequate": "#fbbf24", "Thin": "#f87171", "Gap": "#fca5a5"}.get(strength, "#5a8a6f")
            st.markdown(
                f'<div style="background:rgba(13,43,31,0.5);border:1px solid {color}22;border-radius:10px;padding:10px;text-align:center;">'
                f'<div style="font-family:Oswald;font-size:0.75rem;color:#fff;text-transform:uppercase;letter-spacing:1px;">{phase.title()} Phase</div>'
                f'<div style="font-family:Share Tech Mono;font-size:1.1rem;color:{color};margin-top:4px;">{info["count"]} specialists</div>'
                f'<div style="font-size:0.6rem;color:{color};margin-top:2px;">{strength.upper()}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    seam_divider()

    # ── Recommendations ──
    recs = report["recommendations"]

    weak_role = builder.weakest_role()
    weak_phase = builder.weakest_phase().title()
    st.markdown(
        f'<div style="margin-bottom:12px;">'
        f'<span style="font-family:Oswald;font-size:1rem;color:#c9f34d;text-transform:uppercase;letter-spacing:1px;">'
        f'🎯 Top {len(recs)} Recommended Picks from Unsold Pool</span>'
        f'<span style="font-size:0.75rem;color:#5a8a6f;margin-left:8px;">'
        f'Weakest role: <b style="color:#f0b429;">{weak_role}</b>'
        f' · Weakest phase: <b style="color:#f0b429;">{weak_phase}</b></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not recs:
        st.warning("No suitable candidates found in the unsold pool for this team's needs.")
    else:
        for i, rec in enumerate(recs):
            r1, r2 = st.columns([2, 1])
            with r1:
                st.markdown(make_player_card(
                    rec, show_score=True,
                    score_data={"fit_score": rec["fit_score"], "reasoning": rec["reasoning"]},
                ), unsafe_allow_html=True)
            with r2:
                fig = score_breakdown_chart(rec["scores"])
                st.plotly_chart(fig, use_container_width=True)

    seam_divider()

    # ── Full Auction Pool ──
    st.markdown("### 📋 Full Auction Player Pool")

    # Score from auction pool TSV
    pool = builder._load_auction_pool()
    scored = []
    for p in pool[:200]:  # Top 200 for performance
        s = builder.score_candidate(p)
        name = p.get("name", p.get("Full_Name", p.get("Full Name", "")))
        role = p.get("role", p.get("Player_Role", p.get("Player Role", "")))
        country = p.get("country", p.get("Country", ""))
        base = p.get("base", p.get("Base_Price", p.get("Base Price", 0)))
        if isinstance(base, str): base = float(base.replace(",", "")) / 10000000
        elif base and base > 1000: base = base / 10000000
        if not name: continue
        scored.append({
            "Name": name, "Role": role, "Country": country,
            "Base Price": f"{base:.2f} cr" if base else "—",
            "Fit Score": s["total"], "Role Need": s["role_need"],
            "Budget": s["budget_fit"], "Overseas": s["overseas_fit"],
            "Venue": s["venue_match"], "Value": s["value_index"],
            "Phase": s["phase_need"], "Style": s["team_style"],
        })
    if scored:
        scored_df = pd.DataFrame(scored).sort_values("Fit Score", ascending=False)
        st.dataframe(scored_df, use_container_width=True, hide_index=True)
    else:
        st.info("Auction pool data not found. Place psl11_auction_pool.tsv in the data/ folder.")

    # ── Cross-Team Comparison ──
    seam_divider()
    st.markdown("### 🔄 Cross-Team Gap Comparison")

    comp_data = []
    for tname in PSL11_SQUADS:
        b = SquadBuilder(tname)
        rc = b.role_counts()
        comp_data.append({
            "Team": PSL11_SQUADS[tname]["short"],
            "Batters": rc.get("Batter", 0),
            "Bowlers": rc.get("Bowler", 0),
            "All-rounders": rc.get("All-rounder", 0),
            "Keepers": rc.get("Wicketkeeper", 0),
            "Overseas": b.overseas_count(),
            "Budget Left": b.budget_analysis()["remaining"],
        })
    comp_df = pd.DataFrame(comp_data)

    fig_comp = go.Figure()
    colors = {"Batters": "#c9f34d", "Bowlers": "#f0b429", "All-rounders": "#38bdf8", "Keepers": "#c084fc"}
    for role, color in colors.items():
        fig_comp.add_trace(go.Bar(
            name=role, x=comp_df["Team"], y=comp_df[role],
            marker_color=color, opacity=0.85,
        ))
    fig_comp.update_layout(
        **PLOTLY_LAYOUT,
        title="Role Distribution Across All Franchises",
        barmode="group",
        height=350,
    )
    st.plotly_chart(fig_comp, use_container_width=True)


# ── Footer ──
st.markdown("---")
st.caption(
    "Squad data from PSL 11's first-ever player auction (Feb 11, 2026, Lahore) "
    "and confirmed squad announcements. A few late additions have no confirmed "
    "price (shown as '—'). AI recommendations use a 7-factor weighted scoring model "
    "(role need, budget, overseas, venue, value, phase coverage, franchise DNA) — "
    "not a guarantee of pick quality."
)