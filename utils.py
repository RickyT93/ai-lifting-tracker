import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import random

# Exercise bank – TEMP (replace with dynamic API later)
EXERCISES = {
    "Push": [...],  # same as before or expanded
    "Pull": [...],
    "Legs": [...]
}

GOAL_MAP = {
    "Hypertrophy": {"sets": 4, "reps": "8–12"},
    "Strength": {"sets": 5, "reps": "4–6"},
    "Endurance": {"sets": 3, "reps": "12–20"},
}

def generate_workout(day_type, goal):
    return [
        {
            "name": ex["name"],
            "muscle": ex["muscle"],
            "equipment": ex["equipment"],
            "sets": GOAL_MAP[goal]["sets"],
            "reps": GOAL_MAP[goal]["reps"],
            "weight": "Auto"
        }
        for ex in random.sample(EXERCISES[day_type], 3)
    ]

def log_workout(sheet_url, data):
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_url(sheet_url).sheet1
    for row in data:
        sheet.append_row([
            row["Date"],
            row["Workout Type"],
            row["Exercise"],
            row["Sets"],
            row["Reps"],
            row["Weight"],
            row["Notes"]
        ])
