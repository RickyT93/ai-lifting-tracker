import streamlit as st
from utils import generate_workout, get_today, log_workout
from datetime import date

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")

st.title("🏋️ AI Lifting Tracker")

sheet_url = st.text_input("Paste your Google Sheet URL here")

selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])

if "workout_data" not in st.session_state:
    st.session_state.workout_data = []

if st.button("Generate Workout") and sheet_url:
    try:
        today = get_today()
        st.session_state.workout_data = generate_workout(selected_day, sheet_url)
        st.session_state.today = today

        st.subheader(f"{selected_day} Workout for {today}")
        for i, ex in enumerate(st.session_state.workout_data, start=1):
            st.markdown(f"**{i}. {ex['name']}**")
            st.caption(f"Muscle: {ex['muscle']} | Equipment: {ex['equipment']}")
            st.write(f"Sets: {ex['sets']} | Reps: {ex['reps']} | Weight: {ex['weight']} lbs")
    except Exception as e:
        st.error(f"❌ Error: {e}")

if st.session_state.get("workout_data"):
    notes = st.text_area("📝 Optional Notes for This Workout")

    if st.button("Log Workout"):
        try:
            log_workout(sheet_url, selected_day, st.session_state.today, st.session_state.workout_data, notes)
            st.success("✅ Workout logged successfully!")
        except Exception as e:
            st.error(f"❌ Failed to log workout: {e}")
