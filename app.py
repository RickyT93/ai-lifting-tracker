# app.py
import streamlit as st
from utils import generate_workout, get_today, log_workout_to_sheet
from gspread_helper import get_gsheet_connection

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

sheet_url = st.text_input("Paste your Google Sheet URL here", key="sheet_url")
st.session_state["sheet_url"] = sheet_url  # Save to session for reuse

goal = st.selectbox("📊 Select your goal", ["Hypertrophy", "Strength", "Endurance"])
selected_day = st.selectbox("🗖️ Choose workout day type", ["Push", "Pull", "Legs"])

if st.button("Generate Workout"):
    try:
        today = get_today()
        workout = generate_workout(selected_day, goal, sheet_url)

        st.subheader(f"{selected_day} Workout for {today}")
        for i, ex in enumerate(workout, start=1):
            st.markdown(f"**{i}. {ex['name']}**")
            st.caption(f"Muscle: {ex['muscle']} | Equipment: {ex['equipment']}")
            st.write(f"Sets: {ex['sets']} | Reps: {ex['reps']} | Suggested Weight: {ex['weight']} lbs")

        st.success("Workout generated!")
        st.session_state["current_workout"] = workout
    except Exception as e:
        st.error(f"❌ Error: {e}")

if "current_workout" in st.session_state:
    st.subheader("📃 Log Your Workout")
    notes = st.text_area("Any notes or feedback from today's workout?")

    if st.button("Log Workout"):
        try:
            log_workout_to_sheet(sheet_url, st.session_state["current_workout"], selected_day, notes)
            st.success("Workout logged successfully!")
            del st.session_state["current_workout"]
        except Exception as e:
            st.error(f"❌ Failed to log workout: {e}")
