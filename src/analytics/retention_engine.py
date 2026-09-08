"""
PSL Analytics — Franchise War Room Engine (PSL 12 Preparation)

Coach's decision-support system:
  1. Player Worth Calculator (multi-factor market value)
  2. Retain vs Release Advisor (with reasoning)
  3. Cheaper Alternative Finder (backup options from auction pool)
  4. Auction Target Recommender (gap-based picks)
  5. Squad Strength / Weakness Report
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from src.analytics.squad_builder import (
    PSL11_SQUADS, RISING_STARS, TEAM_PREFERENCES,
    TEAM_HOME_VENUES, VENUE_CONDITIONS, PHASE_KEYWORDS,
)


# ════════════════════════════════════════════════════════════
# RETENTION RULES (projected PSL 12)
# ════════════════════════════════════════════════════════════

RETENTION_SLOTS = {
    "Platinum": 7.0, "Diamond": 4.5, "Gold": 2.8, "Silver": 0.7,
}
TOTAL_RETENTION_COST = sum(RETENTION_SLOTS.values())  # 15.0 cr
PROJECTED_PURSE = 50.0
MAX_OVERSEAS_RETAIN = 1


# ════════════════════════════════════════════════════════════
# PLAYER PROFILES — age, caps, form, specialty tags
# ════════════════════════════════════════════════════════════

# role_tag drives scarcity pricing and backup matching
# phase: powerplay / middle / death
# form: 1-10 subjective rating based on recent T20 form

PLAYER_PROFILES = {
    # ── LQ ──
    "Shaheen Shah Afridi":   {"age": 26, "caps": 65, "pedigree": "elite", "phase": "death", "role_tag": "lead_pacer", "form": 9.0, "bat_style": "Left", "bowl_style": "Left-arm fast"},
    "Abdullah Shafique":     {"age": 25, "caps": 15, "pedigree": "solid", "phase": "powerplay", "role_tag": "anchor", "form": 7.0, "bat_style": "Right", "bowl_style": "—"},
    "Sikandar Raza":         {"age": 38, "caps": 60, "pedigree": "solid", "phase": "middle", "role_tag": "spin_ar", "form": 6.5, "bat_style": "Right", "bowl_style": "Off-spin"},
    "Mohammad Naeem":        {"age": 21, "caps": 0, "pedigree": "uncapped", "phase": "middle", "role_tag": "batter", "form": 5.5, "bat_style": "Right", "bowl_style": "—"},
    "Mustafizur Rahman":     {"age": 29, "caps": 80, "pedigree": "elite", "phase": "death", "role_tag": "death_bowler", "form": 8.0, "bat_style": "Left", "bowl_style": "Left-arm pace"},
    "Haris Rauf":            {"age": 31, "caps": 55, "pedigree": "elite", "phase": "death", "role_tag": "lead_pacer", "form": 8.5, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Usama Mir":             {"age": 28, "caps": 10, "pedigree": "solid", "phase": "middle", "role_tag": "spinner", "form": 7.0, "bat_style": "Right", "bowl_style": "Leg-spin"},
    "Fakhar Zaman":          {"age": 35, "caps": 80, "pedigree": "elite", "phase": "powerplay", "role_tag": "opener", "form": 7.0, "bat_style": "Left", "bowl_style": "—"},
    "Ubaid Shah":            {"age": 22, "caps": 3, "pedigree": "emerging", "phase": "death", "role_tag": "pacer", "form": 7.5, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Haseebullah Khan":      {"age": 22, "caps": 2, "pedigree": "emerging", "phase": "middle", "role_tag": "keeper", "form": 6.0, "bat_style": "Left", "bowl_style": "—"},
    "Daniel Sams":           {"age": 32, "caps": 10, "pedigree": "solid", "phase": "death", "role_tag": "pace_ar", "form": 6.5, "bat_style": "Right", "bowl_style": "Left-arm fast"},
    "Charith Asalanka":      {"age": 28, "caps": 50, "pedigree": "elite", "phase": "middle", "role_tag": "spin_ar", "form": 8.0, "bat_style": "Left", "bowl_style": "Off-spin"},
    "Asif Ali":              {"age": 33, "caps": 50, "pedigree": "solid", "phase": "death", "role_tag": "finisher", "form": 6.0, "bat_style": "Right", "bowl_style": "—"},
    "Hussain Talat":         {"age": 29, "caps": 20, "pedigree": "solid", "phase": "middle", "role_tag": "bat_ar", "form": 5.5, "bat_style": "Left", "bowl_style": "Medium"},
    "Tayyab Tahir":          {"age": 25, "caps": 5, "pedigree": "emerging", "phase": "middle", "role_tag": "batter", "form": 6.5, "bat_style": "Right", "bowl_style": "Leg-spin"},
    "Dunith Wellalage":      {"age": 22, "caps": 30, "pedigree": "solid", "phase": "middle", "role_tag": "spin_ar", "form": 7.5, "bat_style": "Left", "bowl_style": "Slow left-arm"},
    "Shahab Khan":           {"age": 22, "caps": 1, "pedigree": "emerging", "phase": "powerplay", "role_tag": "pace_ar", "form": 6.5, "bat_style": "Left", "bowl_style": "Left-arm fast"},
    # ── KK ──
    "David Warner":          {"age": 39, "caps": 100, "pedigree": "legend", "phase": "powerplay", "role_tag": "opener", "form": 6.0, "bat_style": "Left", "bowl_style": "—"},
    "Hasan Ali":             {"age": 30, "caps": 55, "pedigree": "elite", "phase": "death", "role_tag": "pacer", "form": 6.5, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Abbas Afridi":          {"age": 24, "caps": 15, "pedigree": "emerging", "phase": "powerplay", "role_tag": "lead_pacer", "form": 8.0, "bat_style": "Left", "bowl_style": "Left-arm fast"},
    "Khushdil Shah":         {"age": 29, "caps": 25, "pedigree": "solid", "phase": "death", "role_tag": "finisher", "form": 6.5, "bat_style": "Left", "bowl_style": "Left-arm spin"},
    "Saad Baig":             {"age": 20, "caps": 2, "pedigree": "emerging", "phase": "middle", "role_tag": "keeper", "form": 6.0, "bat_style": "Right", "bowl_style": "—"},
    "Moeen Ali":             {"age": 39, "caps": 75, "pedigree": "elite", "phase": "middle", "role_tag": "spin_ar", "form": 6.5, "bat_style": "Left", "bowl_style": "Off-spin"},
    "Azam Khan":             {"age": 26, "caps": 15, "pedigree": "solid", "phase": "death", "role_tag": "power_keeper", "form": 6.5, "bat_style": "Right", "bowl_style": "—"},
    "Salman Ali Agha":       {"age": 30, "caps": 30, "pedigree": "solid", "phase": "middle", "role_tag": "spin_ar", "form": 8.0, "bat_style": "Right", "bowl_style": "Off-spin"},
    "Mir Hamza":             {"age": 30, "caps": 5, "pedigree": "solid", "phase": "powerplay", "role_tag": "pacer", "form": 6.5, "bat_style": "Left", "bowl_style": "Left-arm fast"},
    "Adam Zampa":            {"age": 34, "caps": 75, "pedigree": "elite", "phase": "middle", "role_tag": "spinner", "form": 8.0, "bat_style": "Right", "bowl_style": "Leg-spin"},
    "Johnson Charles":       {"age": 37, "caps": 40, "pedigree": "solid", "phase": "powerplay", "role_tag": "power_keeper", "form": 6.0, "bat_style": "Right", "bowl_style": "—"},
    "Jason Roy":             {"age": 35, "caps": 35, "pedigree": "solid", "phase": "powerplay", "role_tag": "opener", "form": 5.5, "bat_style": "Right", "bowl_style": "—"},
    "Ihsanullah":            {"age": 22, "caps": 5, "pedigree": "emerging", "phase": "death", "role_tag": "pacer", "form": 7.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    # ── IU ──
    "Shadab Khan":           {"age": 28, "caps": 75, "pedigree": "elite", "phase": "middle", "role_tag": "spin_ar", "form": 8.5, "bat_style": "Right", "bowl_style": "Leg-spin"},
    "Salman Irshad":         {"age": 24, "caps": 5, "pedigree": "emerging", "phase": "death", "role_tag": "pacer", "form": 7.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Andries Gous":          {"age": 30, "caps": 20, "pedigree": "solid", "phase": "death", "role_tag": "power_keeper", "form": 7.5, "bat_style": "Right", "bowl_style": "—"},
    "Devon Conway":          {"age": 33, "caps": 15, "pedigree": "elite", "phase": "powerplay", "role_tag": "anchor", "form": 7.5, "bat_style": "Left", "bowl_style": "—"},
    "Faheem Ashraf":         {"age": 30, "caps": 40, "pedigree": "solid", "phase": "death", "role_tag": "pace_ar", "form": 7.5, "bat_style": "Left", "bowl_style": "Right-arm fast"},
    "Mehran Mumtaz":         {"age": 22, "caps": 5, "pedigree": "emerging", "phase": "middle", "role_tag": "spinner", "form": 7.5, "bat_style": "Left", "bowl_style": "Slow left-arm"},
    "Mark Chapman":          {"age": 32, "caps": 35, "pedigree": "solid", "phase": "middle", "role_tag": "batter", "form": 7.0, "bat_style": "Left", "bowl_style": "Slow left-arm"},
    "Imad Wasim":            {"age": 35, "caps": 60, "pedigree": "elite", "phase": "middle", "role_tag": "spin_ar", "form": 7.0, "bat_style": "Left", "bowl_style": "Slow left-arm"},
    "Mohammad Wasim Jr":     {"age": 24, "caps": 20, "pedigree": "solid", "phase": "death", "role_tag": "lead_pacer", "form": 7.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Sameer Minhas":         {"age": 19, "caps": 3, "pedigree": "emerging", "phase": "powerplay", "role_tag": "opener", "form": 7.5, "bat_style": "Right", "bowl_style": "—"},
    "Richard Gleeson":       {"age": 37, "caps": 10, "pedigree": "solid", "phase": "death", "role_tag": "pacer", "form": 6.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Haider Ali":            {"age": 24, "caps": 20, "pedigree": "solid", "phase": "middle", "role_tag": "batter", "form": 5.5, "bat_style": "Right", "bowl_style": "—"},
    "Chris Green":           {"age": 31, "caps": 5, "pedigree": "solid", "phase": "middle", "role_tag": "spinner", "form": 6.5, "bat_style": "Right", "bowl_style": "Off-spin"},
    # ── QG ──
    "Saud Shakeel":          {"age": 29, "caps": 10, "pedigree": "solid", "phase": "middle", "role_tag": "anchor", "form": 7.5, "bat_style": "Left", "bowl_style": "Slow left-arm"},
    "Abrar Ahmed":           {"age": 26, "caps": 10, "pedigree": "solid", "phase": "middle", "role_tag": "mystery_spin", "form": 8.0, "bat_style": "Right", "bowl_style": "Leg-spin"},
    "Usman Tariq":           {"age": 25, "caps": 3, "pedigree": "emerging", "phase": "death", "role_tag": "pacer", "form": 7.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Hasan Nawaz":           {"age": 23, "caps": 0, "pedigree": "uncapped", "phase": "middle", "role_tag": "batter", "form": 7.0, "bat_style": "Right", "bowl_style": "—"},
    "Shamyl Hussain":        {"age": 21, "caps": 0, "pedigree": "uncapped", "phase": "middle", "role_tag": "batter", "form": 5.5, "bat_style": "Right", "bowl_style": "—"},
    "Alzarri Joseph":        {"age": 29, "caps": 30, "pedigree": "elite", "phase": "death", "role_tag": "lead_pacer", "form": 8.5, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Rilee Rossouw":         {"age": 35, "caps": 25, "pedigree": "solid", "phase": "powerplay", "role_tag": "opener", "form": 7.5, "bat_style": "Left", "bowl_style": "—"},
    "Ahmed Daniyal":         {"age": 24, "caps": 8, "pedigree": "emerging", "phase": "powerplay", "role_tag": "pacer", "form": 7.5, "bat_style": "Left", "bowl_style": "Left-arm fast"},
    "Khawaja Nafay":         {"age": 22, "caps": 2, "pedigree": "emerging", "phase": "powerplay", "role_tag": "opener", "form": 8.0, "bat_style": "Left", "bowl_style": "—"},
    "Tom Curran":            {"age": 31, "caps": 35, "pedigree": "solid", "phase": "death", "role_tag": "pace_ar", "form": 7.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Dinesh Chandimal":      {"age": 36, "caps": 40, "pedigree": "solid", "phase": "middle", "role_tag": "keeper", "form": 6.0, "bat_style": "Right", "bowl_style": "—"},
    "Jahandad Khan":         {"age": 26, "caps": 3, "pedigree": "emerging", "phase": "death", "role_tag": "pacer", "form": 6.5, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    # ── PZ ──
    "Babar Azam":            {"age": 31, "caps": 110, "pedigree": "legend", "phase": "powerplay", "role_tag": "anchor", "form": 8.0, "bat_style": "Right", "bowl_style": "—"},
    "Sufiyan Muqeem":        {"age": 22, "caps": 8, "pedigree": "emerging", "phase": "middle", "role_tag": "mystery_spin", "form": 8.5, "bat_style": "Left", "bowl_style": "Left-arm wrist spin"},
    "Abdul Samad":           {"age": 23, "caps": 5, "pedigree": "emerging", "phase": "death", "role_tag": "finisher", "form": 7.0, "bat_style": "Right", "bowl_style": "—"},
    "Ali Raza":              {"age": 27, "caps": 5, "pedigree": "emerging", "phase": "middle", "role_tag": "spin_ar", "form": 6.0, "bat_style": "Right", "bowl_style": "—"},
    "Aamir Jamal":           {"age": 25, "caps": 15, "pedigree": "solid", "phase": "death", "role_tag": "pace_ar", "form": 8.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Khurram Shehzad":       {"age": 25, "caps": 10, "pedigree": "solid", "phase": "powerplay", "role_tag": "pacer", "form": 7.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Mohammad Haris":        {"age": 24, "caps": 12, "pedigree": "solid", "phase": "powerplay", "role_tag": "power_keeper", "form": 7.5, "bat_style": "Right", "bowl_style": "—"},
    "James Vince":           {"age": 35, "caps": 15, "pedigree": "solid", "phase": "powerplay", "role_tag": "batter", "form": 6.5, "bat_style": "Right", "bowl_style": "—"},
    "Michael Bracewell":     {"age": 34, "caps": 25, "pedigree": "solid", "phase": "middle", "role_tag": "spin_ar", "form": 7.0, "bat_style": "Left", "bowl_style": "Off-spin"},
    "Kusal Mendis":          {"age": 29, "caps": 55, "pedigree": "elite", "phase": "powerplay", "role_tag": "power_keeper", "form": 8.0, "bat_style": "Right", "bowl_style": "—"},
    "Iftikhar Ahmed":        {"age": 34, "caps": 55, "pedigree": "solid", "phase": "death", "role_tag": "finisher", "form": 6.0, "bat_style": "Right", "bowl_style": "Off-spin"},
    "Shoriful Islam":        {"age": 24, "caps": 20, "pedigree": "solid", "phase": "powerplay", "role_tag": "pacer", "form": 7.0, "bat_style": "Left", "bowl_style": "Left-arm fast"},
    # ── MS ──
    "Mohammad Nawaz":        {"age": 32, "caps": 55, "pedigree": "elite", "phase": "middle", "role_tag": "spin_ar", "form": 7.5, "bat_style": "Left", "bowl_style": "Slow left-arm"},
    "Steve Smith":           {"age": 37, "caps": 20, "pedigree": "legend", "phase": "middle", "role_tag": "anchor", "form": 7.0, "bat_style": "Right", "bowl_style": "Leg-spin"},
    "Ashton Turner":         {"age": 32, "caps": 30, "pedigree": "solid", "phase": "death", "role_tag": "finisher", "form": 7.0, "bat_style": "Right", "bowl_style": "—"},
    "Sahibzada Farhan":      {"age": 28, "caps": 5, "pedigree": "emerging", "phase": "powerplay", "role_tag": "opener", "form": 7.5, "bat_style": "Right", "bowl_style": "—"},
    "Peter Siddle":          {"age": 40, "caps": 5, "pedigree": "solid", "phase": "death", "role_tag": "pacer", "form": 5.5, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Tabraiz Shamsi":        {"age": 36, "caps": 55, "pedigree": "elite", "phase": "middle", "role_tag": "spinner", "form": 7.0, "bat_style": "Right", "bowl_style": "Left-arm wrist spin"},
    "Josh Philippe":         {"age": 28, "caps": 5, "pedigree": "solid", "phase": "powerplay", "role_tag": "power_keeper", "form": 7.0, "bat_style": "Right", "bowl_style": "—"},
    "Shan Masood":           {"age": 35, "caps": 5, "pedigree": "solid", "phase": "powerplay", "role_tag": "anchor", "form": 6.0, "bat_style": "Left", "bowl_style": "—"},
    "Arafat Minhas":         {"age": 19, "caps": 5, "pedigree": "emerging", "phase": "powerplay", "role_tag": "pace_ar", "form": 8.0, "bat_style": "Left", "bowl_style": "Slow left-arm"},
    "Momin Qamar":           {"age": 22, "caps": 3, "pedigree": "emerging", "phase": "middle", "role_tag": "spinner", "form": 6.5, "bat_style": "Left", "bowl_style": "Left-arm wrist spin"},
    # ── HK ──
    "Saim Ayub":             {"age": 22, "caps": 20, "pedigree": "elite", "phase": "powerplay", "role_tag": "opener", "form": 9.5, "bat_style": "Left", "bowl_style": "—"},
    "Usman Khan":            {"age": 26, "caps": 10, "pedigree": "solid", "phase": "middle", "role_tag": "batter", "form": 7.5, "bat_style": "Left", "bowl_style": "—"},
    "Akif Javed":            {"age": 26, "caps": 8, "pedigree": "emerging", "phase": "powerplay", "role_tag": "pacer", "form": 7.0, "bat_style": "Left", "bowl_style": "Left-arm fast"},
    "Marnus Labuschagne":    {"age": 32, "caps": 5, "pedigree": "elite", "phase": "middle", "role_tag": "anchor", "form": 6.5, "bat_style": "Right", "bowl_style": "Leg-spin"},
    "Kusal Perera":          {"age": 35, "caps": 50, "pedigree": "solid", "phase": "powerplay", "role_tag": "power_keeper", "form": 6.5, "bat_style": "Left", "bowl_style": "—"},
    "Glenn Maxwell":         {"age": 38, "caps": 100, "pedigree": "legend", "phase": "middle", "role_tag": "spin_ar", "form": 7.0, "bat_style": "Right", "bowl_style": "Off-spin"},
    "Riley Meredith":        {"age": 29, "caps": 5, "pedigree": "solid", "phase": "death", "role_tag": "lead_pacer", "form": 7.5, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Irfan Khan Niazi":      {"age": 21, "caps": 5, "pedigree": "emerging", "phase": "death", "role_tag": "pacer", "form": 8.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Maaz Sadaqat":          {"age": 24, "caps": 2, "pedigree": "emerging", "phase": "middle", "role_tag": "bat_ar", "form": 7.0, "bat_style": "Right", "bowl_style": "—"},
    "Maheesh Theekshana":    {"age": 25, "caps": 25, "pedigree": "solid", "phase": "middle", "role_tag": "mystery_spin", "form": 8.0, "bat_style": "Right", "bowl_style": "Off-spin"},
    "Sharjeel Khan":         {"age": 35, "caps": 15, "pedigree": "solid", "phase": "powerplay", "role_tag": "opener", "form": 5.0, "bat_style": "Left", "bowl_style": "—"},
    # ── RWP ──
    "Mohammad Rizwan":       {"age": 32, "caps": 90, "pedigree": "legend", "phase": "powerplay", "role_tag": "anchor", "form": 8.5, "bat_style": "Right", "bowl_style": "—"},
    "Sam Billings":          {"age": 33, "caps": 30, "pedigree": "solid", "phase": "middle", "role_tag": "keeper", "form": 6.5, "bat_style": "Right", "bowl_style": "—"},
    "Naseem Shah":           {"age": 22, "caps": 20, "pedigree": "elite", "phase": "powerplay", "role_tag": "lead_pacer", "form": 8.5, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Rishad Hossain":        {"age": 22, "caps": 10, "pedigree": "emerging", "phase": "middle", "role_tag": "spinner", "form": 7.0, "bat_style": "Right", "bowl_style": "Leg-spin"},
    "Daryl Mitchell":        {"age": 34, "caps": 45, "pedigree": "elite", "phase": "middle", "role_tag": "bat_ar", "form": 8.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Mohammad Amir":         {"age": 34, "caps": 50, "pedigree": "elite", "phase": "powerplay", "role_tag": "lead_pacer", "form": 7.5, "bat_style": "Left", "bowl_style": "Left-arm fast"},
    "Kamran Ghulam":         {"age": 29, "caps": 10, "pedigree": "solid", "phase": "middle", "role_tag": "batter", "form": 7.0, "bat_style": "Right", "bowl_style": "—"},
    "Asif Afridi":           {"age": 28, "caps": 5, "pedigree": "emerging", "phase": "middle", "role_tag": "spin_ar", "form": 6.0, "bat_style": "Left", "bowl_style": "Slow left-arm"},
    "Dian Forrester":        {"age": 28, "caps": 5, "pedigree": "emerging", "phase": "middle", "role_tag": "bat_ar", "form": 6.0, "bat_style": "Left", "bowl_style": "Right-arm fast"},
    "Yasir Khan":            {"age": 23, "caps": 2, "pedigree": "emerging", "phase": "middle", "role_tag": "pacer", "form": 6.0, "bat_style": "Right", "bowl_style": "Right-arm fast"},
    "Cole McConchie":        {"age": 30, "caps": 20, "pedigree": "solid", "phase": "middle", "role_tag": "spin_ar", "form": 6.0, "bat_style": "Right", "bowl_style": "Off-spin"},
}


# ════════════════════════════════════════════════════════════
# SCARCITY, AGE CURVE, PEDIGREE MULTIPLIERS
# ════════════════════════════════════════════════════════════

ROLE_SCARCITY = {
    "lead_pacer": 1.35, "death_bowler": 1.30, "mystery_spin": 1.25,
    "power_keeper": 1.20, "pace_ar": 1.20, "spin_ar": 1.15,
    "opener": 1.10, "finisher": 1.15, "anchor": 1.05,
    "bat_ar": 1.05, "keeper": 1.00, "pacer": 1.05,
    "batter": 1.00, "spinner": 1.05,
}

ROLE_LABELS = {
    "lead_pacer": "Lead Pacer", "death_bowler": "Death Specialist", "mystery_spin": "Mystery Spinner",
    "power_keeper": "Power Keeper", "pace_ar": "Pace All-rounder", "spin_ar": "Spin All-rounder",
    "opener": "Opener", "finisher": "Finisher", "anchor": "Anchor",
    "bat_ar": "Batting All-rounder", "keeper": "Keeper", "pacer": "Pacer",
    "batter": "Batter", "spinner": "Spinner",
}

PEDIGREE_MULT = {"legend": 1.40, "elite": 1.20, "solid": 1.00, "emerging": 0.90, "uncapped": 0.70}
PEDIGREE_BASES = {"legend": 8.0, "elite": 5.0, "solid": 2.5, "emerging": 1.0, "uncapped": 0.6}


def _age_factor(age: int) -> float:
    if age < 22: return 1.15
    if age < 26: return 1.20
    if age < 30: return 1.10
    if age < 33: return 0.95
    if age < 36: return 0.80
    return 0.65


# ════════════════════════════════════════════════════════════
# WORTH CALCULATOR
# ════════════════════════════════════════════════════════════

def calculate_worth(name: str, auction_price: float = None) -> Dict:
    """Full market value breakdown for a single player."""
    prof = PLAYER_PROFILES.get(name)
    if not prof:
        base = auction_price or 0.6
        return {"name": name, "market_value": round(base, 2), "base_price": base,
                "verdict": "No profile data", "value_band": _band(base), "factors": {},
                "retention_score": 25.0, "retain_advice": "Release — no profile", "age": 28,
                "form": 5.0, "pedigree": "uncapped", "role_tag": "batter", "role_label": "Unknown",
                "phase": "middle", "caps": 0, "is_rising_star": False, "bat_style": "", "bowl_style": ""}

    base = auction_price if auction_price and auction_price > 0 else PEDIGREE_BASES.get(prof["pedigree"], 1.0)
    af = _age_factor(prof["age"])
    sf = ROLE_SCARCITY.get(prof["role_tag"], 1.0)
    pf = PEDIGREE_MULT.get(prof["pedigree"], 1.0)
    ff = 0.85 + (prof["form"] / 10) * 0.30
    rs = 1.15 if name in RISING_STARS else 1.0

    mv = round(max(0.5, min(16.0, base * af * sf * pf * ff * rs)), 2)

    # Verdict
    if auction_price and auction_price > 0:
        ratio = mv / auction_price
        if ratio >= 1.5: verdict = "Massively Underpaid"
        elif ratio >= 1.15: verdict = "Underpaid — great buy"
        elif ratio >= 0.85: verdict = "Fair price"
        elif ratio >= 0.6: verdict = "Slightly Overpaid"
        else: verdict = "Overpaid — consider releasing"
    else:
        verdict = "Unpriced — estimate only"

    # Retain or release?
    ret_score = _retention_score(mv, prof, name)
    if ret_score >= 75: retain_advice = "MUST RETAIN"
    elif ret_score >= 60: retain_advice = "Strong retain candidate"
    elif ret_score >= 45: retain_advice = "Consider retaining"
    elif ret_score >= 30: retain_advice = "Replaceable — release for auction value"
    else: retain_advice = "Release — find cheaper alternative"

    return {
        "name": name, "age": prof["age"], "form": prof["form"],
        "base_price": auction_price, "market_value": mv,
        "pedigree": prof["pedigree"], "role_tag": prof["role_tag"],
        "role_label": ROLE_LABELS.get(prof["role_tag"], prof["role_tag"]),
        "phase": prof["phase"], "bat_style": prof.get("bat_style", ""),
        "bowl_style": prof.get("bowl_style", ""),
        "caps": prof["caps"], "value_band": _band(mv), "verdict": verdict,
        "retention_score": ret_score, "retain_advice": retain_advice,
        "is_rising_star": name in RISING_STARS,
        "factors": {"age": af, "scarcity": sf, "pedigree": pf, "form": round(ff, 3), "rising_star": rs > 1},
    }


def _band(v):
    if v >= 8: return "Franchise Player"
    if v >= 5: return "Premium"
    if v >= 3: return "Solid"
    if v >= 1.5: return "Squad Player"
    return "Value Pick"


def _retention_score(mv, prof, name):
    s = min(35, mv * 4)
    s += prof["form"] * 3.5
    if 22 <= prof["age"] <= 29: s += 15
    elif prof["age"] < 22: s += 10
    ppts = {"legend": 12, "elite": 10, "solid": 5, "emerging": 3, "uncapped": 0}
    s += ppts.get(prof["pedigree"], 0)
    if prof["form"] >= 7.5 and prof["age"] <= 25: s += 8
    return round(min(100, s), 1)


# ════════════════════════════════════════════════════════════
# CHEAPER ALTERNATIVE FINDER
# ════════════════════════════════════════════════════════════

def find_alternatives(player_name: str, team_name: str, top_n: int = 5) -> List[Dict]:
    """
    Find cheaper alternatives from the auction pool who play the same
    role_tag and phase as the given player.
    """
    prof = PLAYER_PROFILES.get(player_name)
    if not prof:
        return []

    target_role = prof["role_tag"]
    target_phase = prof["phase"]
    player_mv = calculate_worth(player_name)["market_value"]

    # Load auction pool
    tsv = Path(__file__).resolve().parent.parent.parent / "data" / "psl11_auction_pool.tsv"
    if not tsv.exists():
        return []
    df = pd.read_csv(tsv, sep="\t")

    # Map pool roles to role_tags
    bowl_to_tag = {
        "Right-Arm Fast": "lead_pacer", "Left-Arm Fast": "lead_pacer",
        "Right-Arm Medium Fast": "pacer", "Left-Arm Medium Fast": "pacer",
        "Right-Arm Legspin": "spinner", "Right-Arm Offspin": "spinner",
        "Slow left-arm orthodox": "spinner", "Slow left-arm wrist spin": "mystery_spin",
        "Left-arm wrist spin": "mystery_spin", "Right-arm Legspin": "spinner",
    }

    # Exclude players already in this team
    team_names = {p["name"] for p in PSL11_SQUADS[team_name]["players"]}

    alts = []
    for _, row in df.iterrows():
        pname = row.get("Full_Name", "")
        if pname in team_names or pname == player_name:
            continue

        base_pkr = row.get("Base_Price", 6000000)
        base_cr = base_pkr / 10000000

        # Only cheaper than the player we're replacing
        if base_cr >= player_mv:
            continue

        # QUALITY FILTER: minimum 1.1 cr (11M PKR) = international/franchise level
        if base_cr < 1.1:
            continue

        bowl = str(row.get("Bowling_Style", ""))
        pool_tag = bowl_to_tag.get(bowl, "batter")
        role_str = str(row.get("Player_Role", ""))
        if "All Rounder" in role_str:
            if "Fast" in bowl or "Medium Fast" in bowl:
                pool_tag = "pace_ar"
            elif "spin" in bowl.lower() or "orthodox" in bowl.lower():
                pool_tag = "spin_ar"
        elif "Wicketkeeper" in role_str:
            pool_tag = "keeper"

        # Match role_tag family AND ensure role category matches
        if not _tags_match(target_role, pool_tag):
            continue
        # Bowler alternatives should be actual Bowlers/All-rounders, not batters with part-time bowling
        target_is_bowling = target_role in ("lead_pacer", "death_bowler", "pacer", "spinner", "mystery_spin")
        candidate_is_batter_role = role_str in ("Batter", "Wicketkeeper Batter")
        if target_is_bowling and candidate_is_batter_role:
            continue

        alts.append({
            "name": pname, "country": row.get("Country", ""),
            "role": role_str, "bowling": bowl,
            "base_price": round(base_cr, 2),
            "savings": round(player_mv - base_cr, 2),
            "pool_tag": pool_tag,
        })

    # Sort by base price DESCENDING — best quality alternatives first, not cheapest
    alts.sort(key=lambda x: (-x["base_price"]))
    return alts[:top_n]


def _tags_match(t1, t2):
    """Check if two role_tags are in the same family."""
    families = {
        frozenset({"lead_pacer", "pacer", "death_bowler"}),
        frozenset({"spinner", "mystery_spin"}),
        frozenset({"spin_ar", "bat_ar"}),
        frozenset({"pace_ar"}),
        frozenset({"opener", "anchor", "batter"}),
        frozenset({"finisher", "power_keeper"}),
        frozenset({"keeper"}),
    }
    if t1 == t2:
        return True
    for fam in families:
        if t1 in fam and t2 in fam:
            return True
    return False


# ════════════════════════════════════════════════════════════
# RETENTION PREDICTOR (PSL 12) — Price-based, no categories
# ════════════════════════════════════════════════════════════

MAX_RETENTIONS = 4

def predict_retentions(team_name: str) -> Dict:
    """
    Predict top 4 retentions — each retained at their LAST AUCTION PRICE.
    No tiers — just price. Total deducted from purse.
    """
    squad = PSL11_SQUADS.get(team_name)
    if not squad:
        return {"error": f"Unknown: {team_name}"}

    scored = []
    for p in squad["players"]:
        w = calculate_worth(p["name"], p.get("price"))
        is_ov = p["country"] != "Pakistan"
        prof = PLAYER_PROFILES.get(p["name"], {})
        sc = w["retention_score"]
        if p.get("captain"):
            sc += 8
        if TEAM_PREFERENCES.get(team_name, {}).get("prefers_youth") and prof.get("age", 30) <= 25:
            sc += 5
        # Domestic bonus — overseas slot is precious, keep it for auction
        if not is_ov:
            sc += 5
        # last auction price — what they'd actually be retained at
        last_price = p.get("price") or 0.6
        scored.append({**p, **w, "retention_score": round(min(100, sc), 1),
                       "is_overseas": is_ov, "last_auction_price": last_price})

    scored.sort(key=lambda x: -x["retention_score"])

    retentions, ov_used = [], 0
    for p in scored:
        if len(retentions) >= MAX_RETENTIONS:
            break
        if p["is_overseas"] and ov_used >= MAX_OVERSEAS_RETAIN:
            continue
        # Retain at LAST AUCTION PRICE, not market value
        retentions.append({**p, "retention_price": p["last_auction_price"]})
        if p["is_overseas"]:
            ov_used += 1

    ret_cost = round(sum(r["retention_price"] for r in retentions), 2)
    retained_names = {r["name"] for r in retentions}
    released = [p for p in scored if p["name"] not in retained_names]
    buybacks = [p for p in released if p["retention_score"] >= 45][:5]

    return {
        "team": team_name, "short": squad["short"],
        "retentions": retentions, "released": released,
        "buybacks": buybacks,
        "cost": ret_cost, "purse_left": round(PROJECTED_PURSE - ret_cost, 2),
        "overseas_retained": ov_used,
    }


def all_teams_summary() -> List[Dict]:
    return [predict_retentions(t) for t in PSL11_SQUADS]