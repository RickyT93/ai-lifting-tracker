# app.py

import streamlit as st
from datetime import date
from utils import generate_workout, log_workout

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

# === Inputs ===
sheet_url = st.text_input(
    "📄 Paste your Google Sheet URL (must be shared with the service account as Editor)"
)
selected_day = st.selectbox("📆 Workout Type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
custom_date = st.date_input("📅 Workout Date", value=date.today())

# === Generate Workout ===
if st.button("Generate Workout") and sheet_url:
    with st.spinner("🧠 Generating workout..."):
        workout = generate_workout(selected_day, goal)
        if workout:
            st.session_state["workout_data"] = []
            workout_id = f"{custom_date.strftime('%Y%m%d')}-{selected_day}"
            for ex in workout:
                st.session_state["workout_data"].append({
                    "Workout ID": workout_id,
                    "Date": custom_date.strftime("%Y-%m-%d"),
                    "Workout Type": selected_day,
                    "Exercise": ex["name"],
                    "Primary Muscle": ex["primary_muscle"],
                    "Target Muscle Detail": ex["target_detail"],
                    "Sets": ex["sets"],
                    "Reps": ex["reps"],
                    "Weight": ex["weight"],
                    "Superset Group ID": ex["superset_group"],
                    "Notes": ""
                })
        else:
            st.error("❌ GPT did not return valid workout data.")

# === Show & Log ===
if "workout_data" in st.session_state:
    st.subheader(f"{selected_day} Workout for {custom_date.strftime('%Y-%m-%d')}")
    for idx, ex in enumerate(st.session_state["workout_data"]):
        st.markdown(f"**{idx + 1}. {ex['Exercise']}**")
        st.caption(
            f"{ex['Primary Muscle']} → {ex['Target Muscle Detail']} | "
            f"{ex['Equipment'] if 'Equipment' in ex else ''} | "
            f"{ex['Sets']} sets x {ex['Reps']} reps"
        )
        note_key = f"note_{idx}"
        st.session_state["workout_data"][idx]["Notes"] = st.text_input(
            f"Notes for {ex['Exercise']}", value=ex["Notes"], key=note_key
        )

    if st.button("Log Workout"):
        try:
            log_workout(sheet_url, st.session_state["workout_data"])
            st.success("✅ Workout logged to Google Sheets!")
            del st.session_state["workout_data"]
        except Exception as e:
            st.error(f"⚠️ Logging failed: {e}")
