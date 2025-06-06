import re
import datetime
import streamlit as st
import gspread
from openai import OpenAI
from google.oauth2.service_account import Credentials

# OpenAI API key (pulled from st.secrets)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Google Sheets credentials setup from st.secrets
creds_dict = {key: value for key, value in st.secrets["gspread_creds"].items()}
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

scopes = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)

# Helper functions
def extract_sheet_id(sheet_url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    return match.group(1) if match else None

def get_today():
    return datetime.date.today().strftime("%Y-%m-%d")

def generate_workout(day_type, sheet_url):
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError("Invalid Google Sheet URL")

    sheet = gc.open_by_key(sheet_id)

    # Pull PRs from PRs tab
    try:
        prs_worksheet = sheet.worksheet("PRs")
        pr_data = prs_worksheet.get_all_records()
    except Exception:
        pr_data = []

    messages = [
        {"role": "system", "content": "You are a personal trainer specializing in hypertrophy and strength programming."},
        {"role": "user", "content": f"Generate a {day_type} workout with 5 exercises based on these PRs: {pr_data}. Use hypertrophy style (8–12 reps). Give sets, reps, and weight suggestions. Output format: numbered list with exercise name, muscles, equipment, sets, reps, weight."}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    text = response.choices[0].message.content

    # Parse GPT response
    exercises = []
    for line in text.strip().split("\n"):
        if line.strip() and line[0].isdigit():
            parts = line.split(". ", 1)
            if len(parts) == 2:
                name_block = parts[1]
                exercises.append({
                    "name": name_block.split(" - ")[0].strip(),
                    "muscle": "Unknown",  # Optional to parse
                    "equipment": "Unknown",
                    "sets": "3",
                    "reps": "10-12",
                    "weight": "Based on PR"
                })
    return exercises

def log_workout(sheet_url, workout_type, exercises):
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError("Invalid Google Sheet URL")

    sheet = gc.open_by_key(sheet_id)
    try:
        log_worksheet = sheet.worksheet("WorkoutLog")
    except gspread.exceptions.WorksheetNotFound:
        log_worksheet = sheet.add_worksheet(title="WorkoutLog", rows="1000", cols="7")
        log_worksheet.append_row(["Date", "Workout Type", "Exercise", "Sets", "Reps", "Weight", "Notes"])

    today = get_today()
    for ex in exercises:
        log_worksheet.append_row([
            today,
            workout_type,
            ex.get("name", ""),
            ex.get("sets", ""),
            ex.get("reps", ""),
            ex.get("weight", ""),
            ex.get("notes", "")
        ])
