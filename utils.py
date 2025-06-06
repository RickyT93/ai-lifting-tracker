import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import random

# Load credentials from Streamlit secrets
scope = ["https://www.googleapis.com/auth/spreadsheets"]
gspread_creds = st.secrets["gspread_creds"]
credentials = Credentials.from_service_account_info(gspread_creds, scopes=scope)
gc = gspread.authorize(credentials)

# Example exercises database (expand as needed)
EXERCISES = {
    "Push": [
        {"name": "Flat Barbell Bench Press", "muscle": "Chest", "equipment": "Barbell"},
        {"name": "Overhead Press", "muscle": "Shoulders", "equipment": "Barbell"},
        {"name": "Dumbbell Lateral Raise", "muscle": "Shoulders", "equipment": "Dumbbell"},
        {"name": "Incline Dumbbell Press", "muscle": "Chest", "equipment": "Dumbbell"},
    ],
    "Pull": [
        {"name": "Deadlift", "muscle": "Back", "equipment": "Barbell"},
        {"name": "Pull-Ups", "muscle": "Lats", "equipment": "Bodyweight"},
        {"name": "Barbell Rows", "muscle": "Back", "equipment": "Barbell"},
        {"name": "Face Pulls", "muscle": "Rear Delts", "equipment": "Cable"},
    ],
    "Legs": [
        {"name": "Back Squat", "muscle": "Quads", "equipment": "Barbell"},
        {"name": "Romanian Deadlift", "muscle": "Hamstrings", "equipment": "Barbell"},
        {"name": "Leg Press", "muscle": "Glutes", "equipment": "Machine"},
        {"name": "Walking Lunges", "muscle": "Quads", "equipment": "Dumbbell"},
    ]
}

# Reps & weight suggestions based on goal
GOAL_MAP = {
    "Hypertrophy": {"reps": "8–12", "sets": 4},
    "Strength": {"reps": "4–6", "sets": 5},
    "Endurance": {"reps": "12–20", "sets": 3},
}

def generate_workout(day_type, goal):
    selected_exercises = random.sample(EXERCISES[day_type], 3)
    workout = []
    for ex in selected_exercises:
        workout.append({
            "name": ex["name"],
            "muscle": ex["muscle"],
            "equipment": ex["equipment"],
            "sets": GOAL_MAP[goal]["sets"],
            "reps": GOAL_MAP[goal]["reps"],
            "weight": "Auto"  # or use previous logs if desired
        })
    return workout

def log_workout(sheet_url, data):
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
