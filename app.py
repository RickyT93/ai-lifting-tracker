# ==============================
# === RAGNARÖK LAB — FINAL CLEAN ===
# ==============================

import streamlit as st
from datetime import date
import utils  # ✅ USE YOUR UTILS!

# === CONFIG ===
st.set_page_config(
    page_title="RAGNARÖK LAB",
    layout="wide"
)

# === STYLE ===
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

# === MAIN TITLE ===
st.title("RAGNARÖK LAB")

# === STOP IF NO SHEET ===
if not sheet_url:
    st.stop()

# === CONNECT SHEET ===
key = sheet_url.split("/d/")[1].split("/")[0]
sheet = utils.gc.open_by_key(key).worksheet("WorkoutLog")

# === GENERATE ===
if generate:
    workout = utils.generate_workout(workout_type, goal)
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
        utils.log_workout(sheet, st.session_state["workout_data"])
        st.success("✅ Workout logged!")
        del st.session_state["workout_data"]
        st.experimental_rerun()

# === EDIT ===
if edit_trigger:
    st.subheader("✏️ Edit Workout")
    edit_date = st.date_input("Select Date to Edit", value=date.today(), key="edit_date")
    if st.button("🔍 Load to Edit"):
        edit_rows = utils.get_workouts_by_date(sheet, edit_date.strftime('%Y-%m-%d'))
        if edit_rows:
            edited = st.data_editor(edit_rows, num_rows="dynamic")
            if st.button("💾 Save Edits"):
                utils.overwrite_sheet_with_rows(sheet, edited)
                st.success("✅ Edits saved.")
                st.experimental_rerun()
        else:
            st.info("No workouts for that date.")

# === DELETE ===
if delete_trigger:
    st.subheader("🗑️ Delete Workout")
    delete_date = st.date_input("Select Date to Delete", value=date.today(), key="delete_date")
    if st.button("🔍 Load to Delete"):
        delete_rows = utils.get_workouts_by_date(sheet, delete_date.strftime('%Y-%m-%d'))
        if delete_rows:
            st.dataframe(delete_rows)
            if st.button("❌ Confirm Delete"):
                all_rows = sheet.get_all_records()
                keep_rows = [r for r in all_rows if r["Date"] != delete_date.strftime('%Y-%m-%d')]
                utils.overwrite_sheet_with_rows(sheet, keep_rows)
                st.success("✅ Workout deleted.")
                st.experimental_rerun()
        else:
            st.info("No workouts for that date.")
