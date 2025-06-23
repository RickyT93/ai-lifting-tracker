import streamlit as st
from datetime import date
from utils import generate_workout, log_workout

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

# === Inputs ===
sheet_url = st.text_input(
    "📄 Paste your Google Sheet URL (must be shared with the service account as Editor)"
)
selected_day = st.selectbox("📆 Workout Type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
custom_date = st.date_input("📅 Workout Date", value=date.today())

# === Generate Workout ===
if st.button("Generate Workout") and sheet_url:
    with st.spinner("Generating workout..."):
        workout = generate_workout(selected_day, goal)
        if workout:
            st.session_state["workout_data"] = [
                {
                    "Date": custom_date.strftime("%Y-%m-%d"),
                    "Workout Type": selected_day,
                    "Exercise": ex["name"],
                    "Sets": ex["sets"],
                    "Reps": ex["reps"],
                    "Weight": ex["weight"],
                    "Muscle": ex["muscle"],
                    "Equipment": ex["equipment"],
                    "Notes": ""
                }
                for ex in workout
            ]
        else:
            st.error("❌ GPT did not return valid data. Try again!")

# === Show & Log ===
if "workout_data" in st.session_state:
    st.subheader(f"{selected_day} Workout for {custom_date.strftime('%Y-%m-%d')}")
    for idx, ex in enumerate(st.session_state["workout_data"]):
        st.markdown(f"**{idx + 1}. {ex['Exercise']}**")
        st.caption(f"{ex['Muscle']} | {ex['Equipment']}")
        st.text(f"Sets: {ex['Sets']} | Reps: {ex['Reps']} | Weight: {ex['Weight']}")
        note_key = f"note_{idx}"
        st.session_state["workout_data"][idx]["Notes"] = st.text_input(
            f"Notes for {ex['Exercise']}", value=ex["Notes"], key=note_key
        )

    if st.button("Log Workout"):
        try:
            log_workout(sheet_url, st.session_state["workout_data"])
            st.success("✅ Workout logged to Google Sheets!")
            del st.session_state["workout_data"]
        except Exception as e:
            st.error(f"⚠️ Logging failed: {e}")
