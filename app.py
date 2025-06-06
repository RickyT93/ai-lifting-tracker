import streamlit as st
from utils import generate_workout, get_today, log_workout
from datetime import date

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

# Input: Google Sheet URL
sheet_url = st.text_input("📄 Paste your Google Sheet URL (shared with service account)", key="sheet_url")

# Input: Workout Type and Goal
selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Select your goal", ["Hypertrophy", "Strength", "Endurance"], index=0)

# Workout generation
if st.button("Generate Workout") and sheet_url:
    today = get_today()
    try:
        workout = generate_workout(selected_day, goal, sheet_url)

        st.subheader(f"{selected_day} Workout for {today}")
        workout_data = []
        for i, ex in enumerate(workout, start=1):
            st.markdown(f"**{i}. {ex['name']}**")
            st.caption(f"Muscle: {ex['muscle']} | Equipment: {ex['equipment']}")
            st.text(f"Sets: {ex['sets']} | Reps: {ex['reps']} | Weight: {ex['weight']} lbs")
            notes = st.text_input(f"Notes for {ex['name']}", key=f"note_{i}")

            workout_data.append({
                "Date": today,
                "Workout Type": selected_day,
                "Exercise": ex['name'],
                "Sets": ex['sets'],
                "Reps": ex['reps'],
                "Weight": ex['weight'],
                "Notes": notes
            })

        if st.button("Log Workout"):
            log_workout(sheet_url, workout_data)
            st.success("✅ Workout logged successfully!")

    except Exception as e:
        st.error(f"❌ Error: {e}")
