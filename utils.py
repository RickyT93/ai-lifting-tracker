# ============================
# === utils.py (Elite Version)
# ============================

import json
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from openai import OpenAI

# === Google Sheets Auth ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_workout(sheet_key, day_type, goal):
    """
    Generate an elite-level workout using PRs + logs.
    """
    # === Get PRs ===
    pr_sheet = gc.open_by_key(sheet_key).worksheet("PR_Baseline")
    pr_records = pr_sheet.get_all_records()
    pr_data = {row["Exercise Name"]: row["1RM"] for row in pr_records}

    # === Get last 3 logs ===
    log_sheet = gc.open_by_key(sheet_key).worksheet("WorkoutLog")
    logs = log_sheet.get_all_records()
    last_logs = [row for row in logs if row["Workout Type"] == day_type]
    last_logs = sorted(last_logs, key=lambda x: x["Date"], reverse=True)[:3]

    # === Ultimate Prompt ===
    prompt = f"""
You are an elite-level strength & functional fitness coach — the caliber of Arnold Schwarzenegger's secret coach and Hafthor Björnsson's strongman advisor — tasked with designing an exceptional, highly personalized workout plan for today.

Constraints & context:
- Goal: {goal}
- Workout Type: {day_type}
- User’s PRs:
  - Squat: {pr_data.get('Squat', 'N/A')}
  - Bench Press: {pr_data.get('Bench Press', 'N/A')}
  - Deadlift: {pr_data.get('Deadlift', 'N/A')}
  - Push-ups: {pr_data.get('Push-ups', 'N/A')}
  - Pull-ups: {pr_data.get('Pull-ups', 'N/A')}
- Last 3 {day_type} logs:
{json.dumps(last_logs)}

Rules:
1️⃣ The workout must be elite-level, functional, strongman-capable.
2️⃣ Use advanced programming: RPE, %PRs, periodization, supersets, cluster sets, auto-regulation.
3️⃣ Include a warm-up tailored to today’s lifts.
4️⃣ Include a finisher for failure + conditioning.
5️⃣ Be creative: free weights, cables, machines, sleds, strongman implements — no limits.
6️⃣ Each exercise must include:
   - name
   - primary_muscle
   - target_muscle_detail
   - equipment
   - sets (int)
   - reps (string, e.g. "5-8 @ RPE 8")
   - weight (string, % of PR if relevant)
   - superset_group_id (0 = none)
7️⃣ Must have at least 1 superset or finisher circuit.
8️⃣ Ensure progression vs. last logs.
9️⃣ Be creative — no boring repeats.
🔟 Return ONLY valid JSON — no explanations, no text.

Mission:
Deliver a workout so savage it could forge a Norse god — safe, progressive, worthy of RAGNARÖK LAB.
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

    except json.JSONDecodeError as je:
        st.error(f"⚠️ GPT JSON error: {je}")
        return []
    except Exception as e:
        st.error(f"⚠️ OpenAI error: {e}")
        return []

def log_workout(sheet, workout_data):
    """
    Append rows to WorkoutLog.
    """
    for row in workout_data:
        sheet.append_row([
            row["Workout ID"], row["Date"], row["Workout Type"],
            row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
            row["Sets"], row["Reps"], row["Weight"],
            row["Superset Group ID"], row["Notes"]
        ])

def get_workouts_by_date(sheet, target_date):
    return [row for row in sheet.get_all_records() if row["Date"] == target_date]

def overwrite_sheet_with_rows(sheet, rows):
    sheet.clear()
    if rows:
        sheet.append_row(list(rows[0].keys()))
        for row in rows:
            sheet.append_row(list(row.values()))
