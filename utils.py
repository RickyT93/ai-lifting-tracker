import os
import re
import datetime
import gspread
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets client
gc = gspread.service_account(filename='gspread_creds.json')


def extract_sheet_id(sheet_url):
    """Extract the Google Sheet ID from the full URL."""
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    return match.group(1) if match else None


def get_today():
    return datetime.date.today().strftime("%Y-%m-%d")


def generate_workout(day_type, goal, sheet_url):
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError("Invalid Google Sheet URL")

    # Open the sheet and fetch PRs
    sheet = gc.open_by_key(sheet_id)
    try:
        prs_worksheet = sheet.worksheet("PRs")
        pr_data = prs_worksheet.get_all_records()
    except Exception:
        pr_data = []

    # Construct prompt for GPT
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

    # Parse response
    exercises = []
    for line in text.strip().split("\n"):
        if line.strip() and re.match(r"^\d+\.", line):
            parts = line.split(". ", 1)
            if len(parts) == 2:
                details = parts[1].strip()
                name = details.split("-")[0].strip()
                exercises.append({
                    "name": name,
                    "muscle": "TBD",
                    "equipment": "TBD",
                    "sets": "3",
                    "reps": "10-12",
                    "weight": "Based on PRs"
                })

    return exercises


def log_workout(sheet_url, exercises):
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError("Invalid Google Sheet URL")

    sheet = gc.open_by_key(sheet_id)
    try:
        log_worksheet = sheet.worksheet("WorkoutLog")
    except gspread.exceptions.WorksheetNotFound:
        log_worksheet = sheet.add_worksheet(title="WorkoutLog", rows="1000", cols="7")
        log_worksheet.append_row(["Date", "Workout Type", "Exercise", "Sets", "Reps", "Weight", "Notes"])

    for ex in exercises:
        log_worksheet.append_row([
            ex.get("Date", ""),
            ex.get("Workout Type", ""),
            ex.get("Exercise", ""),
            ex.get("Sets", ""),
            ex.get("Reps", ""),
            ex.get("Weight", ""),
            ex.get("Notes", "")
        ])
