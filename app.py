import streamlit as st
from datetime import date
from utils import generate_workout, log_workout

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

# Step 1: User Inputs
sheet_url = st.text_input("📄 Paste your Google Sheet URL (shared with service account)", key="sheet_url")
selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Select your goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
custom_date = st.date_input("📅 Select the workout date", value=date.today())

# Step 2: Session State Setup
if "workout_generated" not in st.session_state:
    st.session_state.workout_generated = False

if "workout_data" not in st.session_state:
    st.session_state.workout_data = []

# Step 3: Generate Workout Button
if st.button("Generate Workout") and sheet_url:
    try:
        workout = generate_workout(selected_day, goal)
        st.session_state.workout_data = []
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
                "Notes": ""
            })
        st.session_state.workout_generated = True
    except Exception as e:
        st.error(f"❌ Error generating workout: {e}")

# Step 4: Show Workout + Notes Input
if st.session_state.workout_generated and st.session_state.workout_data:
    st.subheader(f"{selected_day} Workout for {custom_date.strftime('%Y-%m-%d')}")
    for i, ex in enumerate(st.session_state.workout_data):
        st.markdown(f"**{i + 1}. {ex['Exercise']}**")
        st.caption(f"Muscle: {ex['Muscle']} | Equipment: {ex['Equipment']}")
        st.text(f"Sets: {ex['Sets']} | Reps: {ex['Reps']} | Weight: {ex['Weight']}")
        notes_key = f"notes_{i}"
        if notes_key not in st.session_state:
            st.session_state[notes_key] = ""
        st.session_state[notes_key] = st.text_input(f"Notes for {ex['Exercise']}", value=st.session_state[notes_key], key=notes_key)
        st.session_state.workout_data[i]["Notes"] = st.session_state[notes_key]

    # Step 5: Log Button
    if st.button("Log Workout"):
        try:
            log_workout(sheet_url, st.session_state.workout_data)
            st.success("✅ Workout logged successfully!")
            # Clear everything
            st.session_state.workout_generated = False
            st.session_state.workout_data = []
            for i in range(len(st.session_state.workout_data)):
                del st.session_state[f"notes_{i}"]
        except Exception as e:
            st.error(f"❌ Failed to log workout: {e}")
