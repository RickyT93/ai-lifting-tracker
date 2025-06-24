# ==============================
# === RAGNARÖK LAB — Final 🔥 ===
# ==============================

import streamlit as st
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from utils import generate_workout, log_workout, get_workouts_by_date, overwrite_sheet_with_rows

# === CONFIG ===
st.set_page_config(
    page_title="RAGNARÖK LAB",
    layout="wide"
)

# === STYLES ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&family=IM+Fell+English+SC&display=swap');

body, h1, h2, h3, h4, h5, h6, p, label, div, span {
  font-family: 'IM Fell English SC', serif;
  color: #e0f7ff !important;
}

.ragnarok-title {
  font-family: 'UnifrakturCook', cursive;
  font-size: 9vw;
  text-align: center;
  color: #e0f7ff;
  text-shadow:
    0 0 5px #ff0000,
    0 0 10px #ff3300,
    0 0 20px #ff6600,
    0 0 40px #ff9900;
  animation: flameglow 2.5s infinite alternate;
}

@keyframes flameglow {
  from { text-shadow:
    0 0 5px #ff0000,
    0 0 10px #ff3300,
    0 0 20px #ff6600,
    0 0 40px #ff9900; }
  to { text-shadow:
    0 0 10px #ff3300,
    0 0 20px #ff6600,
    0 0 40px #ff9900,
    0 0 60px #ffcc00; }
}

.stButton>button {
  background: #000;
  color: #ff3300;
  border: 2px solid #ff3300;
  border-radius: 8px;
  font-weight: bold;
  padding: 12px 24px;
  font-size: 1.2em;
}

input, select, textarea, input[type="date"] {
    color: white !important;
}

[data-testid="stSidebar"] {
    background-color: #111;
}

[data-testid="stSidebar"] * {
    font-size: 16px !important;
    color: #e0f7ff !important;
}
</style>
""", unsafe_allow_html=True)

# === AUTH ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)

# === SIDEBAR ===
with st.sidebar:
    st.header("⚙️ Controls")
    sheet_url = st.text_input("📄 Google Sheet URL")
    workout_type = st.selectbox("🏋️ Workout Type", ["Push", "Pull", "Legs"])
    goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"])
    workout_date = st.date_input("📅 Workout Date", value=date.today())
    gen_btn = st.button("⚡ Generate Workout")
    edit_btn = st.button("✏️ Edit Previous Workout")
    delete_btn = st.button("❌ Delete Workout")

# === HERO TITLE ===
st.markdown("<h1 class='ragnarok-title'>RAGNARÖK LAB</h1>", unsafe_allow_html=True)

# === STOP IF NO SHEET ===
if not sheet_url:
    st.stop()

# === SETUP SHEET ===
key = sheet_url.split("/d/")[1].split("/")[0]
sheet = gc.open_by_key(key).worksheet("WorkoutLog")

# === GENERATE ===
if gen_btn:
    result = generate_workout(key, workout_type, goal)
    workout_list = result.get("workout", [])
    warmup = result.get("warmup", "")
    finisher = result.get("finisher", "")

    if workout_list:
        st.session_state["workout_data"] = [
            {
                "Workout ID": f"{workout_date.strftime('%Y%m%d')}-{workout_type}",
                "Date": workout_date.strftime('%Y-%m-%d'),
                "Workout Type": workout_type,
                "Exercise": ex.get("name", ""),
                "Primary Muscle": ex.get("primary_muscle", ""),
                "Target Muscle Detail": ex.get("target_muscle_detail", ""),
                "Sets": ex.get("sets", ""),
                "Reps": ex.get("reps", ""),
                "Weight": ex.get("weight", ""),
                "Superset Group ID": ex.get("superset_group_id", 0),
                "Notes": ""
            }
            for ex in workout_list
        ]
        st.session_state["warmup"] = warmup
        st.session_state["finisher"] = finisher

# === SHOW GENERATED ===
if "workout_data" in st.session_state:
    st.subheader(f"🔥 Warm-up: {st.session_state.get('warmup', '')}")
    st.subheader(f"🆕 {workout_type} Workout")
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
    st.subheader(f"💥 Finisher: {st.session_state.get('finisher', '')}")

    if st.button("✅ Log Workout"):
        log_workout(sheet, st.session_state["workout_data"])
        st.success("✅ Workout logged!")
        del st.session_state["workout_data"]

# === EDIT ===
if edit_btn:
    st.subheader("✏️ Edit Workout")
    edit_date = st.date_input("Select Date to Edit", key="edit_date")
    if st.button("🔍 Load to Edit"):
        records = sheet.get_all_records()
        to_edit = [row for row in records if row["Date"] == edit_date.strftime('%Y-%m-%d')]
        if to_edit:
            edited = st.data_editor(to_edit, num_rows="dynamic")
            if st.button("💾 Save Edits"):
                others = [row for row in records if row["Date"] != edit_date.strftime('%Y-%m-%d')]
                overwrite_sheet_with_rows(sheet, others + edited)
                st.success("✅ Edits saved.")
        else:
            st.warning("No workout found for that date.")

# === DELETE ===
if delete_btn:
    st.subheader("❌ Delete Workout")
    del_date = st.date_input("Select Date to Delete", key="del_date")
    if st.button("🗑️ Confirm Delete"):
        records = sheet.get_all_records()
        keep = [row for row in records if row["Date"] != del_date.strftime('%Y-%m-%d')]
        overwrite_sheet_with_rows(sheet, keep)
        st.success(f"✅ Deleted workout for {del_date.strftime('%Y-%m-%d')}.")
