# ============================
# === utils.py — RAGNARÖK LAB
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

# === Evolved Generate Workout ===
def generate_workout(sheet_key, workout_type, goal):
    """
    Pull PR_Baseline + last logs → OpenAI.
    """

    try:
        pr_sheet = gc.open_by_key(sheet_key).worksheet("PR_Baseline")
        pr_records = pr_sheet.get_all_records()
        pr_data = { row["Exercise Name"]: row for row in pr_records }

        log_sheet = gc.open_by_key(sheet_key).worksheet("WorkoutLog")
        logs = log_sheet.get_all_records()
        last_logs = sorted(
            [row for row in logs if row["Workout Type"] == workout_type],
            key=lambda x: x["Date"], reverse=True
        )[:3]

    except Exception as e:
        st.error(f"⚠️ Could not load PRs or logs: {e}")
        return []

    # Evolved prompt
    prompt = f"""
You are an elite-level strength & functional fitness coach — the caliber of Arnold's secret coach & Hafthor Björnsson's strongman advisor — tasked with crafting a world-class, highly personalized workout plan for today.

Context:
- Goal: {goal}
- Workout Type: {workout_type}
- User PRs: {json.dumps(pr_data)}
- Last 3 {workout_type} logs: {json.dumps(last_logs)}

Rules:
1️⃣ 5+ exercises, advanced progression.
2️⃣ Use RPE, %PR, cluster sets, supersets.
3️⃣ Show creativity, elite level.
4️⃣ Each exercise must have:
  - name
  - primary_muscle
  - target_muscle_detail
  - equipment
  - sets (int)
  - reps (string)
  - weight (string)
  - superset_group_id (0 means none)
5️⃣ Return ONLY a valid JSON array. No text.

Make this session so brutal that even Odin weeps.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()

        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []

    except Exception as e:
        st.error(f"⚠️ OpenAI error: {e}")
        return []

# === Log Workout ===
def log_workout(sheet, workout_data: list):
    for row in workout_data:
        sheet.append_row([
            row["Workout ID"], row["Date"], row["Workout Type"],
            row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
            row["Sets"], row["Reps"], row["Weight"],
            row["Superset Group ID"], row["Notes"]
        ])

# === Helpers ===
def get_workouts_by_date(sheet, target_date: str):
    return [row for row in sheet.get_all_records() if row["Date"] == target_date]

def overwrite_sheet_with_rows(sheet, rows: list):
    sheet.clear()
    if rows:
        sheet.append_row(list(rows[0].keys()))
        for row in rows:
            sheet.append_row(list(row.values()))
