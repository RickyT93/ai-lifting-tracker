# utils.py

import json
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from openai import OpenAI

# === Google Sheets Auth ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)

# === OpenAI Auth ===
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_workout(day_type: str, goal: str) -> list:
    """
    Generate a smart workout using GPT-4o with a precise muscle-level and superset detail.
    """
    prompt = f"""
You are an elite strength coach designing a {goal.lower()} workout for a '{day_type}' day.
Use modern methods inspired by PHUL, PHAT, and Arnold splits.

Rules:
- 5 exercises only.
- Balanced compound & isolation.
- Realistic sets & reps for goal.
- Each exercise must include:
  • name
  • primary_muscle (top-level)
  • target_detail (precise muscle, e.g., Lateral Deltoid)
  • equipment
  • sets (int)
  • reps (string)
  • weight ('Auto')
  • superset_group ('1' if none; same ID for paired supersets)

Return ONLY a valid JSON array, no explanations.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        text = response.choices[0].message.content.strip()

        # Clean up any code blocks if present
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()

        return json.loads(text)

    except json.JSONDecodeError as je:
        st.error(f"⚠️ GPT JSON Error: {je}")
        return []
    except Exception as e:
        st.error(f"⚠️ OpenAI Error: {e}")
        return []


def log_workout(sheet_url: str, workout_data: list):
    """
    Log the structured workout data to Google Sheets.
    """
    try:
        key = sheet_url.split("/d/")[1].split("/")[0].strip()
        st.info(f"🔑 Sheet key: {key}")

        sheet = gc.open_by_key(key).worksheet("WorkoutLog")

        for row in workout_data:
            sheet.append_row([
                row["Workout ID"],
                row["Date"],
                row["Workout Type"],
                row["Exercise"],
                row["Primary Muscle"],
                row["Target Muscle Detail"],
                row["Sets"],
                row["Reps"],
                row["Weight"],
                row["Superset Group ID"],
                row["Notes"]
            ])

    except gspread.exceptions.APIError as e:
        st.error("⚠️ Google Sheets API Error — check sharing + tab name!")
        st.exception(e)
        st.stop()
    except Exception as e:
        st.error("⚠️ Unexpected error during logging.")
        st.exception(e)
        st.stop()
