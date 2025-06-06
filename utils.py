from datetime import date
from openai import OpenAI
import streamlit as st
import gspread_helper

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

def get_today():
    return date.today().strftime("%Y-%m-%d")

def get_user_profile(sheet_url):
    gc = gspread_helper.get_gsheet_connection()
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.worksheet("User_Profile")
    data = worksheet.get_all_records()
    return data[0] if data else None

def generate_workout(day_type, profile):
    messages = [
        {"role": "system", "content": f"You are a certified strength coach designing gym workouts."},
        {"role": "user", "content": f"Design a {day_type} workout for someone with 1RM: Squat {profile['1RM_Squat']} lbs, Bench {profile['1RM_Bench']} lbs, Deadlift {profile['1RM_Deadlift']} lbs. Their goal is {profile['Goal']}. Include 5 exercises with sets, reps, and weight suggestions. Format it as JSON list of objects with: name, muscle, equipment, sets, reps, weight."}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    content = response.choices[0].message.content
    try:
        return eval(content)  # Ensure this returns a list of dicts
    except Exception:
        st.error("Failed to parse GPT response.")
        return []

def log_workout(sheet_url, today, day_type, workout, notes):
    gc = gspread_helper.get_gsheet_connection()
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.worksheet("Workout_Log")
    for ex in workout:
        worksheet.append_row([
            today,
            day_type,
            ex["name"],
            ex.get("sets", ""),
            ex.get("reps", ""),
            ex.get("weight", ""),
            notes.get(ex["name"], "")
        ])
