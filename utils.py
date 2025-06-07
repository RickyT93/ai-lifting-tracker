import openai
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Google Sheets setup
scope = ["https://www.googleapis.com/auth/spreadsheets"]
gspread_creds = st.secrets["gspread_creds"]
credentials = Credentials.from_service_account_info(gspread_creds, scopes=scope)
gc = gspread.authorize(credentials)

# OpenAI setup
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🧠 GPT-powered exercise generator
def generate_workout(day_type, goal):
    prompt = (
        f"Create a detailed {goal.lower()} workout for a '{day_type}' day. "
        "Provide 5 exercises with the following fields in JSON format:\n"
        "[\n"
        "  {\n"
        "    'name': 'Exercise Name',\n"
        "    'muscle': 'Targeted Muscle',\n"
        "    'equipment': 'Required Equipment',\n"
        "    'sets': Number of sets,\n"
        "    'reps': 'Reps range',\n"
        "    'weight': 'Auto' (as placeholder)\n"
        "  },\n"
        "  ...\n"
        "]"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )
    text = response["choices"][0]["message"]["content"]
    
    try:
        workout = eval(text, {"__builtins__": None}, {})
        return workout if isinstance(workout, list) else []
    except Exception as e:
        st.error(f"⚠️ GPT response error: {e}")
        return []

# ✅ Workout logger to Google Sheet
def log_workout(sheet_url, workout_data):
    sheet = gc.open_by_url(sheet_url).sheet1
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
