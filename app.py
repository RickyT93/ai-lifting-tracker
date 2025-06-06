import streamlit as st
from datetime import date
from utils import generate_workout, log_workout

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

sheet_url = st.text_input("📄 Paste your Google Sheet URL", key="sheet_url")
selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Select your goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
custom_date = st.date_input("📅 Select workout date", value=date.today())

# Init session state
if "workout" not in st.session_state:
    st.session_state.workout = []
if "notes" not in st.session_state:
    st.session_state.notes = {}

# Generate button
if st.button("Generate Workout") and sheet_url:
    st.session_state.workout = generate_workout(selected_day, goal)

# Display workout
if st.session_state.workout:
    st.subheader(f"{selected_day} Workout for {custom_date}")
    for i, ex in enumerate(st.session_state.workout):
        st.markdown(f"**{i + 1}. {ex['name']}**")
        st.caption(f"Muscle: {ex['muscle']} | Equipment: {ex['equipment']}")
        st.text(f"Sets: {ex['sets']} | Reps: {ex['reps']} | Weight: {ex['weight']}")
        key = f"note_{i}"
        st.session_state.notes[key] = st.text_input(f"Notes for {ex['name']}", key=key)

    if st.button("Log Workout"):
        data = []
        for i, ex in enumerate(st.session_state.workout):
            data.append({
                "Date": custom_date.strftime("%Y-%m-%d"),
                "Workout Type": selected_day,
                "Exercise": ex["name"],
                "Sets": ex["sets"],
                "Reps": ex["reps"],
                "Weight": ex["weight"],
                "Notes": st.session_state.notes.get(f"note_{i}", "")
            })
        try:
            log_workout(sheet_url, data)
            st.success("✅ Workout logged!")
            st.session_state.workout = []
            st.session_state.notes = {}
        except Exception as e:
            st.error(f"❌ Logging failed: {e}")
