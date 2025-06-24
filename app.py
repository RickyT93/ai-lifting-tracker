# ==============================
# === RAGNARÖK LAB — FINAL ===
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

# === NORDIC RED FLAME CSS ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&family=IM+Fell+English+SC&display=swap');

body, h1, h2, h3, h4, h5, h6, p, label, div, span {
  font-family: 'IM Fell English SC', serif;
  color: #ffeaea !important;
}

.ragnarok-title {
  font-family: 'UnifrakturCook', cursive;
  font-size: 12vw;
  text-align: center;
  color: #ff0000;
  text-shadow:
    0 0 5px #ff0000,
    0 0 10px #ff3333,
    0 0 20px #ff6666,
    0 0 40px #ff9999;
  animation: flameglow 3s infinite alternate;
}

@keyframes flameglow {
  from { text-shadow:
    0 0 5px #ff0000,
    0 0 10px #ff3333,
    0 0 20px #ff6666,
    0 0 40px #ff9999; }
  to { text-shadow:
    0 0 10px #ff3333,
    0 0 20px #ff6666,
    0 0 40px #ff9999,
    0 0 60px #ffcccc; }
}

.stButton>button {
  background: #000;
  color: #ff0000;
  border: 2px solid #ff0000;
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

# === HERO TITLE ===
st.markdown("<h1 class='ragnarok-title'>RAGNARÖK LAB</h1>", unsafe_allow_html=True)

# === STOP IF NO SHEET ===
if not sheet_url:
    st.stop()

# === SHEET ===
key = sheet_url.split("/d/")[1].split("/")[0]
sheet = gc.open_by_key(key).worksheet("WorkoutLog")

# === GENERATE ===
if gen_btn:
    workout = generate_workout(key, workout_type, goal)
    if not workout:
        st.warning("⚠️ No workout returned.")
    else:
        st.session_state["workout_data"] = [
            {
                "Workout ID": f"{workout_date.strftime('%Y%m%d')}-{workout_type}",
                "Date": workout_date.strftime('%Y-%m-%d'),
                "Workout Type": workout_type,
                "Exercise": ex.get("name", "Unknown"),
                "Primary Muscle": ex.get("primary_muscle", ""),
                "Target Muscle Detail": ex.get("target_muscle_detail", ""),
                "Sets": ex.get("sets", ""),
                "Reps": ex.get("reps", ""),
                "Weight": ex.get("weight", ""),
                "Superset Group ID": ex.get("superset_group_id", 0),
                "Notes": ""
            }
            for ex in workout
        ]

# === SHOW GENERATED ===
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
        log_workout(sheet, st.session_state["workout_data"])
        st.success("✅ Workout logged!")
        del st.session_state["workout_data"]
        st.experimental_rerun()

# === EDIT ===
if edit_btn:
    st.subheader("✏️ Edit Workout")
    if "edit_date" not in st.session_state:
        st.session_state.edit_date = date.today()
    st.session_state.edit_date = st.date_input("Select Date to Edit", value=st.session_state.edit_date, key="edit_date")
    if st.button("🔍 Load to Edit"):
        to_edit = get_workouts_by_date(sheet, st.session_state.edit_date.strftime('%Y-%m-%d'))
        if to_edit:
            edited = st.data_editor(to_edit, num_rows="dynamic")
            if st.button("💾 Save Edits"):
                others = [row for row in sheet.get_all_records() if row["Date"] != st.session_state.edit_date.strftime('%Y-%m-%d')]
                overwrite_sheet_with_rows(sheet, others + edited)
                st.success("✅ Edits saved.")
                st.experimental_rerun()
        else:
            st.warning("No workout found for that date.")

# === DELETE ===
if delete_btn:
    st.subheader("❌ Delete Workout")
    if "del_date" not in st.session_state:
        st.session_state.del_date = date.today()
    st.session_state.del_date = st.date_input("Select Date to Delete", value=st.session_state.del_date, key="del_date")
    if st.button("🗑️ Confirm Delete"):
        keep = [row for row in sheet.get_all_records() if row["Date"] != st.session_state.del_date.strftime('%Y-%m-%d')]
        overwrite_sheet_with_rows(sheet, keep)
        st.success(f"✅ Deleted workout for {st.session_state.del_date.strftime('%Y-%m-%d')}.")
        st.experimental_rerun()
