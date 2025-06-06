import random
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json

# Load credentials from .streamlit/secrets.toml
scope = ["https://www.googleapis.com/auth/spreadsheets"]
gspread_creds = st.secrets["gspread_creds"]
credentials = Credentials.from_service_account_info(gspread_creds, scopes=scope)
client = gspread.authorize(credentials)

# Sample exercise bank
exercise_bank = {
    "Push": [
        {"name": "Incline Dumbbell Press", "muscle": "Chest", "equipment": "Dumbbell"},
        {"name": "Flat Barbell Bench Press", "muscle": "Chest", "equipment": "Barbell"},
        {"name": "Overhead Press", "muscle": "Shoulders", "equipment": "Barbell"},
        {"name": "Dumbbell Lateral Raise", "muscle": "Shoulders", "equipment": "Dumbbell"},
        {"name": "Cable Triceps Pushdown", "muscle": "Triceps", "equipment": "Cable"}
    ],
    "Pull": [
        {"name": "Barbell Row", "muscle": "Back", "equipment": "Barbell"},
        {"name": "Lat Pulldown", "muscle": "Back", "equipment": "Cable"},
        {"name": "Face Pulls", "muscle": "Rear Delts", "equipment": "Cable"},
        {"name": "Dumbbell Curls", "muscle": "Biceps", "equipment": "Dumbbell"},
        {"name": "Preacher Curl", "muscle": "Biceps", "equipment": "Barbell"}
    ],
    "Legs": [
        {"name": "Back Squat", "muscle": "Quads", "equipment": "Barbell"},
        {"name": "Romanian Deadlift", "muscle": "Hamstrings", "equipment": "Barbell"},
        {"name": "Leg Press", "muscle": "Quads", "equipment": "Machine"},
        {"name": "Walking Lunges", "muscle": "Glutes", "equipment": "Dumbbell"},
        {"name": "Calf Raise", "muscle": "Calves", "equipment": "Machine"}
    ]
}

# Sets/Reps/Weights Generator
def generate_workout(day_type, goal):
    base = exercise_bank.get(day_type, [])
    selected = random.sample(base, 3)
    for ex in selected:
        if goal == "Hypertrophy":
            ex.update({"sets": 4, "reps": "8–12", "weight": "Moderate"})
        elif goal == "Strength":
            ex.update({"sets": 5, "reps": "4–6", "weight": "Heavy"})
        else:
            ex.update({"sets": 3, "reps": "12–20", "weight": "Light"})
    return selected

# Logger
def log_workout(sheet_url, workout_data):
    sheet = client.open_by_url(sheet_url).sheet1
    for row in workout_data:
        sheet.append_row(list(row.values()))
