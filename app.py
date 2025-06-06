import streamlit as st
from utils import generate_workout, get_today
from datetime import date

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")

st.title("🏋️ AI Lifting Tracker")

st.markdown("**📄 Google Sheet URL (shared with service account)**")
st.text_input("Paste your Google Sheet URL here", key="sheet_url")

selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])

if st.button("Generate Workout"):
    try:
        today = get_today()
        workout = generate_workout(selected_day)

        st.subheader(f"{selected_day} Workout for {today}")
        for i, ex in enumerate(workout, start=1):
            name = ex.get("name", "Exercise")
            muscle = ex.get("muscle", "Unknown")
            equipment = ex.get("equipment", "Bodyweight")

            st.markdown(f"**{i}. {name}**")
            st.caption(f"Muscle: {muscle} | Equipment: {equipment}")
    except Exception as e:
        st.error(f"❌ Error: {e}")
