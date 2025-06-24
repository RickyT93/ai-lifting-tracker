# ===================================
# === RAGNARÖK LAB — Nordic Flame PR EDITION ===
# ===================================

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

# === NORDIC FLAME CSS ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&family=IM+Fell+English+SC&display=swap');

body, h1, h2, h3, h4, h5, h6, p, label, div, span {
  font-family: 'IM Fell English SC', serif;
  color: #ffcccc !important;
  font-size: 2.5em !important;
}

.ragnarok-title {
  font-family: 'UnifrakturCook', cursive;
  font-size: 20vw;
  text-align: center;
  color: #ff3300;
  text-shadow:
    0 0 10px #ff0000,
    0 0 20px #ff3300,
    0 0 40px #ff6600,
    0 0 80px #ff9900;
}

.stButton>button {
  background: #000;
  color: #ff3300;
  border: 2px solid #ff3300;
  border-radius: 8px;
  font-weight: bold;
  padding: 18px 36px;
  font-size: 1.8em;
}

input, select, textarea, input[type="date"] {
    color: white !important;
    font-size: 1.5em !important;
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

    # === PR MANAGER ===
    st.header("📊 PR Baseline Manager")
    if sheet_url:
        try:
            key = sheet_url.split("/d/")[1].split("/")[0]
            pr_sheet = gc.open_by_key(key).worksheet("PR_Baseline")
            pr_data = pr_sheet.get_all_records()

            st.write("### Current PRs")
            st.dataframe(pr_data)

            st.write("### ➕ Add or Update PR")
            exercise = st.text_input("Exercise Name")
            one_rm = st.number_input("1RM", min_value=0)
            two_rm = st.number_input("2RM", min_value=0)
            three_rm = st.number_input("3RM", min_value=0)
            target = st.number_input("Target Goal", min_value=0)

            if st.button("💪 Save PR"):
                # Check if exercise exists
                found = False
                all_rows = pr_sheet.get_all_values()
                for idx, row in enumerate(all_rows):
                    if row[0].lower() == exercise.lower():
                        pr_sheet.update(f'A{idx+1}:E{idx+1}',
                                        [[exercise, one_rm, two_rm, three_rm, target]])
                        found = True
                        break
                if not found:
                    pr_sheet.append_row([exercise, one_rm, two_rm, three_rm, target])
                st.success("✅ PR Saved!")

        except Exception as e:
            st.error(f"❌ PR Baseline Error: {e}")

# === HERO TITLE ===
st.markdown("<h1 class='ragnarok-title'>RAGNARÖK LAB</h1>", unsafe_allow_html=True)

# === STOP IF NO SHEET ===
if not sheet_url:
    st.stop()

# === SETUP SHEET ===
key = sheet_url.split("/d/")[1].split("/")[0]
sheet = gc.open_by_key(key).worksheet("WorkoutLog")

# === GENERATE ===
if gen_btn:
    pr_sheet = gc.open_by_key(key).worksheet("PR_Baseline")
    pr_data = pr_sheet.get_all_records()
    last_logs = [row for row in sheet.get_all_records() if row["Workout Type"] == workout_type][-3:]

    prompt = f"""
You are an elite-level strength & functional fitness coach — the caliber of Arnold's secret coach & Hafthor Björnsson's strongman advisor — tasked with crafting a world-class, highly personalized workout plan for today.

Constraints & context:
- Goal: {goal}
- Workout Type: {workout_type}
- User’s PRs: {json.dumps(pr_data)}
- Last 3 {workout_type} logs: {json.dumps(last_logs)}

Rules:
1️⃣ The workout must be elite-level, functional, strongman-capable.
2️⃣ Use advanced programming: RPE, % of PRs, periodization, supersets, cluster sets.
3️⃣ Vary reps for strength + hypertrophy + functional work.
4️⃣ Each exercise must include:
   - name
   - primary_muscle
   - target_muscle_detail
   - equipment
   - sets (int)
   - reps (string)
   - weight (string, % of PR if relevant)
   - superset_group_id (0 means none)
5️⃣ Include at least 1 superset or finisher.
6️⃣ Ensure progression vs. last logs.
7️⃣ Be creative, no repeat.
8️⃣ Return ONLY JSON, no text, no code fences.

Mission:
Deliver an elite, challenging, safe, progressive workout — make me stronger than the gods.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
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

# === EDIT & DELETE remain as before ===
