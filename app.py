# ==============================
# === RAGNARÖK LAB - RED FLAME ===
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

# === FLAME STYLE (scaled down) ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap');

body, h1, h2, h3, h4, h5, h6, p, label, div, span {
  font-family: 'UnifrakturCook', cursive;
  color: #FFEEEE !important;
  font-size: 1.2em !important;
}

.ragnarok-title {
  font-size: 10vw;
  text-align: center;
  color: #FF3300;
  text-shadow:
    0 0 10px #FF2200,
    0 0 20px #FF0000,
    0 0 40px #FF0000,
    0 0 80px #FF0000;
  animation: flame 3s infinite alternate;
}

@keyframes flame {
  0% { text-shadow:
    0 0 10px #FF2200,
    0 0 20px #FF0000,
    0 0 40px #FF0000,
    0 0 80px #FF0000; }
  100% { text-shadow:
    0 0 20px #FF4400,
    0 0 40px #FF1100,
    0 0 80px #FF0000,
    0 0 100px #FF0000; }
}

[data-testid="stSidebar"] * {
  font-size: 0.8em !important;  /* 🔥 Smaller sidebar text only */
}

.stButton>button {
  background: #000;
  color: #FF3300;
  border: 2px solid #FF3300;
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

# === HERO ===
st.markdown("<h1 class='ragnarok-title'>RAGNARÖK LAB</h1>", unsafe_allow_html=True)

# === STOP IF NO SHEET ===
if not sheet_url:
    st.stop()

key = sheet_url.split("/d/")[1].split("/")[0]
log_sheet = gc.open_by_key(key).worksheet("WorkoutLog")

# === GENERATE ===
if gen_btn:
    workout = generate_workout(key, workout_type, goal)
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

# === SHOW + LOG ===
if "workout_data" in st.session_state:
    st.subheader(f"🆕 {workout_type} Workout for {workout_date.strftime('%Y-%m-%d')}")
    for idx, ex in enumerate(st.session_state["workout_data"]):
        st.markdown(f"**{idx+1}. {ex['Exercise']}**")
        st.caption(f"{ex['Primary Muscle']} → {ex['Target Muscle Detail']}")
        st.text(f"{ex['Sets']} sets × {ex['Reps']}")
        st.session_state["workout_data"][idx]["Notes"] = st.text_input(
            f"Notes for {ex['Exercise']}",
            value=ex["Notes"],
            key=f"note_{idx}"
        )

    if st.button("✅ Log Workout"):
        log_workout(log_sheet, st.session_state["workout_data"])
        st.success("✅ Workout logged!")
        del st.session_state["workout_data"]
        st.experimental_rerun()

# === EDIT ===
if edit_btn:
    st.subheader("✏️ Edit Workout")
    edit_date = st.date_input("Select Date to Edit", key="edit_date")
    if st.button("🔍 Load to Edit"):
        rows = get_workouts_by_date(log_sheet, edit_date.strftime('%Y-%m-%d'))
        if rows:
            edited = st.data_editor(rows, num_rows="dynamic")
            if st.button("💾 Save Edits"):
                other_rows = [row for row in log_sheet.get_all_records() if row["Date"] != edit_date.strftime('%Y-%m-%d')]
                overwrite_sheet_with_rows(log_sheet, other_rows + edited)
                st.success("✅ Edits saved.")
        else:
            st.warning("No workouts found for that date.")

# === DELETE ===
if delete_btn:
    st.subheader("❌ Delete Workout")
    del_date = st.date_input("Select Date to Delete", key="del_date")
    if st.button("🗑️ Confirm Delete"):
        keep = [row for row in log_sheet.get_all_records() if row["Date"] != del_date.strftime('%Y-%m-%d')]
        overwrite_sheet_with_rows(log_sheet, keep)
        st.success(f"✅ Deleted workout for {del_date.strftime('%Y-%m-%d')}.")
