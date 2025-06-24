# ==============================
# === RAGNARÖK LAB (Final Polished)
# ==============================

import streamlit as st
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import json

# === CONFIG ===
st.set_page_config(
    page_title="RAGNARÖK LAB",
    layout="wide"
)

# === CUSTOM STYLE ===
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap');

body, div, p, label, span, input, textarea {{
  color: #FFF !important;
}}

body {{
  background: linear-gradient(rgba(0,0,0,0.88), rgba(0,0,0,0.88)),
              url('https://raw.githubusercontent.com/RickyT93/ai-lifting-tracker/main/A41FF6F0-219D-4EB8-AAFD-F4755DEF68BF.jpeg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}}

h1 {{
  font-family: 'UnifrakturCook', cursive;
  font-size: 7em;
  color: #FFF;
  text-align: center;
  text-shadow: 4px 4px #000;
  margin-top: 80px;
}}

h2, h3, h4, h5, h6 {{
  color: #FFF;
}}

.stButton>button {{
  background: #000;
  color: #FF0000;
  border: 2px solid #FF0000;
  border-radius: 8px;
  font-weight: bold;
  padding: 12px 24px;
  font-size: 1.2em;
}}

[data-testid="stSidebar"] {{
    background-color: #111;
}}
</style>
""", unsafe_allow_html=True)

# === AUTH ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# === SIDEBAR ===
with st.sidebar:
    st.header("⚙️ Controls")
    sheet_url = st.text_input("📄 Google Sheet URL")
    workout_type = st.selectbox("🏋️ Workout Type", ["Push", "Pull", "Legs"])
    goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"])
    workout_date = st.date_input("📅 Workout Date", value=date.today())

    generate = st.button("⚡ Generate Workout")
    edit_trigger = st.button("✏️ Edit Previous Workout")
    delete_trigger = st.button("❌ Delete Workout")

# === MAIN HEADER ===
st.title("RAGNARÖK LAB")

# === STOP IF NO SHEET ===
if not sheet_url:
    st.stop()

# === CONNECT SHEET ===
key = sheet_url.split("/d/")[1].split("/")[0]
sheet = gc.open_by_key(key).worksheet("WorkoutLog")

# === GENERATE ===
if generate:
    prompt = (
        f"You are an elite strength coach creating a {goal.lower()} {workout_type} workout. "
        "Use modern programming: supersets, periodization, PHUL/PHAT style. "
        "Return JSON: 5 exercises. Each: name, primary_muscle, target_muscle_detail, "
        "equipment, sets (int), reps (string), weight ('Auto'), superset_group_id (int)."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()

        workout = json.loads(text)
        st.session_state["workout_data"] = [
            {
                "Workout ID": f"{workout_date.strftime('%Y%m%d')}-{workout_type}",
                "Date": workout_date.strftime('%Y-%m-%d'),
                "Workout Type": workout_type,
                "Exercise": ex["name"],
                "Primary Muscle": ex["primary_muscle"],
                "Target Muscle Detail": ex["target_muscle_detail"],
                "Sets": ex["sets"],
                "Reps": ex["reps"],
                "Weight": ex["weight"],
                "Superset Group ID": ex["superset_group_id"],
                "Notes": ""
            }
            for ex in workout
        ]

    except Exception as e:
        st.error(f"❌ GPT failed: {e}")

if "workout_data" in st.session_state:
    st.subheader(f"🆕 {workout_type} Workout for {workout_date.strftime('%Y-%m-%d')}")
    for idx, ex in enumerate(st.session_state["workout_data"]):
        st.markdown(f"**{idx+1}. {ex['Exercise']}**")
        st.caption(f"{ex['Primary Muscle']} → {ex['Target Muscle Detail']}")
        st.text(f"{ex['Sets']} sets × {ex['Reps']}")
        note_key = f"note_{idx}"
        st.session_state["workout_data"][idx]["Notes"] = st.text_input(
            f"Notes for {ex['Exercise']}",
            value=ex["Notes"],
            key=note_key
        )

    if st.button("✅ Log Workout"):
        for row in st.session_state["workout_data"]:
            sheet.append_row([
                row["Workout ID"], row["Date"], row["Workout Type"],
                row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
                row["Sets"], row["Reps"], row["Weight"],
                row["Superset Group ID"], row["Notes"]
            ])
        st.success("✅ Workout logged!")
        del st.session_state["workout_data"]
        st.experimental_rerun()

# === EDIT ===
if edit_trigger:
    st.subheader("✏️ Edit Workout")
    edit_date = st.date_input("Select Date to Edit", value=date.today(), key="edit_date")
    if st.button("🔍 Load to Edit"):
        rows = sheet.get_all_records()
        edit_rows = [r for r in rows if r["Date"] == edit_date.strftime('%Y-%m-%d')]
        if edit_rows:
            edited = st.data_editor(edit_rows, num_rows="dynamic")
            if st.button("💾 Save Edits"):
                headers = sheet.row_values(1)
                sheet.clear()
                sheet.append_row(headers)
                for row in edited:
                    sheet.append_row(list(row.values()))
                st.success("✅ Edits saved.")
                st.experimental_rerun()
        else:
            st.info("No workouts found for that date.")

# === DELETE ===
if delete_trigger:
    st.subheader("🗑️ Delete Workout")
    delete_date = st.date_input("Select Date to Delete", value=date.today(), key="delete_date")
    if st.button("🔍 Load to Delete"):
        rows = sheet.get_all_records()
        delete_rows = [r for r in rows if r["Date"] == delete_date.strftime('%Y-%m-%d')]
        if delete_rows:
            st.dataframe(delete_rows)
            if st.button("❌ Confirm Delete"):
                keep_rows = [r for r in rows if r["Date"] != delete_date.strftime('%Y-%m-%d')]
                headers = sheet.row_values(1)
                sheet.clear()
                sheet.append_row(headers)
                for row in keep_rows:
                    sheet.append_row(list(row.values()))
                st.success("✅ Workout deleted.")
                st.experimental_rerun()
        else:
            st.info("No workouts found for that date.")
