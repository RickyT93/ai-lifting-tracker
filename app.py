import streamlit as st
from datetime import date
from utils import generate_workout, get_today, get_user_profile, log_workout

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

# Step 1: Input Google Sheet URL
sheet_url = st.text_input("📄 Paste your Google Sheet URL (shared with service account)", key="sheet_url")

if sheet_url:
    # Step 2: Load user profile from Google Sheet
    try:
        profile = get_user_profile(sheet_url)
        st.success(f"Loaded profile for: {profile['User']} | Goal: {profile['Goal']}")
    except Exception as e:
        st.error(f"❌ Could not load user profile: {e}")
        st.stop()

    # Step 3: Select day type
    selected_day = st.selectbox("📆 Choose workout day type", ["Push", "Pull", "Legs"])

    # Step 4: Generate Workout
    if st.button("🎯 Generate Workout"):
        today = get_today()
        workout = generate_workout(selected_day, profile)

        if workout:
            st.subheader(f"{selected_day} Workout for {today}")
            notes = {}
            for i, ex in enumerate(workout, start=1):
                name = ex.get("name", f"Exercise {i}")
                muscle = ex.get("muscle", "Unknown")
                equipment = ex.get("equipment", "Bodyweight")
                sets = ex.get("sets", "?")
                reps = ex.get("reps", "?")
                weight = ex.get("weight", "?")

                st.markdown(f"**{i}. {name}**")
                st.caption(f"Muscle: {muscle} | Equipment: {equipment}")
                st.text(f"Sets: {sets} | Reps: {reps} | Suggested Weight: {weight} lbs")
                notes[name] = st.text_input(f"📝 Notes for {name}", key=f"notes_{i}")

            # Step 5: Log Workout
            if st.button("💾 Log Workout"):
                try:
                    log_workout(sheet_url, today, selected_day, workout, notes)
                    st.success("✅ Workout logged successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to log workout: {e}")
