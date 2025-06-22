from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json

# 🔑 Google Sheets Auth
scope = ["https://www.googleapis.com/auth/spreadsheets"]
gspread_creds = st.secrets["gspread_creds"]
credentials = Credentials.from_service_account_info(gspread_creds, scopes=scope)
gc = gspread.authorize(credentials)

# 🧠 OpenAI Auth
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 🔥 Generate workout
def generate_workout(day_type, goal):
    prompt = (
        f"Create a {goal.lower()} workout for a '{day_type}' day. "
        "Return ONLY a JSON array of 5 exercises. Each must have:\n"
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

# ✅ Log workout
def log_workout(sheet_url, workout_data):
    try:
        clean_url = sheet_url.split("/edit")[0]
        sheet = gc.open_by_url(clean_url).worksheet("WorkoutLog")

        for row in workout_data:
            sheet.append_row([
                row["Date"],
                row["Workout Type"],  # ✅ Matches your Sheet header
                row["Exercise"],
                row["Sets"],
                row["Reps"],
                row["Weight"],
                row["Notes"]
            ])
    except gspread.exceptions.APIError:
        st.error("⚠️ Could not access Google Sheet. Check sharing permissions and Sheet name 'WorkoutLog'.")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Unexpected error while logging: {e}")
        st.stop()
