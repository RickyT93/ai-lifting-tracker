import json
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_workout(gc, sheet_key, day_type, goal):
    """Generate a workout using PRs + last logs and GPT-4o"""
    try:
        pr_sheet = gc.open_by_key(sheet_key).worksheet("PR_Baseline")
        pr_records = pr_sheet.get_all_records()
        pr_data = {row["Exercise Name"]: row["1RM"] for row in pr_records}
    except Exception as e:
        st.error(f"Failed to load PRs: {e}")
        return {"warmup": "", "workout": [], "finisher": ""}

    try:
        log_sheet = gc.open_by_key(sheet_key).worksheet("WorkoutLog")
        logs = log_sheet.get_all_records()
        last_logs = [row for row in logs if row["Workout Type"] == day_type]
        last_logs = sorted(last_logs, key=lambda x: x["Date"], reverse=True)[:3]
    except Exception as e:
        st.warning("No previous logs found.")
        last_logs = []

    prompt = build_workout_prompt(goal, day_type, pr_data, last_logs)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        raw_text = response.choices[0].message.content.strip()
        clean_text = clean_json_response(raw_text)
        result = json.loads(clean_text)
        validate_workout_response(result)
        return {
            "warmup": result.get("warmup", ""),
            "workout": result.get("workout", []),
            "finisher": result.get("finisher", "")
        }
    except Exception as e:
        st.error(f"⚠️ Workout generation failed: {e}")
        return {"warmup": "", "workout": [], "finisher": ""}

def build_workout_prompt(goal, day_type, pr_data, last_logs):
    pr_lines = "\n".join([f"  - {k}: {v}" for k, v in pr_data.items()])
    logs_section = json.dumps(last_logs, indent=2) if last_logs else "None"
    return f"""
You are an elite strength coach building a {goal}-focused {day_type} workout.

User’s PRs:
{pr_lines}

Recent {day_type} Logs:
{logs_section}

Rules:
1. Return ONLY valid JSON with keys: warmup (string), workout (list), finisher (string).
2. Each workout item: name, primary_muscle, target_muscle_detail, equipment, sets, reps, weight, superset_group_id.
3. Must include progression logic based on last logs.
4. Be creative and apply strongman logic: sleds, cables, tempo, clusters, etc.
"""

def clean_json_response(text):
    """Remove markdown wrapping from GPT output"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def validate_workout_response(result):
    """Ensure GPT result is valid and has the right shape"""
    if not isinstance(result, dict):
        raise ValueError("GPT response is not a dictionary.")
    for key in ["warmup", "workout", "finisher"]:
        if key not in result:
            raise ValueError(f"Missing key: {key}")
    if not isinstance(result["workout"], list):
        raise ValueError("Workout must be a list.")
    for ex in result["workout"]:
        for req in ["name", "primary_muscle", "target_muscle_detail", "equipment", "sets", "reps", "weight", "superset_group_id"]:
            if req not in ex:
                raise ValueError(f"Exercise missing key: {req}")

def log_workout(sheet, workout_data):
    """Log to Google Sheets with fallback error handling"""
    try:
        rows = []
        for row in workout_data:
            rows.append([
                row["Workout ID"], row["Date"], row["Workout Type"],
                row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
                row["Sets"], row["Reps"], row["Weight"],
                row["Superset Group ID"], row["Notes"]
            ])
        sheet.append_rows(rows)
        return True
    except Exception as e:
        st.error(f"Google Sheets log failed: {e}")
        return False

def get_workouts_by_date(sheet, target_date):
    try:
        return [row for row in sheet.get_all_records() if row["Date"] == target_date]
    except Exception as e:
        st.error(f"Failed to fetch past workouts: {e}")
        return []

def overwrite_sheet_with_rows(sheet, rows):
    try:
        sheet.clear()
        if rows:
            sheet.append_row(list(rows[0].keys()))
            for row in rows:
                sheet.append_row(list(row.values()))
        return True
    except Exception as e:
        st.error(f"Overwrite failed: {e}")
        return False
