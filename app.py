import streamlit as st
from datetime import date
from utils import generate_workout, log_workout
from db import init_db, log_to_db, update_workout_row
from gspread_helper import get_gsheet_connection

st.set_page_config(page_title="S.C.I.F.", layout="wide")

# === LOAD CUSTOM CSS THEME ===
with open("theme.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === INTRO STATIC IMAGE ===
st.markdown('<div id="scif-intro"></div>', unsafe_allow_html=True)

# === LOOPING BACKGROUND VIDEO (optional) ===
video_url = "https://scif-assets.s3.amazonaws.com/background_loop.mp4"
st.markdown(f"""
    <video id="scif-loop-bg" autoplay muted loop>
        <source src="{video_url}" type="video/mp4">
    </video>
""", unsafe_allow_html=True)

# === SESSION CLEANUP ===
def clear_workout_session():
    for key in ["warmup", "finisher", "workout_data"]:
        st.session_state.pop(key, None)

# === SIDEBAR CONFIG ===
st.sidebar.title("S.C.I.F. Control Panel")
sheet_url = st.sidebar.text_input("Google Sheet URL")
goal = st.sidebar.selectbox("Goal", ["Hypertrophy", "Strength", "Endurance"])
day_type = st.sidebar.selectbox("Workout Type", ["Push", "Pull", "Legs"])
workout_date = st.sidebar.date_input("Workout Date", date.today())

# === SHEET KEY PARSE ===
if sheet_url and "/d/" in sheet_url:
    try:
        sheet_key = sheet_url.split("/d/")[1].split("/")[0]
    except IndexError:
        st.error("❌ Invalid Google Sheet URL.")
        st.stop()
else:
    st.warning("Enter a valid Google Sheet URL.")
    st.stop()

# === GENERATE WORKOUT ===
if st.sidebar.button("Generate Workout"):
    clear_workout_session()
    with st.spinner("Generating..."):
        gc = get_gsheet_connection()
        result = generate_workout(gc, sheet_key, day_type, goal)

        st.session_state["warmup"] = result.get("warmup", "")
        st.session_state["finisher"] = result.get("finisher", "")
        st.session_state["workout_data"] = [
            {
                "Workout ID": f"{workout_date}-{i+1}",
                "Date": str(workout_date),
                "Workout Type": day_type,
                "Exercise": ex["name"],
                "Primary Muscle": ex["primary_muscle"],
                "Target Muscle Detail": ex["target_muscle_detail"],
                "Equipment": ex["equipment"],
                "Sets": ex["sets"],
                "Reps": ex["reps"],
                "Weight": ex["weight"],
                "Superset Group ID": ex["superset_group_id"],
                "Notes": "",
                "RPE": 8,
            }
            for i, ex in enumerate(result.get("workout", []))
        ]

# === DISPLAY WORKOUT ===
if "workout_data" in st.session_state:
    st.subheader("🔥 Warm-Up")
    st.info(st.session_state["warmup"])

    for i, row in enumerate(st.session_state["workout_data"]):
        with st.expander(f"{row['Exercise']}"):
            sets = st.number_input("Sets", min_value=1, value=int(row["Sets"]), key=f"sets_{i}")
            reps = st.text_input("Reps", value=row["Reps"], key=f"reps_{i}")
            weight = st.text_input("Weight", value=row["Weight"], key=f"weight_{i}")
            notes = st.text_area("Notes", value=row["Notes"], key=f"notes_{i}")
            rpe = st.slider("RPE", 6, 10, row.get("RPE", 8), key=f"rpe_{i}")

            updated_row = row.copy()
            updated_row.update({
                "Sets": sets,
                "Reps": reps,
                "Weight": weight,
                "Notes": notes,
                "RPE": rpe
            })
            st.session_state["workout_data"][i] = updated_row

            if update_workout_row(updated_row):
                st.success("✔️ Saved", icon="✅")

    st.subheader("🏁 Finisher")
    st.info(st.session_state["finisher"])

    if st.button("✅ Log Workout"):
        try:
            gc = get_gsheet_connection()
            sheet = gc.open_by_key(sheet_key).worksheet("WorkoutLog")
            log_success = log_workout(sheet, st.session_state["workout_data"])
            db_success = log_to_db(st.session_state["workout_data"])

            if log_success and db_success:
                st.success("Workout logged to both Sheets and DB!")
            elif log_success:
                st.warning("Logged to Sheets, but DB log failed.")
            elif db_success:
                st.warning("Logged to DB, but Google Sheets log failed.")
            else:
                st.error("Failed to log workout to either destination.")
        except Exception as e:
            st.error(f"Logging error: {e}")

# === INIT DB ===
init_db()
