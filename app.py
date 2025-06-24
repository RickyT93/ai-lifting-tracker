# ==============================
# === RAGNARÖK LAB ===
# ==============================
import streamlit as st
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import json

# === CONFIG ===
st.set_page_config(
    page_title="🩸 RAGNARÖK LAB 🩸",
    layout="wide"
)

# === CUSTOM STYLE ===
st.markdown(f"""
<style>
body {{
    background-image: url('https://raw.githubusercontent.com/RickyT93/ai-lifting-tracker/main/u2295657366_Atlas_a_mythical_titan_carrying_a_cracked_battle-_010899cb-2237-4ee4-a687-34c02e2f7c58_0.png');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: #FFFFFF;
}}

h1, h2, h3, h4, h5, h6 {{
    color: #FF0000; /* Blood red titles */
    font-family: Impact, sans-serif;
    text-shadow: 2px 2px black;
}}

.stButton>button {{
    background-color: #FF0000;
    color: white;
    border-radius: 6px;
    font-weight: bold;
}}

input, select, textarea {{
    color: black !important;
    background: rgba(255,255,255,0.85);
    border-radius: 4px;
}}
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
    sheet_url = st.text_input("📄 Google Sheet URL")
    workout_type = st.selectbox("🏋️ Workout Type", ["Push", "Pull", "Legs"])
    goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"])
    workout_date = st.date_input("📅 Workout Date", value=date.today())

    if st.button("⚡ Generate Workout"):
        st.session_state.generated = True

    st.divider()
    if st.button("✏️ Edit Previous Workouts"):
        st.session_state.edit_mode = True

    if st.button("🗑️ Delete Workout"):
        st.session_state.delete_mode = True

# === MAIN TITLE ===
st.title("🩸 RAGNARÖK LAB 🩸")

if sheet_url:
    key = sheet_url.split("/d/")[1].split("/")[0]
    sheet = gc.open_by_key(key).worksheet("WorkoutLog")

    all_records = sheet.get_all_records()

    # === SHOW PREVIOUS ===
    prev = [row for row in all_records if row["Workout Type"] == workout_type]
    prev_sorted = sorted(prev, key=lambda x: x["Date"], reverse=True)[:3]

    st.subheader(f"📑 Last {len(prev_sorted)} {workout_type} Workouts")
    if prev_sorted:
        st.dataframe(prev_sorted)
    else:
        st.info("No history yet — forge your legend now!")

    # === GENERATE ===
    if "generated" in st.session_state:
        prompt = (
            f"You are an elite strength coach forging a brutal {goal.lower()} {workout_type} workout "
            "using advanced periodization, RPE, supersets if useful, inspired by PHUL and PHAT. "
            "Return ONLY a JSON array of 5 exercises. Each: name, primary_muscle, target_muscle_detail, "
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
        st.subheader(f"🔥 {workout_type} Workout for {workout_date.strftime('%Y-%m-%d')}")
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
            st.success("✅ Workout forged and logged!")
            del st.session_state["workout_data"]

    # === EDIT ===
    if "edit_mode" in st.session_state:
        st.subheader("✏️ Edit a Workout by Date")
        dates = sorted(list({r["Date"] for r in all_records}), reverse=True)
        selected_date = st.selectbox("Select Date", dates)
        to_edit = [r for r in all_records if r["Date"] == selected_date]
        edited = st.data_editor(to_edit, num_rows="dynamic")
        if st.button("💾 Save Edits"):
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
            del st.session_state["edit_mode"]

    # === DELETE ===
    if "delete_mode" in st.session_state:
        st.subheader("🗑️ Delete a Workout by Date")
        dates = sorted(list({r["Date"] for r in all_records}), reverse=True)
        selected_date = st.selectbox("Select Date to Delete", dates)
        to_delete = [r for r in all_records if r["Date"] == selected_date]
        st.dataframe(to_delete)
        if st.button("🚨 Confirm Delete"):
            remaining = [r for r in all_records if r["Date"] != selected_date]
            sheet.clear()
            headers = ["Workout ID","Date","Workout Type","Exercise","Primary Muscle",
                       "Target Muscle Detail","Sets","Reps","Weight","Superset Group ID","Notes"]
            sheet.append_row(headers)
            for row in remaining:
                sheet.append_row([
                    row["Workout ID"], row["Date"], row["Workout Type"],
                    row["Exercise"], row["Primary Muscle"], row["Target Muscle Detail"],
                    row["Sets"], row["Reps"], row["Weight"],
                    row["Superset Group ID"], row["Notes"]
                ])
            st.success(f"✅ Deleted workout for {selected_date}")
            del st.session_state["delete_mode"]

else:
    st.info("⚠️ Provide your Google Sheet URL in the sidebar to unleash the LAB.")
