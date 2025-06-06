# Updated version of the utils.py file incorporating Google Sheet handling and AI-generated workouts
import os
import re
import datetime
import gspread
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client using environment variable or directly with API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets authentication
gc = gspread.service_account(filename='gspread_creds.json')


def extract_sheet_id(sheet_url):
    """Extract the sheet ID from a full Google Sheets URL."""
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    return match.group(1) if match else None


def get_today():
    return datetime.date.today().strftime("%Y-%m-%d")


def generate_workout(day_type, sheet_url):
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError("Invalid Google Sheet URL")

    # Open the sheet
    sheet = gc.open_by_key(sheet_id)

    # Fetch PRs
    try:
        prs_worksheet = sheet.worksheet("PRs")
        pr_data = prs_worksheet.get_all_records()
    except Exception as e:
        pr_data = []

    messages = [
        {"role": "system", "content": "You are a personal trainer specializing in strength and hypertrophy workouts."},
        {"role": "user", "content": f"Generate a {day_type} workout with sets, reps, and weight suggestions based on these PRs: {pr_data}. Goal: hypertrophy. Provide a list of 5 exercises including name, muscle, equipment, sets, reps, and weight."}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    text = response.choices[0].message.content

    # Parse GPT output into structured list (simple parser for now)
    exercises = []
    for line in text.strip().split("\n"):
        if line and any(char.isdigit() for char in line):
            parts = line.split(". ", 1)
            if len(parts) == 2:
                name_block = parts[1]
                exercises.append({
                    "name": name_block.split(" - ")[0].strip(),
                    "muscle": "Unknown",  # Optionally parse if included
                    "equipment": "Unknown",
                    "sets": "3",
                    "reps": "10-12",
                    "weight": "Based on PRs"
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
