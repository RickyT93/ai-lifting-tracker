import re
import datetime
import gspread
from openai import OpenAI
import streamlit as st
from google.oauth2.service_account import Credentials

# Authenticate with OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Authenticate with Google Sheets using secrets
gspread_creds = {
    "type": st.secrets["gspread_creds"]["type"],
    "project_id": st.secrets["gspread_creds"]["project_id"],
    "private_key_id": st.secrets["gspread_creds"]["private_key_id"],
    "private_key": st.secrets["gspread_creds"]["private_key"],
    "client_email": st.secrets["gspread_creds"]["client_email"],
    "client_id": st.secrets["gspread_creds"]["client_id"],
    "auth_uri": st.secrets["gspread_creds"]["auth_uri"],
    "token_uri": st.secrets["gspread_creds"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["gspread_creds"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["gspread_creds"]["client_x509_cert_url"],
}

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(gspread_creds, scopes=scope)
gc = gspread.authorize(credentials)


def extract_sheet_id(sheet_url):
    """Extracts the Google Sheet ID from the provided URL."""
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    return match.group(1) if match else None


def get_today():
    return datetime.date.today().strftime("%Y-%m-%d")


def generate_workout(day_type, goal, sheet_url):
    """Generates a workout based on the type and goal."""
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError("Invalid Google Sheet URL")

    sheet = gc.open_by_key(sheet_id)
    try:
        prs_worksheet = sheet.worksheet("PRs")
        pr_data = prs_worksheet.get_all_records()
    except Exception:
        pr_data = []

    # Build OpenAI prompt
    messages = [
        {
            "role": "system",
            "content": "You are a personal trainer who builds smart strength and hypertrophy workouts."
        },
        {
            "role": "user",
            "content": f"Generate a {goal.lower()} {day_type} workout with sets, reps, and weight based on these PRs: {pr_data}. "
                       f"Include 5 exercises. For each, list: name, target muscles, equipment, sets, reps, weight."
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    text = response.choices[0].message.content

    # Parse GPT response
    exercises = []
    for line in text.strip().split("\n"):
        if line.strip() and re.match(r"^\d+\.", line):
            parts = line.split(". ", 1)
            if len(parts) == 2:
                details = parts[1]
                segments = [s.strip() for s in details.split("|")]
                name = segments[0].split("-")[0].strip()
                muscle = segments[0].split(":")[-1].strip() if "Muscle" in segments[0] else "TBD"
                equipment = "TBD"
                sets = "3"
                reps = "10-12"
                weight = "Based on PRs"

                for seg in segments:
                    if "Muscle" in seg:
                        muscle = seg.split(":")[-1].strip()
                    elif "Equipment" in seg:
                        equipment = seg.split(":")[-1].strip()
                    elif "Sets" in seg:
                        sets = seg.split(":")[-1].strip()
                    elif "Reps" in seg:
                        reps = seg.split(":")[-1].strip()
                    elif "Weight" in seg:
                        weight = seg.split(":")[-1].strip()

                exercises.append({
                    "name": name,
                    "muscle": muscle,
                    "equipment": equipment,
                    "sets": sets,
                    "reps": reps,
                    "weight": weight
                })

    return exercises


def log_workout(sheet_url, workout_data):
    """Logs the workout into the WorkoutLog sheet."""
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError("Invalid Google Sheet URL")

    sheet = gc.open_by_key(sheet_id)
    try:
        log_worksheet = sheet.worksheet("WorkoutLog")
    except gspread.exceptions.WorksheetNotFound:
        log_worksheet = sheet.add_worksheet(title="WorkoutLog", rows="1000", cols="7")
        log_worksheet.append_row(["Date", "Workout Type", "Exercise", "Sets", "Reps", "Weight", "Notes"])

    for ex in workout_data:
        log_worksheet.append_row([
            ex.get("Date", ""),
            ex.get("Workout Type", ""),
            ex.get("Exercise", ""),
            ex.get("Sets", ""),
            ex.get("Reps", ""),
            ex.get("Weight", ""),
            ex.get("Notes", "")
        ])
