import streamlit as st
from datetime import date
from utils import generate_workout, log_workout

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

sheet_url = st.text_input("📄 Paste your Google Sheet URL (shared with service account)", key="sheet_url")
selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Select your goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
custom_date = st.date_input("📅 Select the workout date", value=date.today())

# Generate Button
if st.button("Generate Workout") and sheet_url:
    with st.spinner("Generating workout..."):
        workout = generate_workout(selected_day, goal)
        st.session_state["workout_data"] = []
        for ex in workout:
            st.session_state["workout_data"].append({
                "Date": custom_date.strftime("%Y-%m-%d"),
                "Workout Type": selected_day,
                "Exercise": ex["name"],
                "Sets": ex["sets"],
                "Reps": ex["reps"],
                "Weight": ex["weight"],
                "Muscle": ex["muscle"],
                "Equipment": ex["equipment"],
                "Notes": ""
            })

# Display Workout
if "workout_data" in st.session_state:
    st.subheader(f"{selected_day} Workout for {custom_date.strftime('%Y-%m-%d')}")
    for i, ex in enumerate(st.session_state["workout_data"]):
        st.markdown(f"**{i + 1}. {ex['Exercise']}**")
        st.caption(f"Muscle: {ex['Muscle']} | Equipment: {ex['Equipment']}")
        st.text(f"Sets: {ex['Sets']} | Reps: {ex['Reps']} | Weight: {ex['Weight']}")
        note_key = f"note_{i}"
        st.session_state["workout_data"][i]["Notes"] = st.text_input(f"Notes for {ex['Exercise']}", key=note_key)

    if st.button("Log Workout"):
        log_workout(sheet_url, st.session_state["workout_data"])
        st.success("✅ Workout logged!")
        del st.session_state["workout_data"]
