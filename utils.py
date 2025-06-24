# ============================
# === utils.py (Final Hardcore)
# ============================

import json
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from openai import OpenAI

# === Auth ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["gspread_creds"],
    scopes=scope
)
gc = gspread.authorize(creds)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_workout(sheet_key, day_type: str, goal: str):
    """
    Generate an elite workout with real PR + log context.
    """
    # Pull PR Baseline
    pr_sheet = gc.open_by_key(sheet_key).worksheet("PR_Baseline")
    pr_records = pr_sheet.get_all_records()
    pr_data = {row['Exercise Name'].lower(): row for row in pr_records}

    pr_string = f"""
    Squat: {pr_data.get('squat', {}).get('1RM', 'N/A')}
    Bench: {pr_data.get('bench press', {}).get('1RM', 'N/A')}
    Deadlift: {pr_data.get('deadlift', {}).get('1RM', 'N/A')}
    Max push-ups: {pr_data.get('push-ups', {}).get('1RM', 'N/A')}
    Max pull-ups: {pr_data.get('pull-ups', {}).get('1RM', 'N/A')}
    """

    # Pull last logs
    log_sheet = gc.open_by_key(sheet_key).worksheet("WorkoutLog")
    last_logs = [row for row in log_sheet.get_all_records() if row["Workout Type"] == day_type]
    last_logs = sorted(last_logs, key=lambda x: x["Date"], reverse=True)[:3]
    last_str = json.dumps(last_logs)

    prompt = f"""
You are an elite-level strength & functional fitness coach — the caliber of Arnold's secret coach & Hafthor Björnsson's strongman advisor — tasked with crafting a world-class, highly personalized workout plan for today.

Constraints & context:
- Goal: {goal}
- Workout Type: {day_type}
- User’s PRs:
{pr_string}
- Last 3 {day_type} logs:
{last_str}

Rules:
1️⃣ The workout must be elite-level, functional, strongman-capable.
2️⃣ Use advanced programming: RPE, % of PRs, periodization, supersets, cluster sets.
3️⃣ Vary reps for strength + hypertrophy + functional work.
4️⃣ Each exercise must include:
   - name
   - primary_muscle
   - target_muscle_detail
   - equipment
   - sets (int)
   - reps (string)
   - weight (string)
   - superset_group_id (0 means none)
5️⃣ Include at least 1 superset or finisher.
6️⃣ Ensure progression vs. last logs.
7️⃣ Be creative, no repeats.
8️⃣ Return ONLY valid JSON, no text, no code fences.

Mission:
Deliver an elite, challenging, safe, progressive workout — make me stronger than the gods.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()
        return json.loads(text)
    except Exception as e:
        st.error(f"⚠️ OpenAI error: {e}")
        return []

def log_workout(sheet, workout_data: list):
    """
    Append new workout rows.
    """
    for row in workout_data:
        sheet.append_row([
            row["Workout ID"], row["Date"], row["Workout Type"],
            row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
            row["Sets"], row["Reps"], row["Weight"],
            row["Superset Group ID"], row["Notes"]
        ])

def get_workouts_by_date(sheet, target_date: str):
    """
    Get rows matching a specific date.
    """
    return [row for row in sheet.get_all_records() if row["Date"] == target_date]

def overwrite_sheet_with_rows(sheet, rows: list):
    """
    Clear sheet and write given rows.
    """
    sheet.clear()
    if rows:
        sheet.append_row(list(rows[0].keys()))
        for row in rows:
            sheet.append_row(list(row.values()))
