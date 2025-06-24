import streamlit as st
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import json
from openai import OpenAI

# ==============================
# === STREAMLIT CONFIG + STYLE ===
# ==============================
st.set_page_config(
    page_title="🏋️ AI Lifting Tracker",
    layout="centered"
)

st.markdown("""
<style>
body {
    background-color: #000000;
    color: #FFFFFF;
}
h1, h2, h3, h4, h5, h6 {
    color: #00B4FF;
}
.stButton>button {
    background-color: #00B4FF;
    color: black;
    border-radius: 6px;
}
input, select, textarea {
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# === GOOGLE + OPENAI ===
# ==============================
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ==============================
# === MAIN APP ===
# ==============================
st.title("🏋️ AI Lifting Tracker")

sheet_url = st.text_input("📄 Google Sheet URL (must be shared with the service account)")

workout_type = st.selectbox("📆 Workout Type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
custom_date = st.date_input("📅 Workout Date", value=date.today())

# ==============================
# === SHOW PREVIOUS WORKOUTS ===
# ==============================
if sheet_url:
    try:
        key = sheet_url.split("/d/")[1].split("/")[0]
        sheet = gc.open_by_key(key).worksheet("WorkoutLog")

        all_records = sheet.get_all_records()
        prev = [row for row in all_records if row["Workout Type"] == workout_type]
        prev_sorted = sorted(prev, key=lambda x: x["Date"], reverse=True)[:3]

        if prev_sorted:
            st.subheader(f"📑 Last {len(prev_sorted)} {workout_type} Workouts")
            st.dataframe(prev_sorted)
        else:
            st.info(f"No {workout_type} workouts found yet. Generate one!")

    except Exception as e:
        st.warning(f"Could not load previous workouts: {e}")

# ==============================
# === GENERATE WORKOUT ===
# ==============================
if st.button("⚡ Generate Workout") and sheet_url:
    prompt = (
        f"You are an elite world-class strength coach designing a {goal.lower()} workout "
        f"for a '{workout_type}' day. Use modern programming methods (RPE, periodization, "
        "supersets where appropriate). Return ONLY a JSON array of 5 exercises. "
        "Each must have: name, primary_muscle, target_muscle_detail, equipment, sets (int), "
        "reps (string), weight (string 'Auto'), superset_group_id (int)."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()

        workout = json.loads(text)
        st.session_state["workout_data"] = [
            {
                "Workout ID": f"{custom_date.strftime('%Y%m%d')}-{workout_type}",
                "Date": custom_date.strftime('%Y-%m-%d'),
                "Workout Type": workout_type,
                "Exercise": ex["name"],
                "Primary Muscle": ex["primary_muscle"],
                "Target Muscle Detail": ex["target_muscle_detail"],
                "Sets": ex["sets"],
                "Reps": ex["reps"],
                "Weight": ex["weight"],
                "Superset Group ID": ex["superset_group_id"],
                "Notes": ""
            }
            for ex in workout
        ]

    except Exception as e:
        st.error(f"❌ GPT failed: {e}")

# ==============================
# === SHOW GENERATED ===
# ==============================
if "workout_data" in st.session_state:
    st.subheader(f"{workout_type} Workout for {custom_date.strftime('%Y-%m-%d')}")
    for idx, ex in enumerate(st.session_state["workout_data"]):
        st.markdown(f"**{idx+1}. {ex['Exercise']}**")
        st.caption(f"{ex['Primary Muscle']} → {ex['Target Muscle Detail']}")
        st.text(f"{ex['Sets']} sets x {ex['Reps']} reps")
        note_key = f"note_{idx}"
        st.session_state["workout_data"][idx]["Notes"] = st.text_input(
            f"Notes for {ex['Exercise']}",
            value=ex["Notes"],
            key=note_key
        )

    if st.button("✅ Log Workout"):
        try:
            for row in st.session_state["workout_data"]:
                sheet.append_row([
                    row["Workout ID"], row["Date"], row["Workout Type"],
                    row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
                    row["Sets"], row["Reps"], row["Weight"],
                    row["Superset Group ID"], row["Notes"]
                ])
            st.success("✅ Workout logged to Google Sheets!")
            del st.session_state["workout_data"]
        except Exception as e:
            st.error(f"⚠️ Failed to log workout: {e}")

# ==============================
# === EDIT PREVIOUS ===
# ==============================
if sheet_url and prev_sorted:
    st.subheader("✏️ Edit Last Workout")
    edited = st.data_editor(prev_sorted, num_rows="dynamic")
    if st.button("💾 Save Edits"):
        try:
            sheet.clear()
            headers = ["Workout ID","Date","Workout Type","Exercise","Primary Muscle",
                       "Target Muscle Detail","Sets","Reps","Weight","Superset Group ID","Notes"]
            sheet.append_row(headers)
            for row in edited:
                sheet.append_row([
                    row["Workout ID"], row["Date"], row["Workout Type"],
                    row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
                    row["Sets"], row["Reps"], row["Weight"],
                    row["Superset Group ID"], row["Notes"]
                ])
            st.success("✅ Edits saved!")
        except Exception as e:
            st.error(f"❌ Failed to save edits: {e}")
