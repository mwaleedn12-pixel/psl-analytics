"""PSL Analytics — Franchise War Room (PSL 12 Preparation)"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, fix_metrics
from src.analytics.retention_engine import (
    calculate_worth, find_alternatives, predict_retentions, all_teams_summary,
    PROJECTED_PURSE, PLAYER_PROFILES, ROLE_LABELS,
)
from src.analytics.squad_builder import PSL11_SQUADS

inject_custom_css()
fix_metrics()

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700;800&family=Share+Tech+Mono&display=swap');
.wc{background:linear-gradient(135deg,rgba(13,43,31,0.8),rgba(6,25,18,0.9));border-radius:14px;padding:16px;margin:6px 0;position:relative;overflow:hidden;border:1px solid rgba(201,243,77,0.06);}
.wc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:14px 14px 0 0;}
.wc-retain::before{background:linear-gradient(90deg,#34d399,#a3e635);}
.wc-release::before{background:linear-gradient(90deg,#f87171,#fbbf24);}
.mv{font-family:'Share Tech Mono',monospace;font-size:1.3rem;font-weight:700;background:linear-gradient(135deg,#c9f34d,#f0b429);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.tag{display:inline-block;padding:2px 8px;border-radius:6px;font-size:0.6rem;font-weight:600;letter-spacing:0.5px;margin-right:4px;}
.t-retain{background:rgba(52,211,153,0.12);color:#34d399;border:1px solid rgba(52,211,153,0.2);}
.t-release{background:rgba(248,113,113,0.12);color:#f87171;border:1px solid rgba(248,113,113,0.2);}
.t-star{background:rgba(251,191,36,0.12);color:#fbbf24;border:1px solid rgba(251,191,36,0.2);}
.t-consider{background:rgba(56,189,248,0.12);color:#38bdf8;border:1px solid rgba(56,189,248,0.2);}
</style>""", unsafe_allow_html=True)

hero_card("🏟️ Franchise War Room — PSL 12 Preparation", "Retain · Release · Find Cheaper Alternatives · Plan Auction Strategy")
seam_divider()

team_sel = st.selectbox("🏏 Select Your Franchise", list(PSL11_SQUADS.keys()))
pred = predict_retentions(team_sel)

# ── KPIs ──
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Projected Purse", f"{PROJECTED_PURSE:.0f} cr")
k2.metric("🔒 Retention Cost", f"{pred['cost']:.2f} cr")
k3.metric("📊 Auction Purse Left", f"{pred['purse_left']:.2f} cr")
k4.metric("👥 Squad Size", len(PSL11_SQUADS[team_sel]["players"]))
k5.metric("🌐 Overseas Retained", f"{pred['overseas_retained']} / 1")

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 1: FULL SQUAD ANALYSIS
# ════════════════════════════════════════════════════════════

st.markdown("### 📋 Squad Analysis — Every Player's Worth & Verdict")
st.markdown('<div style="font-size:0.78rem;color:#5a8a6f;margin-bottom:12px;">Each player scored on market value, form, age, role scarcity, pedigree. Sorted by retention priority — top 4 are predicted retentions.</div>', unsafe_allow_html=True)

all_players = []
for p in PSL11_SQUADS[team_sel]["players"]:
    w = calculate_worth(p["name"], p.get("price"))
    all_players.append(w)
all_players.sort(key=lambda x: -x["retention_score"])

retained_names = {r["name"] for r in pred["retentions"]}

for idx, pl in enumerate(all_players):
    is_retained = pl["name"] in retained_names
    card_class = "wc-retain" if is_retained else "wc-release"
    if pl["retention_score"] >= 60:
        advice_class = "t-retain"
    elif pl["retention_score"] >= 40:
        advice_class = "t-consider"
    else:
        advice_class = "t-release"

    flag = "🌐" if pl["name"] in [p["name"] for p in PSL11_SQUADS[team_sel]["players"] if p["country"] != "Pakistan"] else "🇵🇰"
    star_tag = '<span class="tag t-star">⭐ RISING STAR</span>' if pl.get("is_rising_star") else ""
    retained_tag = '<span class="tag t-retain" style="font-size:0.65rem;">🔒 RETAINED</span>' if is_retained else ""
    price_display = f"{pl['base_price']:.2f} cr" if pl.get("base_price") else "—"
    cap_badge = " (C)" if any(p.get("captain") and p["name"] == pl["name"] for p in PSL11_SQUADS[team_sel]["players"]) else ""

    bar_w = min(pl["retention_score"], 100)
    bar_color = "#34d399" if bar_w >= 60 else "#fbbf24" if bar_w >= 40 else "#f87171"

    st.markdown(
        f'<div class="wc {card_class}">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">'
        f'<div style="flex:1;min-width:200px;">'
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">'
        f'<span style="font-family:Oswald;font-size:1.05rem;font-weight:700;color:#fff;text-transform:uppercase;">{pl["name"]}{cap_badge}</span>'
        f'{retained_tag}{star_tag}'
        f'</div>'
        f'<div style="font-size:0.7rem;color:#5a8a6f;margin:3px 0;">{flag} Age {pl["age"]} · {pl["role_label"]} · {pl["phase"].title()} phase · {pl["pedigree"].title()} · {pl["caps"]} T20I caps</div>'
        f'<div style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap;align-items:center;">'
        f'<span class="tag {advice_class}">{pl["retain_advice"]}</span>'
        f'<span style="font-size:0.6rem;color:#5a8a6f;">Form {pl["form"]}/10 · {pl["verdict"]}</span>'
        f'</div>'
        f'</div>'
        f'<div style="text-align:right;min-width:160px;">'
        f'<div style="font-size:0.55rem;color:#5a8a6f;text-transform:uppercase;letter-spacing:1px;">PSL 11 → Market Value</div>'
        f'<div style="display:flex;gap:8px;justify-content:flex-end;align-items:baseline;">'
        f'<span style="font-family:Share Tech Mono;font-size:0.9rem;color:#9ca3af;text-decoration:line-through;">{price_display}</span>'
        f'<span class="mv">{pl["market_value"]:.2f} cr</span>'
        f'</div>'
        f'<div style="font-size:0.6rem;color:{bar_color};margin-top:4px;">Retention Score: {pl["retention_score"]:.0f}/100</div>'
        f'<div style="background:rgba(201,243,77,0.06);border-radius:3px;height:6px;width:120px;margin-top:2px;margin-left:auto;">'
        f'<div style="height:100%;width:{bar_w}%;background:{bar_color};border-radius:3px;"></div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 2: RETENTION SUMMARY (price-based)
# ════════════════════════════════════════════════════════════

st.markdown("### 🔒 Predicted PSL 12 Retentions")
st.markdown(f'<div style="font-size:0.78rem;color:#5a8a6f;margin-bottom:12px;">Top 4 players retained at market value. Max 1 overseas. Total retention cost deducted from {PROJECTED_PURSE:.0f} cr purse.</div>', unsafe_allow_html=True)

cols = st.columns(4)
for i, ret in enumerate(pred["retentions"]):
    flag = "🌐" if ret["is_overseas"] else "🇵🇰"
    with cols[i]:
        st.markdown(
            f'<div class="wc wc-retain">'
            f'<div style="font-family:Share Tech Mono;font-size:0.7rem;color:#34d399;letter-spacing:1px;">RETENTION #{i+1}</div>'
            f'<div style="font-family:Oswald;font-size:1rem;font-weight:700;color:#fff;margin:6px 0 2px;text-transform:uppercase;">{ret["name"]}</div>'
            f'<div style="font-size:0.65rem;color:#5a8a6f;">{flag} {ret["role_label"]} · Age {ret["age"]}</div>'
            f'<div style="margin-top:10px;">'
            f'<div style="font-size:0.5rem;color:#5a8a6f;text-transform:uppercase;">Retention Price</div>'
            f'<span class="mv" style="font-size:1.2rem;">{ret["retention_price"]:.2f} cr</span>'
            f'</div>'
            f'<div style="font-size:0.6rem;color:#5a8a6f;margin-top:6px;">Form {ret["form"]}/10 · Score {ret["retention_score"]:.0f}/100</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 3: CHEAPER ALTERNATIVES
# ════════════════════════════════════════════════════════════

st.markdown("### 🔄 Cheaper Alternatives — Auction Pool")
st.markdown('<div style="font-size:0.78rem;color:#5a8a6f;margin-bottom:12px;">Select a player to release → find cheaper options from the 903-player auction pool who play the same role.</div>', unsafe_allow_html=True)

release_candidates = [p for p in all_players if p["retention_score"] < 70]
if release_candidates:
    alt_player = st.selectbox(
        "Find alternatives for:",
        [p["name"] for p in release_candidates],
        format_func=lambda n: f"{n} — MV {next(p['market_value'] for p in release_candidates if p['name']==n):.2f} cr, {next(p['role_label'] for p in release_candidates if p['name']==n)}",
    )
    if alt_player:
        alts = find_alternatives(alt_player, team_sel, top_n=8)
        sel_w = next(p for p in release_candidates if p["name"] == alt_player)

        st.markdown(
            f'<div style="font-size:0.8rem;color:#5a8a6f;margin-bottom:8px;">'
            f'Releasing <b style="color:#f87171;">{alt_player}</b> (MV {sel_w["market_value"]:.2f} cr, {sel_w["role_label"]}, {sel_w["phase"].title()}) — '
            f'{len(alts)} cheaper alternatives:</div>',
            unsafe_allow_html=True,
        )
        if alts:
            st.dataframe(pd.DataFrame([{
                "Player": a["name"], "Country": a["country"], "Role": a["role"],
                "Bowling": a["bowling"], "Base Price": f"{a['base_price']:.2f} cr",
                "You Save": f"{a['savings']:.2f} cr",
            } for a in alts]), use_container_width=True, hide_index=True)
        else:
            st.info("No cheaper alternatives found for this player's role in the auction pool.")
else:
    st.success("All players have strong retention scores — no obvious release candidates!")

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 4: BUYBACK TARGETS
# ════════════════════════════════════════════════════════════

if pred["buybacks"]:
    st.markdown("### 🎯 Buy-Back Targets at Auction")
    st.markdown('<div style="font-size:0.78rem;color:#5a8a6f;margin-bottom:12px;">Strong players who didn\'t make the 4 retention slots — chase them at auction.</div>', unsafe_allow_html=True)
    for bb in pred["buybacks"]:
        flag = "🌐" if bb.get("is_overseas") else "🇵🇰"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:10px 14px;'
            f'background:rgba(13,43,31,0.4);border:1px solid rgba(201,243,77,0.06);border-radius:10px;margin:4px 0;align-items:center;">'
            f'<div><span style="font-weight:700;color:#fff;">{bb["name"]}</span>'
            f' <span style="font-size:0.7rem;color:#5a8a6f;">· {flag} {bb["role"]} · Age {bb["age"]} · Form {bb["form"]}/10</span></div>'
            f'<div style="font-family:Share Tech Mono;color:#f0b429;font-weight:700;">{bb["market_value"]:.2f} cr</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 5: ALL-TEAMS OVERVIEW
# ════════════════════════════════════════════════════════════

st.markdown("### 📊 All-Teams Retention Comparison")
all_res = all_teams_summary()

rows = []
for r in all_res:
    rets = r["retentions"]
    ret_names = [ret["name"] for ret in rets]
    ov_name = next((ret["name"] for ret in rets if ret["is_overseas"]), "—")
    rows.append({
        "Team": r["short"],
        "Ret 1": ret_names[0] if len(ret_names) > 0 else "—",
        "Ret 2": ret_names[1] if len(ret_names) > 1 else "—",
        "Ret 3": ret_names[2] if len(ret_names) > 2 else "—",
        "Ret 4": ret_names[3] if len(ret_names) > 3 else "—",
        "🌐": ov_name,
        "Cost": f"{r['cost']:.2f} cr",
        "Purse Left": f"{r['purse_left']:.2f} cr",
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# Value chart
teams_x = [r["short"] for r in all_res]
mv_vals = [round(sum(ret["retention_price"] for ret in r["retentions"]), 2) for r in all_res]

fig = go.Figure(go.Bar(x=teams_x, y=mv_vals, marker_color="#c9f34d",
    text=[f"{v:.0f}" for v in mv_vals], textposition="outside",
    textfont=dict(color="#c9f34d", size=12, family="Share Tech Mono")))
fig.update_layout(**PLOTLY_LAYOUT, title="Total Retention Cost by Franchise (cr)", height=350)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Players retained at market value (no fixed tiers). Worth model: age × role scarcity × pedigree × form × rising star bonus. "
           "Auction pool: 903 registered players. Projected PSL 12 purse: 50 cr.")