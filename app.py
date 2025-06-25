# ==============================
# === S.C.I.F. — Phase I Build
# ==============================

import streamlit as st
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from utils import generate_workout, log_workout, get_workouts_by_date, overwrite_sheet_with_rows
from db import init_db, log_to_db

# === CONFIG ===
st.set_page_config(page_title="S.C.I.F.", layout="wide")
with open("theme.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === AUTH ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)

# === SIDEBAR ===
with st.sidebar:
    sheet_url = st.text_input("Google Sheet URL")
    workout_type = st.selectbox("Workout Type", ["Push", "Pull", "Legs"])
    goal = st.radio("Goal", ["Hypertrophy", "Strength", "Endurance"])
    workout_date = st.date_input("Workout Date", value=date.today())
    theme_toggle = st.checkbox("Light/Dark Theme")

    gen_btn = st.button("Generate Workout")
    edit_btn = st.button("Edit Previous Workout")
    delete_btn = st.button("Delete Workout")

# === STOP IF NO SHEET ===
if not sheet_url:
    st.stop()

key = sheet_url.split("/d/")[1].split("/")[0]
log_sheet = gc.open_by_key(key).worksheet("WorkoutLog")

# === GENERATE ===
if gen_btn:
    result = generate_workout(key, workout_type, goal)
    if result and result["workout"]:
        st.session_state["warmup"] = result["warmup"]
        st.session_state["finisher"] = result["finisher"]
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
            for ex in result["workout"]
        ]

# === SHOW ===
if "workout_data" in st.session_state:
    st.subheader(f"🔥 Warm-up: {st.session_state.get('warmup', '')}")
    st.subheader(f"📑 {workout_type} Workout for {workout_date.strftime('%Y-%m-%d')}")

    for idx, ex in enumerate(st.session_state["workout_data"]):
        st.markdown(f"### {idx+1}. {ex['Exercise']}")
        st.caption(f"{ex['Primary Muscle']} → {ex['Target Muscle Detail']}")
        st.text(f"{ex['Sets']} sets × {ex['Reps']} | Weight: {ex['Weight']}")

        st.write(f"**Set Details:**")
        sets = []
        for set_num in range(1, ex['Sets'] + 1):
            w = st.number_input(f"Weight (Set {set_num}) — {ex['Exercise']}", 0, 1000, step=5, key=f"w_{idx}_{set_num}")
            r = st.number_input(f"Reps (Set {set_num}) — {ex['Exercise']}", 1, 50, step=1, key=f"r_{idx}_{set_num}")
            sets.append(f"Set {set_num}: {w}lbs x {r} reps")

        rpe = st.slider(f"RPE for {ex['Exercise']}", 6, 10, 8, key=f"rpe_{idx}")
        technique = st.selectbox(f"Technique for {ex['Exercise']}",
                                 ["Perfect", "Minor Issues", "Needs Work"], key=f"tech_{idx}")
        fatigue = st.selectbox(f"Fatigue for {ex['Exercise']}",
                               ["Easy", "Moderate", "Hard", "Failure"], key=f"fat_{idx}")

        # Pack into Notes
        ex["Notes"] = "; ".join(sets) + f" | RPE: {rpe} | Technique: {technique} | Fatigue: {fatigue}"

    st.subheader(f"💥 Finisher: {st.session_state.get('finisher', '')}")

    if st.button("✅ Log Workout"):
        log_workout(log_sheet, st.session_state["workout_data"])
        log_to_db(st.session_state["workout_data"])
        st.success("✅ Workout logged to Sheets & DB!")

    if st.button("♻️ Clear & Reset"):
        for k in ["warmup", "finisher", "workout_data"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()

# === EDIT ===
if edit_btn:
    st.subheader("✏️ Edit Workout")
    edit_date = st.date_input("Select Date to Edit", key="edit_date")
    if st.button("🔍 Load"):
        to_edit = get_workouts_by_date(log_sheet, edit_date.strftime('%Y-%m-%d'))
        if to_edit:
            edited = st.data_editor(to_edit, num_rows="dynamic")
            if st.button("💾 Save"):
                others = [row for row in log_sheet.get_all_records() if row["Date"] != edit_date.strftime('%Y-%m-%d')]
                overwrite_sheet_with_rows(log_sheet, others + edited)
                st.success("✅ Edits saved.")
        else:
            st.warning("No workout found.")

# === DELETE ===
if delete_btn:
    st.subheader("🗑️ Delete Workout")
    del_date = st.date_input("Select Date", key="del_date")
    if st.button("❌ Confirm Delete"):
        keep = [row for row in log_sheet.get_all_records() if row["Date"] != del_date.strftime('%Y-%m-%d')]
        overwrite_sheet_with_rows(log_sheet, keep)
        st.success(f"✅ Deleted for {del_date.strftime('%Y-%m-%d')}")
