from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json

# 🔑 Google Sheets credentials
scope = ["https://www.googleapis.com/auth/spreadsheets"]
gspread_creds = st.secrets["gspread_creds"]
credentials = Credentials.from_service_account_info(gspread_creds, scopes=scope)
gc = gspread.authorize(credentials)

# 🧠 OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ✅ Helper: extract Sheet ID safely from ANY pasted URL
def extract_sheet_key(sheet_url):
    return sheet_url.split("/d/")[1].split("/")[0]

# ✅ Generate workout using GPT-4o
def generate_workout(day_type, goal):
    prompt = (
        f"Create a {goal.lower()} workout for a '{day_type}' day. "
        "Return ONLY a JSON array of 5 exercises. Each exercise must include:\n"
        "- name (string)\n"
        "- muscle (string)\n"
        "- equipment (string)\n"
        "- sets (integer)\n"
        "- reps (string)\n"
        "- weight (string, always 'Auto')\n\n"
        "Example:\n"
        '[{\"name\": \"Squat\", \"muscle\": \"Quads\", \"equipment\": \"Barbell\", \"sets\": 4, \"reps\": \"8-10\", \"weight\": \"Auto\"}]'
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = response.choices[0].message.content.strip()
        st.text_area("🧠 GPT Raw Output", text, height=200)

        # Remove code block syntax if any
        if text.startswith("```json") and text.endswith("```"):
            text = text[len("```json"):-3].strip()
        elif text.startswith("```") and text.endswith("```"):
            text = text[3:-3].strip()

        workout = json.loads(text)
        return workout if isinstance(workout, list) else []
    except json.JSONDecodeError as je:
        st.error(f"⚠️ GPT returned invalid JSON: {je}")
        return []
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {e}")
        return []

# ✅ Log workout to Google Sheets
def log_workout(sheet_url, workout_data):
    try:
        key = extract_sheet_key(sheet_url)
        sheet = gc.open_by_key(key).worksheet("WorkoutLog")

        for row in workout_data:
            sheet.append_row([
                row["Date"],
                row["Workout Type"],
                row["Exercise"],
                row["Sets"],
                row["Reps"],
                row["Weight"],
                row["Notes"]
            ])
    except gspread.exceptions.APIError as e:
        st.error("⚠️ Google Sheets API Error — check permissions and Sheet ID.")
        st.exception(e)
    except Exception as e:
        st.error("⚠️ Unexpected error while logging workout.")
        st.exception(e)
