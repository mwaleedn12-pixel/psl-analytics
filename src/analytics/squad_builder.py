"""
PSL Analytics — Squad Builder & AI Draft Assistant (v3)
PSL 11 (2026) — Corrected prices from official PSL graphics.
Post-trade + post-withdrawal final squads.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

TIER_COLORS = {"Platinum": "#e02020", "Diamond": "#3b82f6", "Gold": "#f0b429", "Silver": "#9ca3af", "Emerging": "#34d399"}
ROLE_ICONS = {"Batter": "🏏", "Bowler": "🎯", "All-rounder": "⭐", "Wicketkeeper": "🧤"}

VENUE_CONDITIONS = {
    "National Stadium, Karachi":    {"pace": 0.55, "spin": 0.45, "avg_first": 165, "label": "Balanced"},
    "Gaddafi Stadium, Lahore":      {"pace": 0.50, "spin": 0.50, "avg_first": 170, "label": "Balanced"},
    "Rawalpindi Cricket Stadium":   {"pace": 0.65, "spin": 0.35, "avg_first": 168, "label": "Pace-friendly"},
    "Multan Cricket Stadium":       {"pace": 0.40, "spin": 0.60, "avg_first": 160, "label": "Spin-friendly"},
    "Arbab Niaz Stadium, Peshawar": {"pace": 0.60, "spin": 0.40, "avg_first": 163, "label": "Pace-friendly"},
    "Bugti Stadium, Quetta":        {"pace": 0.45, "spin": 0.55, "avg_first": 155, "label": "Spin-friendly"},
    "Niaz Stadium, Hyderabad":      {"pace": 0.42, "spin": 0.58, "avg_first": 158, "label": "Spin-friendly"},
}
TEAM_HOME_VENUES = {
    "Lahore Qalandars": "Gaddafi Stadium, Lahore", "Karachi Kings": "National Stadium, Karachi",
    "Islamabad United": "Rawalpindi Cricket Stadium", "Quetta Gladiators": "Bugti Stadium, Quetta",
    "Peshawar Zalmi": "Arbab Niaz Stadium, Peshawar", "Multan Sultans": "Multan Cricket Stadium",
    "Hyderabad Kingsmen": "Niaz Stadium, Hyderabad", "Rawalpindi Pindiz": "Rawalpindi Cricket Stadium",
}
TEAM_PREFERENCES = {
    "Lahore Qalandars": {"style": "pace-heavy", "prefers_youth": True, "prefers_experience": False,
        "key_roles_priority": ["Bowler", "Batter", "All-rounder", "Wicketkeeper"],
        "description": "Pace-first attack, aggressive openers, young fast bowlers"},
    "Karachi Kings": {"style": "balanced", "prefers_youth": False, "prefers_experience": True,
        "key_roles_priority": ["All-rounder", "Bowler", "Batter", "Wicketkeeper"],
        "description": "Star-studded, experienced internationals, all-round depth"},
    "Islamabad United": {"style": "pace-heavy", "prefers_youth": True, "prefers_experience": True,
        "key_roles_priority": ["All-rounder", "Bowler", "Batter", "Wicketkeeper"],
        "description": "All-rounder heavy, strong pace, analytical franchise"},
    "Quetta Gladiators": {"style": "spin-heavy", "prefers_youth": False, "prefers_experience": True,
        "key_roles_priority": ["Bowler", "Batter", "All-rounder", "Wicketkeeper"],
        "description": "Mystery spinners, experienced overseas batters, spin-friendly ground"},
    "Peshawar Zalmi": {"style": "balanced", "prefers_youth": True, "prefers_experience": True,
        "key_roles_priority": ["Batter", "Bowler", "All-rounder", "Wicketkeeper"],
        "description": "Batting powerhouse, pace for Peshawar wicket, strong culture"},
    "Multan Sultans": {"style": "spin-heavy", "prefers_youth": True, "prefers_experience": True,
        "key_roles_priority": ["All-rounder", "Batter", "Bowler", "Wicketkeeper"],
        "description": "All-rounder core, spin-friendly Multan pitch, aggressive batting"},
    "Hyderabad Kingsmen": {"style": "spin-heavy", "prefers_youth": True, "prefers_experience": False,
        "key_roles_priority": ["Batter", "All-rounder", "Bowler", "Wicketkeeper"],
        "description": "Young Pakistan talent, spin-friendly venue, USA connection"},
    "Rawalpindi Pindiz": {"style": "pace-heavy", "prefers_youth": True, "prefers_experience": True,
        "key_roles_priority": ["Bowler", "All-rounder", "Batter", "Wicketkeeper"],
        "description": "Pace battery for seaming pitch, Rizwan-anchored batting"},
}
PHASE_KEYWORDS = {
    "powerplay": {"opener", "opening", "powerplay", "swing", "new ball", "top-order", "aggressive opener"},
    "middle": {"anchor", "control", "middle-order", "middle overs", "off-spin", "wrist spin", "spin", "mystery"},
    "death": {"death", "yorker", "finisher", "slower", "slog", "power hitter", "big hitter", "hitting", "express"},
}
RISING_STARS = {
    "Saim Ayub", "Sameer Minhas", "Shahab Khan", "Irfan Khan Niazi",
    "Haseebullah Khan", "Mehran Mumtaz", "Ubaid Shah", "Abdul Samad",
    "Arafat Minhas", "Sufiyan Muqeem", "Maaz Sadaqat", "Hunain Shah",
    "Abbas Afridi", "Ihsanullah", "Salman Irshad", "Imran Randhawa",
    "Mohammad Naeem", "Shamyl Hussain", "Saad Baig", "Shahzaib Khan",
    "Ahmed Daniyal", "Khawaja Nafay", "Hasan Nawaz",
}

# Backward compat — 37_Squad_Builder imports this
UNSOLD_POOL = []


def _p(name, role, country, price=None, retained=False, tier="", captain=False, specialty="", direct_signing=False, note=""):
    return {"name": name, "role": role, "country": country, "price": price,
            "retained": retained, "tier": tier, "captain": captain,
            "specialty": specialty, "direct_signing": direct_signing, "note": note}

# ═══════════════════════════════════════════════════════════
# FINAL SQUADS — corrected prices from official PSL graphics
# ═══════════════════════════════════════════════════════════

PSL11_SQUADS = {
    "Lahore Qalandars": {"short": "LQ", "purse": 45.0, "players": [
        _p("Shaheen Shah Afridi", "Bowler", "Pakistan", 7.0, True, "Platinum", True, "Left-arm pace, death overs"),
        _p("Abdullah Shafique", "Batter", "Pakistan", 2.2, True, "Diamond", specialty="Top-order anchor"),
        _p("Sikandar Raza", "All-rounder", "Zimbabwe", 2.8, True, "Gold", specialty="Off-spin + middle-order"),
        _p("Mohammad Naeem", "Batter", "Pakistan", 0.7, True, "Silver", specialty="Emerging talent"),
        _p("Mustafizur Rahman", "Bowler", "Bangladesh", 6.44, direct_signing=True, specialty="Left-arm pace, cutters"),
        _p("Haris Rauf", "Bowler", "Pakistan", 7.6, specialty="Express pace, death bowling"),
        _p("Usama Mir", "Bowler", "Pakistan", 3.5, specialty="Leg-spin"),
        _p("Fakhar Zaman", "Batter", "Pakistan", 7.95, specialty="Aggressive opener"),
        _p("Ubaid Shah", "Bowler", "Pakistan", 2.7, specialty="Fast bowling, rising star"),
        _p("Haseebullah Khan", "Wicketkeeper", "Pakistan", 1.1, specialty="Young keeper-batter"),
        _p("Mohammad Farooq", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Daniel Sams", "All-rounder", "Australia", 0.75, specialty="Left-arm pace AR", note="Replaced Shanaka (IPL)"),
        _p("Charith Asalanka", "All-rounder", "Sri Lanka", 0.6, specialty="Left-hand bat, off-spin", note="Replaced Emon (shoulder)"),
        _p("Asif Ali", "Batter", "Pakistan", 0.6, specialty="Power hitter, finisher"),
        _p("Tayyab Tahir", "Batter", "Pakistan", 0.6, specialty="Middle-order batter"),
        _p("Dunith Wellalage", "All-rounder", "Sri Lanka", 0.6, specialty="Spin all-rounder"),
        _p("Rubin Hermann", "Wicketkeeper", "South Africa", 0.6, specialty="Keeper-batter"),
        _p("Maaz Khan", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Shahab Khan", "All-rounder", "Pakistan", 0.6, specialty="Rising star, pace AR"),
        _p("Ryan Burl", "All-rounder", "Zimbabwe", 0.6, specialty="Wrist spin AR"),
    ]},
    "Karachi Kings": {"short": "KK", "purse": 45.0, "players": [
        _p("David Warner", "Batter", "Australia", 7.9, captain=True, specialty="Aggressive opener"),
        _p("Hasan Ali", "Bowler", "Pakistan", 4.76, True, "Platinum", specialty="Pace bowling"),
        _p("Abbas Afridi", "Bowler", "Pakistan", 3.08, True, "Diamond", specialty="Left-arm pace, powerplay"),
        _p("Khushdil Shah", "All-rounder", "Pakistan", 3.36, True, "Gold", specialty="Power hitting, left-arm spin"),
        _p("Saad Baig", "Wicketkeeper", "Pakistan", 0.6, True, "Silver", specialty="Young keeper-batter"),
        _p("Moeen Ali", "All-rounder", "England", 6.44, direct_signing=True, specialty="Off-spin + top-order"),
        _p("Azam Khan", "Wicketkeeper", "Pakistan", 3.25, specialty="Big-hitting keeper"),
        _p("Salman Ali Agha", "All-rounder", "Pakistan", 5.85, specialty="Spin all-rounder"),
        _p("Shahid Aziz", "Bowler", "Pakistan", 0.925, specialty="Pace bowling"),
        _p("Mir Hamza", "Bowler", "Pakistan", 2.4, specialty="Left-arm pace, swing"),
        _p("Adam Zampa", "Bowler", "Australia", 4.5, specialty="Leg-spin, middle overs"),
        _p("Hamza Sohail", "Batter", "Pakistan", 0.6, specialty="Young batter"),
        _p("Aqib Ilyas", "Batter", "Oman", 0.6, specialty="Associate batter"),
        _p("Khuzaima Bin Tanveer", "Batter", "UAE", 0.6, specialty="Associate batter"),
        _p("Muhammad Waseem", "Batter", "Pakistan", 1.1, specialty="Middle-order"),
        _p("Ihsanullah", "Bowler", "Pakistan", 1.05, specialty="Express pace, rising star"),
        _p("Rizwanullah", "Batter", "Pakistan", 0.6, specialty="Domestic talent"),
        _p("Haroon Arshad", "All-rounder", "Pakistan", 0.6, specialty="Domestic AR"),
        _p("Jason Roy", "Batter", "England", 0.6, specialty="T20 opener", note="Replaced Waseem (UAE duty)"),
        _p("Reeza Hendricks", "Batter", "South Africa", 2.0, specialty="Experienced opener"),
    ]},
    "Islamabad United": {"short": "IU", "purse": 45.0, "players": [
        _p("Shadab Khan", "All-rounder", "Pakistan", 7.0, True, "Platinum", True, "Leg-spin + batting, captain"),
        _p("Salman Irshad", "Bowler", "Pakistan", 1.2, True, "Diamond", specialty="Pace bowling"),
        _p("Andries Gous", "Wicketkeeper", "South Africa", 1.4, True, "Gold", specialty="Power-hitting keeper"),
        _p("Devon Conway", "Wicketkeeper", "New Zealand", 6.3, direct_signing=True, specialty="Anchor opener"),
        _p("Faheem Ashraf", "All-rounder", "Pakistan", 8.5, specialty="Pace AR, lower-order hitting"),
        _p("Mehran Mumtaz", "Bowler", "Pakistan", 1.2, specialty="Left-arm spin, rising star"),
        _p("Chris Green", "Bowler", "Australia", 1.4, specialty="Off-spin T20 specialist", note="Replaced Bryant (injury)"),
        _p("Mark Chapman", "Batter", "New Zealand", 7.0, specialty="Left-hand middle-order"),
        _p("Salman Mirza", "Bowler", "Pakistan", 3.92, specialty="Pace bowling"),
        _p("Mir Hamza Sajjad", "Bowler", "Pakistan", 0.7, specialty="Pace bowling"),
        _p("Sameen Gul", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Sameer Minhas", "Batter", "Pakistan", 1.9, specialty="Young aggressive batter"),
        _p("Imad Wasim", "All-rounder", "Pakistan", 2.2, specialty="Left-arm spin + opener"),
        _p("Richard Gleeson", "Bowler", "England", 1.2, specialty="Right-arm fast, T20"),
        _p("Haider Ali", "Batter", "Pakistan", 1.5, specialty="Power-hitting middle-order"),
        _p("Mohammad Hasnain", "Bowler", "Pakistan", 0.775, specialty="Express pace"),
        _p("Pavan Rathnayake", "Batter", "Sri Lanka", 0.6, specialty="Young talent", note="Replaced Airee (Nepal duty)"),
        _p("Mohammad Faiq", "Batter", "Pakistan", 0.6, specialty="Young batter"),
        _p("Nisar Ahmed", "Bowler", "Pakistan", 0.6, specialty="Fast bowling"),
        _p("Mohsin Riaz", "Batter", "Pakistan", 0.6, specialty="Domestic batter"),
    ]},
    "Quetta Gladiators": {"short": "QG", "purse": 45.0, "players": [
        _p("Saud Shakeel", "Batter", "Pakistan", 0.65, captain=True, specialty="Left-hand anchor, captain"),
        _p("Abrar Ahmed", "Bowler", "Pakistan", 7.0, True, "Platinum", specialty="Mystery spin, googly"),
        _p("Usman Tariq", "Bowler", "Pakistan", 5.6, True, "Diamond", specialty="Pace bowling"),
        _p("Hasan Nawaz", "Batter", "Pakistan", 3.92, True, "Gold", specialty="Middle-order power"),
        _p("Shamyl Hussain", "Batter", "Pakistan", 0.84, True, "Silver", specialty="Emerging talent"),
        _p("Alzarri Joseph", "Bowler", "West Indies", 5.6, specialty="Express pace"),
        _p("Rilee Rossouw", "Batter", "South Africa", 5.5, specialty="Explosive left-hand opener"),
        _p("Ahmed Daniyal", "Bowler", "Pakistan", 2.24, specialty="Left-arm pace, swing"),
        _p("Jahanzaib Sultan", "Batter", "Pakistan", 0.6, specialty="Young batter"),
        _p("Jahandad Khan", "Bowler", "Pakistan", 2.5, specialty="Right-arm fast"),
        _p("Khawaja Nafay", "Batter", "Pakistan", 6.5, specialty="Top-order left-hander"),
        _p("Wasim Akram Jr", "Bowler", "Pakistan", 0.775, specialty="Left-arm pace"),
        _p("Khan Zeb", "All-rounder", "Pakistan", 0.6, specialty="All-rounder"),
        _p("Bismillah Khan", "Batter", "Pakistan", 0.6, specialty="Domestic batter"),
        _p("Saqib Khan", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Brett Hampton", "Batter", "New Zealand", 0.6, specialty="Overseas batter"),
        _p("Sam Harper", "Wicketkeeper", "Australia", 0.6, specialty="Keeper-batter"),
        _p("Dinesh Chandimal", "Wicketkeeper", "Sri Lanka", 0.6, specialty="Experienced keeper", note="Replaced Jacobs (NZ duty)"),
        _p("Ben McDermott", "Wicketkeeper", "Australia", 1.1, specialty="Explosive keeper-batter"),
        _p("Tom Curran", "All-rounder", "England", 4.2, specialty="Pace AR, death overs"),
        _p("Khalil Ahmed", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Ahsan Ali", "Batter", "Pakistan", 0.6, specialty="Domestic batter"),
        _p("Kashif Bhatti", "All-rounder", "Pakistan", 0.6, specialty="Left-arm spin AR"),
    ]},
    "Peshawar Zalmi": {"short": "PZ", "purse": 45.0, "players": [
        _p("Babar Azam", "Batter", "Pakistan", 7.0, True, "Platinum", True, "Top-order anchor"),
        _p("Sufiyan Muqeem", "Bowler", "Pakistan", 4.48, True, "Diamond", specialty="Left-arm wrist spin"),
        _p("Abdul Samad", "Batter", "Pakistan", 2.8, True, "Gold", specialty="Power-hitting finisher"),
        _p("Ali Raza", "All-rounder", "Pakistan", 1.96, True, "Silver", specialty="Spin all-rounder"),
        _p("Aaron Hardie", "All-rounder", "Australia", 6.3, direct_signing=True, specialty="Pace all-rounder"),
        _p("Aamir Jamal", "All-rounder", "Pakistan", 1.9, specialty="Pace AR, death bowling"),
        _p("Khurram Shehzad", "Bowler", "Pakistan", 2.7, specialty="Right-arm fast"),
        _p("Mohammad Haris", "Wicketkeeper", "Pakistan", 2.2, specialty="Explosive keeper-batter"),
        _p("Khalid Usman", "Bowler", "Pakistan", 0.6, specialty="Off-spin"),
        _p("Abdul Subhan", "Bowler", "Pakistan", 0.625, specialty="Young pace"),
        _p("James Vince", "Batter", "England", 3.0, specialty="Elegant top-order batter"),
        _p("Michael Bracewell", "All-rounder", "New Zealand", 4.2, specialty="Off-spin AR"),
        _p("Kusal Mendis", "Wicketkeeper", "Sri Lanka", 4.2, specialty="Explosive keeper-batter"),
        _p("Iftikhar Ahmed", "All-rounder", "Pakistan", 1.8, specialty="Power-hitting, off-spin"),
        _p("Nahid Rana", "Bowler", "Bangladesh", 0.6, specialty="Express pace, raw talent"),
        _p("Mirza Tahir Baig", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Kashif Ali", "Batter", "Pakistan", 0.6, specialty="Domestic batter"),
        _p("Shahnawaz Dahani", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Farhan Yousaf", "Batter", "Pakistan", 0.6, specialty="U19 captain, rising star"),
        _p("Shoriful Islam", "Bowler", "Bangladesh", 0.6, specialty="Left-arm pace"),
    ]},
    "Multan Sultans": {"short": "MS", "purse": 45.0, "players": [
        _p("Ashton Turner", "Batter", "Australia", 4.2, captain=True, specialty="Middle-order finisher"),
        _p("Mohammad Nawaz", "All-rounder", "Pakistan", 6.16, True, "Platinum", specialty="Left-arm spin + opener"),
        _p("Shehzad Gul", "Bowler", "Pakistan", 0.6, specialty="Left-arm pace"),
        _p("Faisal Akram", "Bowler", "Pakistan", 1.25, specialty="Pace bowling"),
        _p("Imran Randhawa", "All-rounder", "Pakistan", 0.6, specialty="Rising star"),
        _p("Arafat Minhas", "All-rounder", "Pakistan", 1.1, specialty="Young left-arm pace AR"),
        _p("Sahibzada Farhan", "Batter", "Pakistan", 5.7, specialty="Aggressive opener"),
        _p("Steve Smith", "Batter", "Australia", 14.0, direct_signing=True, specialty="World-class anchor"),
        _p("Peter Siddle", "Bowler", "Australia", 2.5, specialty="Veteran pace, yorkers"),
        _p("Tabraiz Shamsi", "Bowler", "South Africa", 2.2, specialty="Left-arm wrist spin"),
        _p("Lachlan Shaw", "Bowler", "Australia", 0.6, specialty="Pace bowling"),
        _p("Delano Potgieter", "All-rounder", "South Africa", 0.6, specialty="Pace all-rounder"),
        _p("Josh Philippe", "Wicketkeeper", "Australia", 2.3, specialty="Explosive keeper-batter"),
        _p("Shan Masood", "Batter", "Pakistan", 0.65, specialty="Left-hand opener"),
        _p("Momin Qamar", "Bowler", "Pakistan", 1.07, specialty="Wrist spin"),
        _p("Mohammad Awais Zafar", "Batter", "Pakistan", 0.6, specialty="Domestic talent"),
        _p("Muhammad Shahzad", "Batter", "Pakistan", 0.6, specialty="Domestic talent"),
        _p("Arshad Iqbal", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Mohammad Wasim Jr", "Bowler", "Pakistan", 4.1, specialty="Right-arm fast, death overs"),
        _p("Muhammad Ismail", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Atizaz Habib Khan", "Batter", "Pakistan", 0.6, specialty="Domestic batter"),
    ]},
    "Hyderabad Kingsmen": {"short": "HK", "purse": 50.5, "players": [
        _p("Marnus Labuschagne", "Batter", "Australia", 5.88, direct_signing=True, captain=True, specialty="Anchor, leg-spin option"),
        _p("Saim Ayub", "Batter", "Pakistan", 12.6, True, "Platinum", specialty="Young left-hand opener, star"),
        _p("Usman Khan", "Batter", "Pakistan", 4.62, True, "Diamond", specialty="Aggressive middle-order"),
        _p("Akif Javed", "Bowler", "Pakistan", 1.96, True, "Gold", specialty="Left-arm pace"),
        _p("Maaz Sadaqat", "All-rounder", "Pakistan", 3.5, True, specialty="All-rounder, rising star"),
        _p("Mohammad Ali", "Bowler", "Pakistan", 2.15, specialty="Pace bowling"),
        _p("Kusal Perera", "Wicketkeeper", "Sri Lanka", 3.1, specialty="Explosive left-hand keeper"),
        _p("Irfan Khan Niazi", "Bowler", "Pakistan", 2.9, specialty="Right-arm fast, young"),
        _p("Hassan Khan", "All-rounder", "USA", 1.85, specialty="USA international"),
        _p("Shayan Jahangir", "Wicketkeeper", "USA", 0.6, specialty="USA keeper"),
        _p("Glenn Maxwell", "All-rounder", "Australia", 2.34, specialty="360-degree batting, off-spin"),
        _p("Hammad Azam", "All-rounder", "USA", 0.6, specialty="USA all-rounder"),
        _p("Riley Meredith", "Bowler", "Australia", 4.2, specialty="Express pace, 150kph+"),
        _p("Sharjeel Khan", "Batter", "Pakistan", 0.6, specialty="Big-hitting opener"),
        _p("Asif Mehmood", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Hunain Shah", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Rizwan Mehmood", "Wicketkeeper", "Pakistan", 0.6, specialty="Domestic keeper"),
        _p("Saad Ali", "Batter", "Pakistan", 0.6, specialty="Domestic talent"),
        _p("Maheesh Theekshana", "Bowler", "Sri Lanka", 0.6, specialty="Off-spin, carrom ball", note="Replaced Baartman"),
        _p("Ahmed Hussain", "All-rounder", "Pakistan", 0.6, specialty="Domestic talent"),
        _p("Tayyab Arif", "Batter", "Pakistan", 0.6, specialty="Domestic talent"),
    ]},
    "Rawalpindi Pindiz": {"short": "RWP", "purse": 50.5, "players": [
        _p("Mohammad Rizwan", "Wicketkeeper", "Pakistan", 5.6, True, "Platinum", True, "Anchor opener, elite keeper"),
        _p("Sam Billings", "Wicketkeeper", "England", 3.08, True, "Diamond", specialty="Middle-order keeper"),
        _p("Jalat Khan", "All-rounder", "Pakistan", 0.6, specialty="Trade window signing"),
        _p("Yasir Khan", "Bowler", "Pakistan", 0.6, True, "Silver", specialty="Pace bowling"),
        _p("Ben Sears", "Bowler", "New Zealand", 2.5, specialty="Right-arm fast", note="Replaced Zaman Khan"),
        _p("Rishad Hossain", "Bowler", "Bangladesh", 3.0, specialty="Leg-spin"),
        _p("Daryl Mitchell", "All-rounder", "New Zealand", 8.05, specialty="Anchor AR, match-winner"),
        _p("Mohammad Amir", "Bowler", "Pakistan", 5.4, specialty="Left-arm swing, powerplay"),
        _p("Abdullah Fazal", "Batter", "Pakistan", 0.675, specialty="Domestic batter"),
        _p("Amad Butt", "Bowler", "Pakistan", 0.8, specialty="Pace bowling"),
        _p("Dian Forrester", "All-rounder", "South Africa", 0.6, specialty="All-rounder"),
        _p("Usman Khawaja", "Batter", "Australia", 2.2, specialty="Left-hand opener", note="Replaced Laurie Evans"),
        _p("Asif Afridi", "All-rounder", "Pakistan", 2.4, specialty="Left-arm spin AR"),
        _p("Kamran Ghulam", "Batter", "Pakistan", 0.65, specialty="Middle-order batter"),
        _p("Fawad Ali", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Mohammad Amir Khan", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
        _p("Shahzaib Khan", "Batter", "Pakistan", 0.6, specialty="Domestic talent"),
        _p("Cole McConchie", "All-rounder", "New Zealand", 0.6, specialty="Off-spin AR", note="Replaced Fraser-McGurk"),
        _p("Saad Masood", "Batter", "Pakistan", 0.84, specialty="Domestic batter"),
        _p("Mubashir Khan", "All-rounder", "Pakistan", 0.6, specialty="Domestic AR", note="Replaced Naseem Shah"),
        _p("Razaullah", "Bowler", "Pakistan", 0.6, specialty="Pace bowling"),
    ]},
}


# ═══════════════════════════════════════════════════════════
# SQUAD BUILDER ENGINE
# ═══════════════════════════════════════════════════════════

class SquadBuilder:
    MAX_OVERSEAS_IN_SQUAD = 7
    MAX_OVERSEAS_IN_XI = 4
    IDEAL_COMPOSITION = {"Batter": (4, 6), "Bowler": (5, 8), "All-rounder": (2, 4), "Wicketkeeper": (1, 2)}

    def __init__(self, team_name: str):
        if team_name not in PSL11_SQUADS:
            raise ValueError(f"Unknown team: {team_name}")
        self.team_name = team_name
        self.squad_data = PSL11_SQUADS[team_name]
        self.players = self.squad_data["players"]
        self.purse = self.squad_data["purse"]

    def get_squad_df(self):
        df = pd.DataFrame(self.players)
        df["tier"] = df["tier"].fillna("")
        df["price_display"] = df["price"].apply(lambda x: f"{x:.2f} cr" if x is not None else "—")
        return df

    def get_retained(self): return [p for p in self.players if p.get("retained")]
    def get_auction_picks(self): return [p for p in self.players if not p.get("retained")]
    def get_direct_signings(self): return [p for p in self.players if p.get("direct_signing")]
    def get_captain(self): return next((p for p in self.players if p.get("captain")), None)
    def get_rising_stars(self): return [p for p in self.players if p["name"] in RISING_STARS]

    def budget_analysis(self):
        priced = [p for p in self.players if p.get("price") is not None]
        spent = sum(p["price"] for p in priced)
        return {"purse": self.purse, "spent": round(spent, 2), "remaining": round(self.purse - spent, 2),
                "avg_per_player": round(spent / len(priced), 2) if priced else 0,
                "priced_count": len(priced), "unconfirmed_count": len(self.players) - len(priced),
                "squad_size": len(self.players)}

    def spend_by_role(self):
        by_role = {}
        for p in self.players: by_role[p["role"]] = by_role.get(p["role"], 0) + (p.get("price") or 0)
        return {k: round(v, 2) for k, v in sorted(by_role.items(), key=lambda x: -x[1])}

    def price_tier(self, price):
        if price is None: return "Value"
        if price >= 7: return "Elite"
        if price >= 4: return "Premium"
        if price >= 2: return "Solid"
        return "Value"

    def tier_distribution(self):
        tiers = {"Elite": 0, "Premium": 0, "Solid": 0, "Value": 0}
        for p in self.players: tiers[self.price_tier(p.get("price"))] += 1
        return tiers

    def role_counts(self):
        counts = {"Batter": 0, "Bowler": 0, "All-rounder": 0, "Wicketkeeper": 0}
        for p in self.players: counts[p["role"]] = counts.get(p["role"], 0) + 1
        return counts

    def overseas_count(self): return sum(1 for p in self.players if p["country"] != "Pakistan")
    def overseas_players(self): return [p for p in self.players if p["country"] != "Pakistan"]

    def role_gaps(self):
        counts = self.role_counts()
        gaps = {}
        for role, (lo, hi) in self.IDEAL_COMPOSITION.items():
            c = counts.get(role, 0)
            if c < lo: gaps[role] = {"status": "SHORT", "current": c, "ideal_min": lo, "deficit": lo - c}
            elif c > hi: gaps[role] = {"status": "EXCESS", "current": c, "ideal_max": hi, "surplus": c - hi}
            else: gaps[role] = {"status": "OK", "current": c, "ideal_range": f"{lo}-{hi}"}
        return gaps

    def weakest_role(self):
        counts = self.role_counts()
        worst, wd = None, 0
        for role, (lo, _) in self.IDEAL_COMPOSITION.items():
            d = lo - counts.get(role, 0)
            if d > wd: wd, worst = d, role
        return worst or min(counts, key=counts.get)

    def phase_coverage(self):
        cov = {ph: {"players": [], "count": 0, "strength": ""} for ph in PHASE_KEYWORDS}
        for p in self.players:
            spec = (p.get("specialty") or "").lower()
            for phase, kws in PHASE_KEYWORDS.items():
                if any(kw in spec for kw in kws):
                    cov[phase]["players"].append(p["name"])
                    cov[phase]["count"] += 1
        for ph in cov:
            c = cov[ph]["count"]
            cov[ph]["strength"] = "Strong" if c >= 5 else "Adequate" if c >= 3 else "Thin" if c >= 1 else "Gap"
        return cov

    def weakest_phase(self):
        pc = self.phase_coverage()
        return min(pc, key=lambda x: pc[x]["count"])

    def home_venue(self): return TEAM_HOME_VENUES.get(self.team_name, "National Stadium, Karachi")
    def venue_conditions(self): return VENUE_CONDITIONS.get(self.home_venue(), VENUE_CONDITIONS["National Stadium, Karachi"])

    def bowling_style_balance(self):
        pace_kw = {"pace", "fast", "swing", "express", "death", "yorker", "150", "left-arm pace", "right-arm fast"}
        spin_kw = {"spin", "wrist", "off-spin", "leg-spin", "mystery", "googly", "left-arm spin"}
        pace, spin = 0, 0
        for p in self.players:
            if p["role"] in ("Bowler", "All-rounder"):
                spec = (p.get("specialty") or "").lower()
                if any(kw in spec for kw in spin_kw): spin += 1
                else: pace += 1
        return {"pace": pace, "spin": spin, "ratio": f"{pace}:{spin}"}

    def team_preferences(self): return TEAM_PREFERENCES.get(self.team_name, {"style": "balanced", "prefers_youth": True, "prefers_experience": True, "key_roles_priority": ["Bowler","All-rounder","Batter","Wicketkeeper"], "description": "Balanced"})

    def score_candidate(self, candidate):
        scores = {}
        gaps = self.role_gaps()
        role = candidate.get("role", candidate.get("Player_Role", candidate.get("Player Role", "")))
        role = {"Wicketkeeper Batter": "Wicketkeeper", "All Rounder": "All-rounder"}.get(role, role)
        gap_info = gaps.get(role, {})
        scores["role_need"] = (80 + min(20, gap_info.get("deficit", 0) * 10)) if gap_info.get("status") == "SHORT" else 40 if gap_info.get("status") == "OK" else 10

        budget = self.budget_analysis()
        base = candidate.get("base", candidate.get("price", candidate.get("Base_Price", candidate.get("Base Price", 1.0))))
        if isinstance(base, str): base = float(base.replace(",", "")) / 10000000
        elif base and base > 1000: base = base / 10000000
        base = base or 1.0
        rem = budget["remaining"]
        scores["budget_fit"] = 0 if rem <= 0 else 90 if base <= rem * 0.3 else 65 if base <= rem * 0.6 else 40 if base <= rem else 0

        ov = self.overseas_count()
        country = candidate.get("country", candidate.get("Country", "Pakistan"))
        is_ov = country != "Pakistan"
        scores["overseas_fit"] = 80 if not is_ov else 85 if ov < self.MAX_OVERSEAS_IN_SQUAD - 2 else 70 if ov < self.MAX_OVERSEAS_IN_SQUAD else 0

        cond = self.venue_conditions()
        spec = (candidate.get("specialty", "") or candidate.get("Bowling_Style", "") or candidate.get("Bowling Style", "") or "").lower()
        pace_kw = {"pace", "fast", "swing", "express", "death", "yorker", "150", "medium fast"}
        spin_kw = {"spin", "wrist", "off-spin", "leg-spin", "mystery", "googly", "orthodox"}
        is_pace = any(kw in spec for kw in pace_kw)
        is_spin = any(kw in spec for kw in spin_kw)
        scores["venue_match"] = int(cond["pace"] * 120) if is_pace else int(cond["spin"] * 120) if is_spin else 55
        scores["value_index"] = 75 if base <= 1.5 else 65 if base <= 3 else 50 if base <= 5 else 35

        pc = self.phase_coverage()
        wp = self.weakest_phase()
        cand_phases = [ph for ph, kws in PHASE_KEYWORDS.items() if any(kw in spec for kw in kws)]
        scores["phase_need"] = 85 if wp in cand_phases else 65 if any(pc[p]["strength"] in ("Thin", "Gap") for p in cand_phases) else 45 if cand_phases else 30

        prefs = self.team_preferences()
        ss = 50
        if prefs["style"] == "pace-heavy" and is_pace: ss += 25
        elif prefs["style"] == "spin-heavy" and is_spin: ss += 25
        elif prefs["style"] == "balanced": ss += 10
        pri = prefs.get("key_roles_priority", [])
        if role in pri[:2]: ss += 15
        elif role in pri[2:]: ss += 5
        name = candidate.get("name", candidate.get("Full_Name", candidate.get("Full Name", "")))
        if name in RISING_STARS and prefs.get("prefers_youth"): ss += 10
        scores["team_style"] = min(100, ss)

        weights = {"role_need": 0.25, "budget_fit": 0.12, "overseas_fit": 0.10, "venue_match": 0.15, "value_index": 0.12, "phase_need": 0.13, "team_style": 0.13}
        scores["total"] = round(sum(scores[k] * weights[k] for k in weights), 1)
        return scores

    def recommend_picks(self, pool=None, top_n=5):
        if pool is None: pool = self._load_auction_pool()
        results = []
        for c in pool:
            scores = self.score_candidate(c)
            country = c.get("country", c.get("Country", "Pakistan"))
            if scores["overseas_fit"] == 0 and country != "Pakistan": continue
            if scores["budget_fit"] == 0: continue
            name = c.get("name", c.get("Full_Name", c.get("Full Name", "")))
            role = c.get("role", c.get("Player_Role", c.get("Player Role", "")))
            base = c.get("base", c.get("Base_Price", c.get("Base Price", 0)))
            if isinstance(base, str): base = float(base.replace(",", "")) / 10000000
            elif base and base > 1000: base = base / 10000000
            spec = c.get("specialty", c.get("Bowling_Style", c.get("Bowling Style", "")))
            rp = []
            if scores["role_need"] >= 70: rp.append(f"fills {role} gap")
            if scores["venue_match"] >= 60: rp.append("suits home conditions")
            if scores["value_index"] >= 65: rp.append(f"value at {base:.1f} cr")
            if scores["phase_need"] >= 70: rp.append(f"covers {self.weakest_phase()} gap")
            if scores["team_style"] >= 70: rp.append("fits franchise DNA")
            if name in RISING_STARS: rp.append("rising star")
            results.append({"name": name, "role": role, "country": country, "base": base, "specialty": spec or "",
                            "scores": scores, "fit_score": scores["total"], "reasoning": "; ".join(rp) if rp else "Adds depth"})
        results.sort(key=lambda x: -x["fit_score"])
        return results[:top_n]

    def _load_auction_pool(self):
        tsv = Path(__file__).resolve().parent.parent.parent / "data" / "psl11_auction_pool.tsv"
        if tsv.exists():
            try: return pd.read_csv(tsv, sep="\t").to_dict("records")
            except: pass
        return []

    def generate_draft_report(self):
        budget = self.budget_analysis(); gaps = self.role_gaps(); balance = self.bowling_style_balance()
        venue = self.venue_conditions(); recs = self.recommend_picks(); pc = self.phase_coverage()
        prefs = self.team_preferences(); counts = self.role_counts()
        strengths, weaknesses = [], []
        for role, info in gaps.items():
            if info["status"] in ("OK", "EXCESS"): strengths.append(f"{role}s covered ({counts[role]})")
        cap = self.get_captain()
        if cap: strengths.append(f"Captain: {cap['name']}")
        for phase, info in pc.items():
            if info["strength"] == "Strong": strengths.append(f"{phase.title()} phase strong")
        ds = self.get_direct_signings()
        if ds: strengths.append(f"{len(ds)} direct signing(s)")
        for role, info in gaps.items():
            if info["status"] == "SHORT": weaknesses.append(f"Need {info['deficit']} more {role}(s)")
        if self.overseas_count() >= self.MAX_OVERSEAS_IN_SQUAD - 1:
            weaknesses.append(f"Overseas nearly full ({self.overseas_count()}/{self.MAX_OVERSEAS_IN_SQUAD})")
        if budget["remaining"] < 3: weaknesses.append(f"Tight budget ({budget['remaining']:.2f} cr)")
        for phase, info in pc.items():
            if info["strength"] in ("Gap", "Thin"): weaknesses.append(f"{phase.title()} phase {info['strength'].lower()}")
        return {"team": self.team_name, "budget": budget, "role_gaps": gaps, "bowling_balance": balance,
                "venue_conditions": venue, "strengths": strengths, "weaknesses": weaknesses,
                "recommendations": recs, "phase_coverage": pc, "team_preferences": prefs}