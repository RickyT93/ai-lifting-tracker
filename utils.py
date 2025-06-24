# ============================
# === utils.py (Cleaned Up)
# ============================

import json
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from openai import OpenAI

# === Auth ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["gspread_creds"],
    scopes=scope
)
gc = gspread.authorize(creds)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# === Generate workout using GPT ===
def generate_workout(day_type: str, goal: str) -> list:
    """
    Calls OpenAI to generate a workout.
    """
    prompt = f"""
You are an elite strength coach designing a {goal.lower()} workout for a '{day_type}' day.
Rules:
- 5 exercises.
- Balanced compound & isolation.
- For each: 
  • name
  • primary_muscle
  • target_muscle_detail
  • equipment
  • sets (int)
  • reps (string)
  • weight ('Auto')
  • superset_group_id (int)

Return ONLY valid JSON.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()

        return json.loads(text)

    except json.JSONDecodeError as je:
        st.error(f"⚠️ GPT JSON error: {je}")
        return []
    except Exception as e:
        st.error(f"⚠️ OpenAI error: {e}")
        return []

# === Log workout ===
def log_workout(sheet, workout_data: list):
    """
    Append new workout rows.
    """
    for row in workout_data:
        sheet.append_row([
            row["Workout ID"], row["Date"], row["Workout Type"],
            row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
            row["Sets"], row["Reps"], row["Weight"],
            row["Superset Group ID"], row["Notes"]
        ])

# === Helpers ===

def get_workouts_by_date(sheet, target_date: str):
    """
    Get rows matching a specific date.
    """
    return [row for row in sheet.get_all_records() if row["Date"] == target_date]

def overwrite_sheet_with_rows(sheet, rows: list):
    """
    Clear sheet and write given rows.
    """
    sheet.clear()
    if rows:
        sheet.append_row(list(rows[0].keys()))
        for row in rows:
            sheet.append_row(list(row.values()))
