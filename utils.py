import json
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import streamlit as st

# === Google Sheets ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)

# === OpenAI ===
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_workout(day_type: str, goal: str) -> list:
    prompt = (
        f"Create a {goal.lower()} workout for a '{day_type}' day. "
        "Return ONLY a JSON array of 5 exercises, no explanation.\n"
        "Each must include: name, muscle, equipment, sets (int), reps (string), weight (string 'Auto')."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = response.choices[0].message.content.strip()
        st.text_area("🧠 GPT Raw Output", text, height=200)

        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()

        return json.loads(text)

    except json.JSONDecodeError as je:
        st.error(f"⚠️ GPT JSON Error: {je}")
        return []
    except Exception as e:
        st.error(f"⚠️ OpenAI Error: {e}")
        return []

def log_workout(sheet_url: str, workout_data: list):
    try:
        # Extract the sheet key
        key = sheet_url.split("/d/")[1].split("/")[0].strip()
        st.info(f"Sheet key used: {key}")

        # Open by key — robust & works
        sheet = gc.open_by_key(key).worksheet("WorkoutLog")

        for row in workout_data:
            sheet.append_row([
                row["Date"],
                row["Workout Type"],
                row["Exercise"],
                row["Sets"],
                row["Reps"],
                row["Weight"],
                row["Notes"]
            ])
    except gspread.exceptions.APIError as e:
        st.error("⚠️ Google Sheets API Error — check sharing + tab name!")
        st.exception(e)
        st.stop()
    except PermissionError as e:
        st.error("⚠️ Google says the service account is not an editor for this sheet key.")
        st.info("Check your share settings carefully and re-share if needed.")
        st.exception(e)
        st.stop()
    except Exception as e:
        st.error("⚠️ Unexpected error.")
        st.exception(e)
        st.stop()
