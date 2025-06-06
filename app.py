import streamlit as st
from utils import generate_workout, get_today, log_workout
from datetime import date

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

# Input: Google Sheet URL
sheet_url = st.text_input("📄 Paste your Google Sheet URL (shared with service account)", key="sheet_url")

# Input: Workout Type, Goal, and Date
selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Select your goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
selected_date = st.date_input("📅 Select workout date", value=date.today())

# Workout generation
if st.button("Generate Workout") and sheet_url:
    workout_date = selected_date.strftime("%Y-%m-%d")
    try:
        workout = generate_workout(selected_day, goal, sheet_url)

        st.subheader(f"{selected_day} Workout for {workout_date}")
        workout_data = []
        for i, ex in enumerate(workout, start=1):
            st.markdown(f"**{i}. {ex['name']}**")
            st.caption(f"Muscle: {ex['muscle']} | Equipment: {ex['equipment']}")
            st.text(f"Sets: {ex['sets']} | Reps: {ex['reps']} | Weight: {ex['weight']}")
            notes = st.text_input(f"Notes for {ex['name']}", key=f"note_{i}")

            workout_data.append({
                "Date": workout_date,
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
