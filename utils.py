import openai
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Set up Google Sheets credentials
scope = ["https://www.googleapis.com/auth/spreadsheets"]
gspread_creds = st.secrets["gspread_creds"]
credentials = Credentials.from_service_account_info(gspread_creds, scopes=scope)
gc = gspread.authorize(credentials)

# Configure OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

# GPT-powered dynamic exercise generator
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
    
    # Clean and parse GPT response
    text = response["choices"][0]["message"]["content"]
    try:
        # Try parsing JSON safely using eval in a safe context
        workout = eval(text, {"__builtins__": None}, {})
        return workout if isinstance(workout, list) else []
    except Exception as e:
        st.error(f"Error parsing GPT response: {e}")
        return []

# Append workout logs to Google Sheets
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
