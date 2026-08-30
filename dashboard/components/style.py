"""
PSL Analytics — Stadium-Themed Premium Dashboard
Dark emerald green, floodlight glows, cricket ball seam dividers,
team jersey colors, animated charts.
"""

import streamlit as st

# ════════════════════════════════════════════════════════════
# PSL TEAM COLORS (from jersey images)
# ════════════════════════════════════════════════════════════
TEAM_COLORS = {
    "Islamabad United":    {"primary": "#e02020", "secondary": "#1a1a1a", "accent": "#ff4444"},
    "Karachi Kings":       {"primary": "#1a237e", "secondary": "#c62828", "accent": "#3949ab"},
    "Lahore Qalandars":    {"primary": "#76ff03", "secondary": "#1b5e20", "accent": "#c6ff00"},
    "Multan Sultans":      {"primary": "#1565c0", "secondary": "#ffd600", "accent": "#42a5f5"},
    "Quetta Gladiators":   {"primary": "#6a1b9a", "secondary": "#ffd54f", "accent": "#ab47bc"},
    "Peshawar Zalmi":      {"primary": "#f9a825", "secondary": "#e65100", "accent": "#ffcc02"},
    "Rawalpindiz":         {"primary": "#e65100", "secondary": "#7b1fa2", "accent": "#ff6d00"},
    "Hyderabad Kingsmen":  {"primary": "#8e1530", "secondary": "#c8a850", "accent": "#b71c1c"},
}

TEAM_GRADIENTS = {
    name: f"linear-gradient(135deg, {c['primary']}, {c['secondary']})"
    for name, c in TEAM_COLORS.items()
}


def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700;800&family=Share+Tech+Mono&display=swap');

    /* ══ GLOBAL ══ */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1350px; }

    /* ══ STADIUM BACKGROUND ══ */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(160deg, #061912 0%, #030f0a 40%, #051a10 70%, #020d08 100%);
        position: relative;
    }

    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        top: -15%; left: -10%;
        width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(201, 243, 77, 0.04) 0%, transparent 70%);
        pointer-events: none;
    }

    [data-testid="stAppViewContainer"]::after {
        content: '';
        position: fixed;
        bottom: -10%; right: -5%;
        width: 600px; height: 600px;
        background: radial-gradient(circle, rgba(240, 180, 41, 0.03) 0%, transparent 70%);
        pointer-events: none;
    }

    /* ══ SIDEBAR ══ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #041a10 0%, #030e08 50%, #021008 100%);
        border-right: 1px solid rgba(201, 243, 77, 0.08);
    }

    [data-testid="stSidebarNav"] a {
        border-radius: 10px !important;
        padding: 8px 14px !important;
        margin: 2px 8px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        font-family: 'Oswald', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        font-size: 0.8rem !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: rgba(201, 243, 77, 0.08) !important;
        transform: translateX(6px);
    }

    [data-testid="stSidebarNav"] a[aria-selected="true"] {
        background: linear-gradient(135deg, rgba(201, 243, 77, 0.15), rgba(240, 180, 41, 0.08)) !important;
        border-left: 3px solid #c9f34d !important;
    }

    /* ══ KPI CARDS — GLASSMORPHISM + FADE-IN ══ */
    [data-testid="stMetric"] {
        background: rgba(13, 43, 31, 0.6);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(201, 243, 77, 0.08);
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeUp 0.6s ease-out both;
        position: relative;
        overflow: hidden;
    }

    [data-testid="stMetric"]:nth-child(1) { animation-delay: 0.1s; }
    [data-testid="stMetric"]:nth-child(2) { animation-delay: 0.2s; }
    [data-testid="stMetric"]:nth-child(3) { animation-delay: 0.3s; }
    [data-testid="stMetric"]:nth-child(4) { animation-delay: 0.4s; }
    [data-testid="stMetric"]:nth-child(5) { animation-delay: 0.5s; }

    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: rgba(201, 243, 77, 0.25);
        box-shadow: 0 12px 40px rgba(201, 243, 77, 0.08);
    }

    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #c9f34d, #f0b429, transparent);
        opacity: 0;
        transition: opacity 0.4s;
    }

    [data-testid="stMetric"]:hover::before { opacity: 1; }

    [data-testid="stMetricLabel"] {
        color: #5a8a6f !important;
        font-family: 'Oswald', sans-serif !important;
        font-size: 0.7rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }

    [data-testid="stMetricValue"] {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #c9f34d, #f0b429);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    [data-testid="stMetricDelta"] {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.7rem !important;
    }

    /* ══ TABS ══ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(13, 43, 31, 0.4);
        border-radius: 14px;
        padding: 5px;
        border: 1px solid rgba(201, 243, 77, 0.06);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        color: #5a8a6f;
        font-family: 'Oswald', sans-serif;
        font-weight: 500;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"]:hover { color: #c9f34d; }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #c9f34d, #a8d830) !important;
        color: #030f0a !important;
        font-weight: 700;
        box-shadow: 0 4px 20px rgba(201, 243, 77, 0.25);
    }

    /* ══ CHART CONTAINERS ══ */
    [data-testid="stPlotlyChart"] {
        background: rgba(13, 43, 31, 0.4);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 10px;
        border: 1px solid rgba(201, 243, 77, 0.06);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        animation: fadeUp 0.8s ease-out both;
    }

    [data-testid="stPlotlyChart"]:hover {
        border-color: rgba(201, 243, 77, 0.12);
    }

    /* ══ DATAFRAMES ══ */
    [data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid rgba(201, 243, 77, 0.06);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        animation: fadeUp 0.8s ease-out both;
    }

    /* ══ HEADINGS ══ */
    h1 {
        font-family: 'Oswald', sans-serif !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 2rem !important;
    }

    h2, h3, h4, h5 {
        font-family: 'Oswald', sans-serif !important;
        color: #c9f34d !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }

    /* ══ INPUTS ══ */
    [data-baseweb="select"] > div {
        background: rgba(13, 43, 31, 0.5) !important;
        border: 1px solid rgba(201, 243, 77, 0.1) !important;
        border-radius: 10px !important;
    }

    [data-baseweb="select"] > div:hover {
        border-color: rgba(201, 243, 77, 0.3) !important;
    }

    [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
        background: #c9f34d !important;
        box-shadow: 0 0 12px rgba(201, 243, 77, 0.4);
    }

    /* ══ BUTTONS ══ */
    .stButton > button {
        background: linear-gradient(135deg, #c9f34d, #a8d830);
        color: #030f0a;
        border: none;
        border-radius: 10px;
        font-family: 'Oswald', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 10px 24px;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(201, 243, 77, 0.2);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(201, 243, 77, 0.35);
    }

    /* ══ DIVIDERS ══ */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(201, 243, 77, 0.15), rgba(240, 180, 41, 0.1), transparent) !important;
        margin: 1.5rem 0 !important;
    }

    /* ══ HIDE BRANDING ══ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ══ ANIMATIONS ══ */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes shimmer {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }

    @keyframes seamMove {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }

    /* ══ CRICKET BALL SEAM DIVIDER ══ */
    .seam-divider {
        height: 4px;
        background: repeating-linear-gradient(
            90deg,
            transparent, transparent 8px,
            #c9f34d 8px, #c9f34d 14px,
            transparent 14px, transparent 22px
        );
        background-size: 200% 100%;
        animation: seamMove 8s linear infinite;
        border-radius: 2px;
        margin: 0.5rem 0 1.8rem 0;
        opacity: 0.5;
    }

    /* ══ HERO CARD ══ */
    .hero-card {
        background: linear-gradient(135deg, rgba(201, 243, 77, 0.06), rgba(240, 180, 41, 0.03));
        border: 1px solid rgba(201, 243, 77, 0.1);
        border-radius: 20px;
        padding: 28px 36px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
        animation: fadeUp 0.5s ease-out both;
    }

    .hero-card::before {
        content: '';
        position: absolute;
        top: -60%; right: -15%;
        width: 350px; height: 350px;
        background: radial-gradient(circle, rgba(201, 243, 77, 0.05) 0%, transparent 70%);
        border-radius: 50%;
    }

    .hero-card::after {
        content: '';
        position: absolute;
        bottom: -40%; left: -10%;
        width: 250px; height: 250px;
        background: radial-gradient(circle, rgba(240, 180, 41, 0.03) 0%, transparent 70%);
        border-radius: 50%;
    }

    .hero-card h2 {
        font-family: 'Oswald', sans-serif !important;
        color: #fff !important;
        margin: 0 0 6px 0;
        font-size: 1.5rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .hero-card p {
        color: #5a8a6f;
        margin: 0;
        font-size: 0.85rem;
    }

    /* ══ TEAM COLOR CARD ══ */
    .team-card {
        border-radius: 14px;
        padding: 16px 20px;
        margin: 6px 0;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        animation: fadeUp 0.6s ease-out both;
    }

    .team-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }

    .team-card .team-name {
        font-family: 'Oswald', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        color: #fff;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .team-card .team-stat {
        font-family: 'Share Tech Mono', monospace;
        font-size: 1.4rem;
        color: rgba(255,255,255,0.9);
    }

    /* ══ SCROLLBAR ══ */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #030f0a; }
    ::-webkit-scrollbar-thumb { background: #1a3d2a; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #c9f34d; }

    /* ══ SPINNER ══ */
    .stSpinner > div { border-top-color: #c9f34d !important; }

    /* ══ ALERT BOXES ══ */
    .stAlert {
        border-radius: 12px;
        border: 1px solid rgba(201, 243, 77, 0.08);
        background: rgba(13, 43, 31, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)


def hero_card(title, subtitle=""):
    st.markdown(f'<div class="hero-card"><h2>{title}</h2><p>{subtitle}</p></div>', unsafe_allow_html=True)


def seam_divider():
    st.markdown('<div class="seam-divider"></div>', unsafe_allow_html=True)


def accent_line():
    seam_divider()


def team_color_card(team, stat_label, stat_value):
    colors = TEAM_COLORS.get(team, {"primary": "#333", "secondary": "#222"})
    st.markdown(f"""
    <div class="team-card" style="background: linear-gradient(135deg, {colors['primary']}dd, {colors['secondary']}aa);
         border: 1px solid {colors['primary']}44;">
        <div class="team-name">{team}</div>
        <div class="team-stat">{stat_value}</div>
        <div style="color: rgba(255,255,255,0.5); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">{stat_label}</div>
    </div>
    """, unsafe_allow_html=True)


# Plotly Stadium Theme
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#7aaa8f", size=12),
    title_font=dict(size=14, color="#c9f34d", family="Oswald, sans-serif"),
    margin=dict(l=40, r=20, t=50, b=40),
    colorway=["#c9f34d", "#f0b429", "#38bdf8", "#c084fc", "#fb923c",
              "#f87171", "#34d399", "#818cf8"],
    hoverlabel=dict(bgcolor="#0d2b1f", font_color="#fff", bordercolor="#c9f34d",
                    font=dict(family="Share Tech Mono")),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(201,243,77,0.05)",
                font=dict(family="Oswald", color="#7aaa8f")),
)

def get_team_bar_colors(teams):
    """Return list of colors matching team jerseys for bar charts."""
    return [TEAM_COLORS.get(t, {"primary": "#c9f34d"})["primary"] for t in teams]


# Additional CSS fix for truncated metrics
METRIC_FIX_CSS = """
<style>
[data-testid="stMetricLabel"] {
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: unset !important;
    min-width: 0 !important;
}
[data-testid="stMetricValue"] {
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: unset !important;
    font-size: 1.5rem !important;
}
[data-testid="stMetric"] {
    min-width: 0 !important;
    overflow: visible !important;
}
</style>
"""

def fix_metrics():
    """Call after inject_custom_css to fix truncated metric cards."""
    import streamlit as st
    st.markdown(METRIC_FIX_CSS, unsafe_allow_html=True)