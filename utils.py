from datetime import datetime
from openai import OpenAI
import gspread
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

def get_today():
    return datetime.today().strftime("%Y-%m-%d")

def get_user_profile(sheet_url):
    gc = gspread.service_account()
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.worksheet("UserProfile")
    data = worksheet.get_all_records()
    profile = {row["Exercise"]: row for row in data}
    return profile

def calculate_weight(pr, percent):
    return round(pr * percent)

def generate_workout(day_type, sheet_url):
    messages = [
        {"role": "system", "content": "You are a personal trainer creating gym workouts."},
        {"role": "user", "content": f"Create a {day_type} workout with 5 exercises including muscles and equipment. Return only JSON in this format:\n[{'{'}'name':'','muscle':'','equipment':''{'}'}]"}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    exercises = eval(response.choices[0].message.content)

    # Fetch PRs
    profile = get_user_profile(sheet_url)

    for ex in exercises:
        pr_entry = profile.get(ex["name"], None)
        if pr_entry:
            pr = pr_entry.get("1RM", 100)
        else:
            pr = 100  # fallback
        ex["sets"] = 4
        ex["reps"] = 12
        ex["weight"] = calculate_weight(pr, 0.7)  # 70% of 1RM
    return exercises

def log_workout(sheet_url, day_type, date_str, workout_data, notes):
    gc = gspread.service_account()
    sh = gc.open_by_url(sheet_url)
    try:
        sheet = sh.worksheet("WorkoutLog")
    except gspread.exceptions.WorksheetNotFound:
        sheet = sh.add_worksheet(title="WorkoutLog", rows="1000", cols="20")
        sheet.append_row(["Date", "Day Type", "Exercise", "Muscle", "Equipment", "Sets", "Reps", "Weight", "Notes"])

    for ex in workout_data:
        sheet.append_row([
            date_str,
            day_type,
            ex["name"],
            ex["muscle"],
            ex["equipment"],
            ex["sets"],
            ex["reps"],
            ex["weight"],
            notes
        ])
