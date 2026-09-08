"""PSL Analytics — Coach Room: PSL 12 Auction War Room"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.style import inject_custom_css, hero_card, seam_divider, PLOTLY_LAYOUT, fix_metrics
from src.analytics.retention_engine import (
    calculate_worth, find_alternatives, all_teams_summary,
    PROJECTED_PURSE, PLAYER_PROFILES, ROLE_LABELS, MAX_OVERSEAS_RETAIN,
)
from src.analytics.squad_builder import PSL11_SQUADS, RISING_STARS

inject_custom_css()
fix_metrics()

hero_card("🧠 Coach Room — PSL 12 Auction Planner",
          "Your squad · Player worth · Retain/release · Find replacements · Plan auction")
seam_divider()

# ════════════════════════════════════════════════════════════
# TEAM SELECTION
# ════════════════════════════════════════════════════════════

team_sel = st.selectbox("🏏 You are the Head Coach of:", list(PSL11_SQUADS.keys()))
squad = PSL11_SQUADS[team_sel]

# Build full worth data for every player
squad_worth = []
for p in squad["players"]:
    w = calculate_worth(p["name"], p.get("price"))
    is_ov = p["country"] != "Pakistan"
    squad_worth.append({**p, **w, "is_overseas": is_ov})

squad_worth.sort(key=lambda x: -x["retention_score"])

# ════════════════════════════════════════════════════════════
# SECTION 1: YOUR SQUAD — Pick who to retain
# ════════════════════════════════════════════════════════════

st.markdown("### 1️⃣ Your PSL 11 Squad — Select Up To 4 Retentions")

player_names = [p["name"] for p in squad_worth]
# Default: top 4 by retention score (respecting 1 overseas max)
default_retain = []
ov_count = 0
for p in squad_worth:
    if len(default_retain) >= 4:
        break
    if p["is_overseas"] and ov_count >= MAX_OVERSEAS_RETAIN:
        continue
    default_retain.append(p["name"])
    if p["is_overseas"]:
        ov_count += 1

chosen = st.multiselect(
    "Pick up to 4 players to retain (max 1 overseas):",
    player_names,
    default=default_retain,
    max_selections=4,
)

# Validate overseas constraint
chosen_data = [p for p in squad_worth if p["name"] in chosen]
overseas_chosen = sum(1 for p in chosen_data if p["is_overseas"])
if overseas_chosen > MAX_OVERSEAS_RETAIN:
    st.error(f"⚠️ You selected {overseas_chosen} overseas players — max allowed is {MAX_OVERSEAS_RETAIN}. Remove one overseas player.")

# Calculate budget
retain_cost = round(sum(p["market_value"] for p in chosen_data), 2)
purse_left = round(PROJECTED_PURSE - retain_cost, 2)

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("🔒 Retaining", f"{len(chosen)} / 4")
k2.metric("💸 Retention Cost", f"{retain_cost:.2f} cr")
k3.metric("💰 Auction Purse", f"{purse_left:.2f} cr")
k4.metric("🌐 Overseas Kept", f"{overseas_chosen} / {MAX_OVERSEAS_RETAIN}")

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 2: SQUAD TABLE — worth, verdict, retain status
# ════════════════════════════════════════════════════════════

st.markdown("### 2️⃣ Full Squad Worth Report")

rows = []
for p in squad_worth:
    flag = "🌐" if p["is_overseas"] else "🇵🇰"
    status = "🔒 RETAINED" if p["name"] in chosen else "📤 RELEASED"
    star = "⭐" if p.get("is_rising_star") else ""
    captain = " (C)" if any(x.get("captain") and x["name"] == p["name"] for x in squad["players"]) else ""
    rows.append({
        "Status": status,
        "Player": f"{p['name']}{captain} {star}",
        "": flag,
        "Age": p["age"],
        "Role": p["role_label"],
        "Phase": p["phase"].title(),
        "Form": f"{p['form']}/10",
        "Pedigree": p["pedigree"].title(),
        "Caps": p["caps"],
        "PSL 11 Price": f"{p['base_price']:.2f}" if p.get("base_price") else "—",
        "Market Value": f"{p['market_value']:.2f}",
        "Verdict": p["verdict"],
        "Advice": p["retain_advice"],
        "Score": p["retention_score"],
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True, height=500)

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 3: PLAYER DEEP DIVE — worth breakdown + alternatives
# ════════════════════════════════════════════════════════════

st.markdown("### 3️⃣ Player Deep Dive — Worth Breakdown & Cheaper Alternatives")

dive_player = st.selectbox("Select a player to analyze:", player_names, key="dive")
dp = next(p for p in squad_worth if p["name"] == dive_player)

c1, c2 = st.columns([1, 1])

with c1:
    flag = "🌐 Overseas" if dp["is_overseas"] else "🇵🇰 Pakistan"
    star = "⭐ Rising Star" if dp.get("is_rising_star") else ""
    price_disp = f"{dp['base_price']:.2f} cr" if dp.get("base_price") else "Unpriced"

    st.markdown(f"**{dp['name']}** — {flag} {star}")
    st.markdown(f"Age **{dp['age']}** · **{dp['role_label']}** · {dp['phase'].title()} phase · {dp['pedigree'].title()} · {dp['caps']} T20I caps")

    m1, m2, m3 = st.columns(3)
    m1.metric("PSL 11 Price", price_disp)
    m2.metric("Market Value", f"{dp['market_value']:.2f} cr")
    m3.metric("Form", f"{dp['form']}/10")

    st.markdown(f"**Verdict:** {dp['verdict']}")
    st.markdown(f"**Coach Advice:** {dp['retain_advice']}")
    st.markdown(f"**Retention Score:** {dp['retention_score']:.0f}/100")

    factors = dp.get("factors", {})
    if factors:
        st.markdown("**Value Factors:**")
        factor_text = (
            f"Age factor: **{factors.get('age', 1):.2f}x** · "
            f"Role scarcity: **{factors.get('scarcity', 1):.2f}x** · "
            f"Pedigree: **{factors.get('pedigree', 1):.2f}x** · "
            f"Form: **{factors.get('form', 1):.3f}x**"
        )
        if factors.get("rising_star"):
            factor_text += " · Rising star: **1.15x**"
        st.markdown(factor_text)

with c2:
    # Radar chart
    fct = dp.get("factors", {})
    if fct and "age" in fct:
        labels = ["Age", "Scarcity", "Pedigree", "Form", "Youth Bonus"]
        vals = [
            fct.get("age", 1) * 50,
            fct.get("scarcity", 1) * 50,
            fct.get("pedigree", 1) * 45,
            fct.get("form", 1) * 55,
            70 if fct.get("rising_star") else 30,
        ]
        vals.append(vals[0])
        labels.append(labels[0])
        fig = go.Figure(go.Scatterpolar(r=vals, theta=labels, fill="toself",
            fillcolor="rgba(201,243,77,0.12)", line=dict(color="#c9f34d", width=2),
            marker=dict(size=6, color="#c9f34d")))
        fig.update_layout(**PLOTLY_LAYOUT, polar=dict(bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False,
                gridcolor="rgba(201,243,77,0.06)"),
            angularaxis=dict(gridcolor="rgba(201,243,77,0.06)",
                tickfont=dict(color="#7aaa8f", size=10))),
            showlegend=False, height=280)
        st.plotly_chart(fig, use_container_width=True)

# Cheaper alternatives
st.markdown(f"#### 🔄 Cheaper Alternatives for {dive_player}")
alts = find_alternatives(dive_player, team_sel, top_n=8)
if alts:
    alt_df = pd.DataFrame([{
        "Player": a["name"], "Country": a["country"], "Role": a["role"],
        "Bowling": a["bowling"], "Base Price": f"{a['base_price']:.2f} cr",
        "You Save": f"{a['savings']:.2f} cr",
    } for a in alts])
    st.dataframe(alt_df, use_container_width=True, hide_index=True)
else:
    st.info(f"No cheaper alternatives found for {dp['role_label']} in the auction pool. This player's role is rare — consider retaining.")

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 4: RELEASED PLAYERS — who goes to auction
# ════════════════════════════════════════════════════════════

released = [p for p in squad_worth if p["name"] not in chosen]
if released:
    st.markdown("### 4️⃣ Released Players — Entering PSL 12 Auction Pool")
    st.markdown(f"*{len(released)} players released. Strong ones are buy-back targets at auction.*")

    rel_rows = []
    for p in released:
        flag = "🌐" if p["is_overseas"] else "🇵🇰"
        buyback = "🎯 Buy-back target" if p["retention_score"] >= 50 else ""
        rel_rows.append({
            "Player": p["name"],
            "": flag,
            "Role": p["role_label"],
            "Age": p["age"],
            "Form": f"{p['form']}/10",
            "Market Value": f"{p['market_value']:.2f} cr",
            "Score": p["retention_score"],
            "Note": buyback,
        })
    st.dataframe(pd.DataFrame(rel_rows), use_container_width=True, hide_index=True)

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 5: AUCTION GAPS — what your squad needs
# ════════════════════════════════════════════════════════════

st.markdown("### 5️⃣ Auction Shopping List — Gaps After Retention")

# Count roles in retained squad
retained_roles = {}
for p in chosen_data:
    r = p["role"]
    retained_roles[r] = retained_roles.get(r, 0) + 1

ideal = {"Batter": 4, "Bowler": 5, "All-rounder": 2, "Wicketkeeper": 1}
needs = []
for role, need in ideal.items():
    have = retained_roles.get(role, 0)
    gap = max(0, need - have)
    if gap > 0:
        needs.append({"Role": role, "Need": need, "Retained": have, "To Buy": gap})

if needs:
    st.dataframe(pd.DataFrame(needs), use_container_width=True, hide_index=True)
else:
    st.success("Your retained core covers the basic composition — fill depth at auction.")

st.markdown(f"**Auction budget: {purse_left:.2f} cr** for ~{18 - len(chosen)} remaining squad spots")
if purse_left > 0 and (18 - len(chosen)) > 0:
    avg = purse_left / (18 - len(chosen))
    st.markdown(f"Average available per player: **{avg:.2f} cr**")

seam_divider()

# ════════════════════════════════════════════════════════════
# SECTION 6: RIVAL INTEL — what other teams are retaining
# ════════════════════════════════════════════════════════════

st.markdown("### 6️⃣ Rival Intel — Other Teams' Probable Retentions")
st.markdown("*Know who's available at auction and who's locked in.*")

all_res = all_teams_summary()
rival_rows = []
for r in all_res:
    rets = r["retentions"]
    ret_names = [ret["name"] for ret in rets]
    ov_name = next((ret["name"] for ret in rets if ret["is_overseas"]), "—")
    rival_rows.append({
        "Team": r["short"],
        "Ret 1": f"{ret_names[0]} ({rets[0]['retention_price']:.1f})" if len(ret_names) > 0 else "—",
        "Ret 2": f"{ret_names[1]} ({rets[1]['retention_price']:.1f})" if len(ret_names) > 1 else "—",
        "Ret 3": f"{ret_names[2]} ({rets[2]['retention_price']:.1f})" if len(ret_names) > 2 else "—",
        "Ret 4": f"{ret_names[3]} ({rets[3]['retention_price']:.1f})" if len(ret_names) > 3 else "—",
        "🌐": ov_name,
        "Cost": f"{r['cost']:.1f}",
        "Purse Left": f"{r['purse_left']:.1f}",
    })
st.dataframe(pd.DataFrame(rival_rows), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Coach Room: PSL 12 mock auction planner. Worth model uses age, role scarcity, form, pedigree, rising star bonus. "
           "Retention at market value. 903-player auction pool. Projected purse 50 cr.")
