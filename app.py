# ==============================
# === RAGNARÖK LAB ===
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

body {{
  background: linear-gradient(rgba(0,0,0,0.88), rgba(0,0,0,0.88)),
              url('https://raw.githubusercontent.com/RickyT93/ai-lifting-tracker/main/A41FF6F0-219D-4EB8-AAFD-F4755DEF68BF.jpeg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  background-repeat: no-repeat;
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

input, select, textarea {{
    color: black !important;
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

    st.button("⚡ Generate Workout")
    st.button("✏️ Edit Previous Workouts")
    st.button("❌ Delete Workout")

# === MAIN HERO HEADER ===
st.title("RAGNARÖK LAB")

# === STOP IF NO SHEET URL ===
if not sheet_url:
    st.stop()

# === SHEET LOGIC ===
key = sheet_url.split("/d/")[1].split("/")[0]
sheet = gc.open_by_key(key).worksheet("WorkoutLog")

# === SHOW LAST WORKOUTS ===
all_records = sheet.get_all_records()
prev = [row for row in all_records if row["Workout Type"] == workout_type]
prev_sorted = sorted(prev, key=lambda x: x["Date"], reverse=True)[:3]

st.subheader(f"📑 Last {len(prev_sorted)} {workout_type} Workouts")
if prev_sorted:
    st.dataframe(prev_sorted)
else:
    st.info(f"No {workout_type} workouts yet.")

# === GENERATE ===
if st.session_state.get("generated") or st.sidebar.button("⚡ Generate Workout"):
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

# === SHOW GENERATED + LOG ===
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

# === PLACEHOLDER: Edit/Delete functionality ===
# (To be implemented fully later — currently only buttons in sidebar)
