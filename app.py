import streamlit as st
from utils import generate_workout, get_today, log_workout
from datetime import date

# Page config
st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

# Input fields
sheet_url = st.text_input("📄 Paste your Google Sheet URL (shared with service account)", key="sheet_url")
selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"], key="day_type")
goal = st.radio("🎯 Select your goal", ["Hypertrophy", "Strength", "Endurance"], index=0, key="goal_type")
custom_date = st.date_input("📅 Select the workout date", value=date.today(), key="workout_date")

# Button to generate workout
if st.button("🚀 Generate Workout"):
    if not sheet_url:
        st.warning("Please enter your Google Sheet URL first.")
    else:
        try:
            workout = generate_workout(selected_day, goal, sheet_url)

            st.subheader(f"{selected_day} Workout for {custom_date.strftime('%Y-%m-%d')}")
            workout_data = []
            for i, ex in enumerate(workout, start=1):
                st.markdown(f"**{i}. {ex['name']}**")
                st.caption(f"Muscle: {ex['muscle']} | Equipment: {ex['equipment']}")
                st.text(f"Sets: {ex['sets']} | Reps: {ex['reps']} | Weight: {ex['weight']}")
                notes = st.text_input(f"📝 Notes for {ex['name']}", key=f"note_{i}")

                workout_data.append({
                    "Date": custom_date.strftime("%Y-%m-%d"),
                    "Workout Type": selected_day,
                    "Exercise": ex['name'],
                    "Sets": ex['sets'],
                    "Reps": ex['reps'],
                    "Weight": ex['weight'],
                    "Notes": notes
                })

            if st.button("💾 Log Workout"):
                log_workout(sheet_url, workout_data)
                st.success("✅ Workout logged successfully!")

        except Exception as e:
            st.error(f"❌ Error: {e}")
