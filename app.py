# ==============================
# === AI Lifting Tracker (Refined)
# ==============================
import streamlit as st
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import json

# === CONFIG ===
st.set_page_config(
    page_title="🏋️ AI Lifting Tracker",
    layout="wide"
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

# === AUTH ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# === SIDEBAR ===
with st.sidebar:
    st.header("⚙️ Controls")
    sheet_url = st.text_input("📄 Google Sheet URL (must be shared)")
    workout_type = st.selectbox("🏋️ Workout Type", ["Push", "Pull", "Legs"])
    goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"])
    workout_date = st.date_input("📅 Workout Date", value=date.today())

    if st.button("⚡ Generate Workout"):
        st.session_state.generated = True

# === MAIN ===
st.title("🏋️ AI Lifting Tracker")

if sheet_url:
    # Extract sheet
    key = sheet_url.split("/d/")[1].split("/")[0]
    sheet = gc.open_by_key(key).worksheet("WorkoutLog")

    # === SHOW PREVIOUS ===
    all_records = sheet.get_all_records()
    prev = [row for row in all_records if row["Workout Type"] == workout_type]
    prev_sorted = sorted(prev, key=lambda x: x["Date"], reverse=True)[:3]

    st.subheader(f"📑 Last {len(prev_sorted)} {workout_type} Workouts")
    if prev_sorted:
        st.dataframe(prev_sorted)
    else:
        st.info("No history yet — generate your first workout!")

    # === GENERATE ===
    if "generated" in st.session_state:
        prompt = (
            f"You are an elite strength coach creating a {goal.lower()} {workout_type} workout. "
            "Use modern programming: supersets, periodization, PHUL/PHAT style. "
            "Return JSON: 5 exercises. Each: name, primary_muscle, target_muscle_detail, "
            "equipment, sets (int), reps (string), weight ('Auto'), superset_group_id (int)."
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1]).strip()

            workout = json.loads(text)

            st.session_state["workout_data"] = [
                {
                    "Workout ID": f"{workout_date.strftime('%Y%m%d')}-{workout_type}",
                    "Date": workout_date.strftime('%Y-%m-%d'),
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

    # === SHOW GENERATED + LOG ===
    if "workout_data" in st.session_state:
        st.subheader(f"🆕 {workout_type} Workout for {workout_date.strftime('%Y-%m-%d')}")
        for idx, ex in enumerate(st.session_state["workout_data"]):
            st.markdown(f"**{idx+1}. {ex['Exercise']}**")
            st.caption(f"{ex['Primary Muscle']} → {ex['Target Muscle Detail']}")
            st.text(f"{ex['Sets']} sets × {ex['Reps']}")
            note_key = f"note_{idx}"
            st.session_state["workout_data"][idx]["Notes"] = st.text_input(
                f"Notes for {ex['Exercise']}",
                value=ex["Notes"],
                key=note_key
            )

        if st.button("✅ Log Workout"):
            for row in st.session_state["workout_data"]:
                sheet.append_row([
                    row["Workout ID"], row["Date"], row["Workout Type"],
                    row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
                    row["Sets"], row["Reps"], row["Weight"],
                    row["Superset Group ID"], row["Notes"]
                ])
            st.success("✅ Workout logged!")
            del st.session_state["workout_data"]

    # === EDIT PREVIOUS ===
    if prev_sorted:
        st.subheader("✏️ Edit Previous Workout")
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

else:
    st.info("Paste your Google Sheet URL in the sidebar to begin.")
