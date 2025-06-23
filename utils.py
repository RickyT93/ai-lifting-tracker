import json
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import streamlit as st

# --- Google Sheets setup ---
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds_info = st.secrets["gspread_creds"]
creds = Credentials.from_service_account_info(creds_info, scopes=scope)
gc = gspread.authorize(creds)

# --- OpenAI setup ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_workout(day_type: str, goal: str) -> list:
    """
    Generate a JSON-formatted workout using OpenAI:
    5 exercises, each with 
    name, muscle, equipment, sets, reps, weight ("Auto").
    """
    prompt = (
        f"Create a {goal.lower()} workout for a '{day_type}' day.\n"
        "Return ONLY a JSON array of 5 exercises. No extra explanation.\n"
        "Each exercise must include:\n"
        "name (string), muscle (string), equipment (string),\n"
        "sets (integer), reps (string), weight (string, always 'Auto')\n\n"
        "Example output:\n"
        '[{\"name\":\"Squat\",\"muscle\":\"Quads\",\"equipment\":\"Barbell\",'
        '"sets\":4,\"reps\":\"8-10\",\"weight\":\"Auto\"}, ...]'
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = resp.choices[0].message.content.strip()
        st.text_area("🧠 GPT Raw Output", text, height=200)

        # Strip markdown backticks if present
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1])

        return json.loads(text)

    except json.JSONDecodeError as je:
        st.error(f"⚠️ GPT returned invalid JSON: {je}")
        return []
    except Exception as e:
        st.error(f"⚠️ Unexpected error during generation: {e}")
        return []

def log_workout(sheet_url: str, workout_data: list):
    """
    Append each workout row to the "WorkoutLog" sheet.
    """
    clean_url = sheet_url.split("/edit")[0]
    sheet = gc.open_by_url(clean_url).worksheet("WorkoutLog")

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
