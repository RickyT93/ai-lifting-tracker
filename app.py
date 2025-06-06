import streamlit as st
from datetime import date
from utils import generate_workout, log_workout

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

# Inputs
sheet_url = st.text_input("📄 Paste your Google Sheet URL (shared with service account)", key="sheet_url")
selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Select your goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
custom_date = st.date_input("📅 Select the workout date", value=date.today())

# Store generated workout persistently
if "workout_data" not in st.session_state:
    st.session_state.workout_data = None

if st.button("Generate Workout") and sheet_url:
    try:
        workout = generate_workout(selected_day, goal)
        st.session_state.workout_data = []  # Reset log

        for ex in workout:
            st.session_state.workout_data.append({
                "Date": custom_date.strftime("%Y-%m-%d"),
                "Workout Type": selected_day,
                "Exercise": ex['name'],
                "Sets": ex['sets'],
                "Reps": ex['reps'],
                "Weight": ex['weight'],
                "Muscle": ex['muscle'],
                "Equipment": ex['equipment'],
                "Notes": ""  # placeholder
            })

    except Exception as e:
        st.error(f"❌ Error generating workout: {e}")

# Display and update notes
if st.session_state.workout_data:
    st.subheader(f"{selected_day} Workout for {custom_date.strftime('%Y-%m-%d')}")

    for i, ex in enumerate(st.session_state.workout_data):
        st.markdown(f"**{i + 1}. {ex['Exercise']}**")
        st.caption(f"Muscle: {ex['Muscle']} | Equipment: {ex['Equipment']}")
        st.text(f"Sets: {ex['Sets']} | Reps: {ex['Reps']} | Weight: {ex['Weight']} lbs")
        notes = st.text_input(f"Notes for {ex['Exercise']}", key=f"note_{i}", value=ex["Notes"])
        st.session_state.workout_data[i]["Notes"] = notes

    if st.button("Log Workout"):
        try:
            log_workout(sheet_url, st.session_state.workout_data)
            st.success("✅ Workout logged successfully!")
            st.session_state.workout_data = None  # Reset after logging
        except Exception as e:
            st.error(f"❌ Error logging workout: {e}")
