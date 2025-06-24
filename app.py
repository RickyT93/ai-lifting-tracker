# ==============================
# === RAGNARÖK LAB v2 ===
# ==============================

import streamlit as st
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import json

# === CONFIG ===
st.set_page_config(
    page_title="RAGNARÖK LAB",
    layout="wide"
)

# === CUSTOM STYLE ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap');

.ragnarok-title {
  font-family: 'UnifrakturCook', cursive;
  font-size: 18vw;  /* Ultra Big */
  text-align: center;
  color: #FFF;
  position: relative;
  text-shadow: 4px 4px #000, 8px 8px #111, 12px 12px #222;
  overflow: hidden;
}

.ragnarok-title::before {
  content: '';
  position: absolute;
  top: 0; left: -75%;
  width: 50%;
  height: 100%;
  background: linear-gradient(120deg, transparent, rgba(255,255,255,0.6), transparent);
  transform: skewX(-20deg);
  animation: shimmer 3s infinite;
}

@keyframes shimmer {
  0% { left: -75%; }
  50% { left: 125%; }
  100% { left: 125%; }
}

body {
  background: black;
  color: white;
}

h2, h3, h4, h5, h6, p, span, label, div {
  color: white !important;
}

.stButton>button {
  background: #000;
  color: #FF0000;
  border: 2px solid #FF0000;
  border-radius: 8px;
  font-weight: bold;
  padding: 12px 24px;
  font-size: 1.2em;
}

input, select, textarea {
    color: black !important;
}

[data-testid="stSidebar"] {
    background-color: #111;
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
    sheet_url = st.text_input("📄 Google Sheet URL")
    workout_type = st.selectbox("🏋️ Workout Type", ["Push", "Pull", "Legs"])
    goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"])
    workout_date = st.date_input("📅 Workout Date", value=date.today())

    gen_btn = st.button("⚡ Generate Workout")
    edit_btn = st.button("✏️ Edit Previous Workout")
    delete_btn = st.button("❌ Delete Workout")

# === TITLE ===
st.markdown("<h1 class='ragnarok-title'>RAGNARÖK LAB</h1>", unsafe_allow_html=True)

# === STOP IF NO SHEET ===
if not sheet_url:
    st.stop()

# === SETUP SHEET ===
key = sheet_url.split("/d/")[1].split("/")[0]
sheet = gc.open_by_key(key).worksheet("WorkoutLog")

# === GENERATE ===
if gen_btn:
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

# === SHOW GENERATED ===
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
        st.experimental_rerun()

# === EDIT ===
if edit_btn:
    st.subheader("✏️ Edit Workout")
    edit_date = st.date_input("Select Date to Edit", key="edit_date")
    if st.button("🔍 Load to Edit"):
        records = sheet.get_all_records()
        to_edit = [row for row in records if row["Date"] == edit_date.strftime('%Y-%m-%d')]
        if to_edit:
            edited = st.data_editor(to_edit, num_rows="dynamic")
            if st.button("💾 Save Edits"):
                others = [row for row in records if row["Date"] != edit_date.strftime('%Y-%m-%d')]
                sheet.clear()
                headers = list(edited[0].keys())
                sheet.append_row(headers)
                for row in others + edited:
                    sheet.append_row(list(row.values()))
                st.success("✅ Edits saved.")
        else:
            st.warning("No workout found for that date.")

# === DELETE ===
if delete_btn:
    st.subheader("❌ Delete Workout")
    del_date = st.date_input("Select Date to Delete", key="del_date")
    if st.button("🗑️ Confirm Delete"):
        records = sheet.get_all_records()
        keep = [row for row in records if row["Date"] != del_date.strftime('%Y-%m-%d')]
        sheet.clear()
        if keep:
            sheet.append_row(list(keep[0].keys()))
            for row in keep:
                sheet.append_row(list(row.values()))
        st.success(f"✅ Deleted workout for {del_date.strftime('%Y-%m-%d')}.")
