import json
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import streamlit as st

# === Google Sheets ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["gspread_creds"], scopes=scope
)
gc = gspread.authorize(creds)

# === OpenAI ===
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def generate_workout(day_type: str, goal: str, want_supersets: bool = False) -> list:
    """
    Uses GPT to create a workout with detailed muscle targeting and optional supersets.
    """
    superset_note = "Include 1-2 supersets where appropriate." if want_supersets else ""
    prompt = (
        f"Create a {goal.lower()} workout for a '{day_type}' day. "
        f"{superset_note} "
        "Return ONLY a JSON array of 5 exercises, no explanation. "
        "Each must have: name, precise muscle (e.g. 'Vastus Lateralis' not just 'Quads'), "
        "equipment, sets (int), reps (string), weight ('Auto'), "
        "and superset_group (number if part of a superset, else null)."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()
        return json.loads(text)
    except Exception as e:
        st.error(f"⚠️ OpenAI Error: {e}")
        return []


def log_workout(sheet_url: str, workout_data: list):
    """
    Logs a full workout session to the Google Sheet using the updated schema.
    """
    try:
        key = sheet_url.split("/d/")[1].split("/")[0]
        sheet = gc.open_by_key(key).worksheet("WorkoutLog")

        for row in workout_data:
            sheet.append_row([
                row["Workout ID"],
                row["Date"],
                row["Workout Type"],
                row["Exercise"],
                row["Sets"],
                row["Reps"],
                row["Weight"],
                row["Superset Group"],
                row["Target Muscle"],
                row["Equipment"],
                row["Notes"]
            ])
    except Exception as e:
        st.error(f"⚠️ Google Sheets Error: {e}")
