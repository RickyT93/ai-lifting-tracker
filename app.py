import streamlit as st
import openai
from gspread_helper import get_gsheet_connection, log_workout
from utils import generate_workout, get_today

st.set_page_config(page_title="AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

openai.api_key = st.secrets["openai"]["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"]
gc = get_gsheet_connection(st.secrets["gspread"]["creds_path"])

sheet_url = st.text_input("📄 Google Sheet URL (shared with service account)", "")
selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])

if st.button("Generate Workout"):
    with st.spinner("Generating..."):
        workout = generate_workout(selected_day)
        st.session_state["workout"] = workout

if "workout" in st.session_state:
    st.subheader(f"{selected_day} Workout for {get_today()}")
    for i, ex in enumerate(st.session_state["workout"], 1):
        st.markdown(f"**{i}. {ex['name']}**")
        st.caption(f"Muscle: {ex['muscle']} | Equipment: {ex['equipment']}")
        st.text_area("Log your sets/reps/weight:", key=f"log_{i}")

    if st.button("Log Workout to Google Sheet"):
        if sheet_url:
            logs = [st.session_state[f"log_{i}"] for i in range(1, len(st.session_state["workout"]) + 1)]
            log_workout(gc, sheet_url, selected_day, st.session_state["workout"], logs)
            st.success("✅ Workout logged!")
        else:
            st.error("Please provide a valid Google Sheet URL.")
