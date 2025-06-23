from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json

# 🔑 Google Sheets setup
scope = ["https://www.googleapis.com/auth/spreadsheets"]
gspread_creds = st.secrets["gspread_creds"]
credentials = Credentials.from_service_account_info(gspread_creds, scopes=scope)
gc = gspread.authorize(credentials)

# 🧠 OpenAI setup
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 📊 ---- New: Get last log for an exercise ----
def get_last_log(sheet_url, exercise_name):
    clean_url = sheet_url.split("/edit")[0]
    sheet = gc.open_by_url(clean_url).worksheet("WorkoutLog")
    records = sheet.get_all_records()

    for row in reversed(records):
        if row.get("Exercise") == exercise_name:
            return row  # last log for this exercise
    return None  # no previous log

# 📈 ---- New: Smart progression ----
def calculate_next_weight(last_weight, last_note):
    try:
        last_weight = float(last_weight)
    except:
        return "Auto"

    note = str(last_note).lower()
    if "easy" in note:
        next_weight = last_weight * 1.025
    elif "heavy" in note:
        next_weight = last_weight  # retry
    else:
        next_weight = last_weight

    # Cap jump at +5%
    next_weight = min(next_weight, last_weight * 1.05)
    return round(next_weight, 1)

# 🏋️ ---- GPT workout generator ----
def generate_workout(sheet_url, day_type, goal):
    # 📌 Optional: use previous log for progression context
    examples = []
    for ex_name in ["Bench Press", "Overhead Press", "Squat"]:  # top frequent
        last = get_last_log(sheet_url, ex_name)
        if last:
            next_weight = calculate_next_weight(last["Weight"], last["Notes"])
            examples.append(f"{ex_name} next weight suggestion: {next_weight} lbs based on last note '{last['Notes']}'")

    prompt = (
        f"Create a {goal.lower()} workout for a '{day_type}' day. "
        "Return ONLY a JSON array of 5 exercises. No explanation. "
        f"Here are prior examples: {examples}. "
        "Each must include:\n"
        "- name (string)\n"
        "- muscle (string)\n"
        "- equipment (string)\n"
        "- sets (int)\n"
        "- reps (string)\n"
        "- weight (string, suggest progression if you know else use 'Auto')\n"
        "JSON only!"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = response.choices[0].message.content.strip()
        st.text_area("🧠 GPT Raw Output", text, height=200)

        # Clean up possible code fences
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

# ✅ ---- Log workout ----
def log_workout(sheet_url, workout_data):
    clean_url = sheet_url.split("/edit")[0]
    sheet = gc.open_by_url(clean_url).worksheet("WorkoutLog")

    for row in workout_data:
        st.write("Appending row:", row)  # debug
        sheet.append_row([
            row["Date"],
            row["Workout Type"],  # must match "Workout Type"
            row["Exercise"],
            row["Sets"],
            row["Reps"],
            row["Weight"],
            row["Notes"]
        ])
