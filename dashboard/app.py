"""PSL Analytics — Minimal test for navigation"""
import streamlit as st

st.set_page_config(page_title="PSL Analytics", page_icon="🏏", layout="wide")

overview = st.Page("pages/0_Overview.py", title="Overview", icon="🏠", default=True)
players = st.Page("pages/1_Player_Analytics.py", title="Player Analytics", icon="🏏")
teams = st.Page("pages/2_Team_Analytics.py", title="Team Analytics", icon="👥")
matchups = st.Page("pages/3_Matchups.py", title="Matchups", icon="⚔️")
venues = st.Page("pages/4_Venue_Intelligence.py", title="Venue Intelligence", icon="🏟️")
phases = st.Page("pages/5_Phase_Analytics.py", title="Phase Analytics", icon="⏱️")
form = st.Page("pages/6_Player_Form.py", title="Player Form", icon="📈")
match_intel = st.Page("pages/7_Match_Intelligence.py", title="Match Intelligence", icon="🧠")
predictions = st.Page("pages/8_Predictions.py", title="Predictions", icon="🔮")
clutch = st.Page("pages/9_Clutch_Pressure.py", title="Clutch & Pressure", icon="🔥")

nav = st.navigation([overview, players, teams, matchups, venues, phases, form, match_intel, predictions, clutch])
nav.run()