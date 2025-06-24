import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import json
from openai import OpenAI
import pandas as pd

# === Connect ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="🏋️ AI Lifting Tracker", layout="centered")
st.title("🏋️ AI Lifting Tracker")

# === Inputs ===
sheet_url = st.text_input(
    "📄 Paste your Google Sheet URL (must be shared with the service account as Editor)"
)
selected_day = st.selectbox("📆 Workout Type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
custom_date = st.date_input("📅 Workout Date", value=date.today())

# === Get Sheet ===
if sheet_url:
    key = sheet_url.split("/d/")[1].split("/")[0]
    sheet = gc.open_by_key(key).worksheet("WorkoutLog")

    # === Pull LAST workout(s) ===
    data = pd.DataFrame(sheet.get_all_records())
    prev = data[data["Workout Type"] == selected_day].sort_values(by="Date", ascending=False)
    last = prev.head(3)

    with st.expander(f"📜 Last {selected_day} Workouts"):
        if last.empty:
            st.info(f"No previous {selected_day} workouts found.")
        else:
            st.dataframe(last[["Date", "Exercise", "Sets", "Reps", "Weight", "Notes"]])

    # === Edit Last Workout ===
    if not last.empty:
        st.subheader(f"✏️ Edit Most Recent {selected_day} Workout")
        edited = []
        for i, row in last.iterrows():
            st.markdown(f"**{row['Exercise']}** ({row['Date']})")
            sets = st.number_input(f"Sets for {row['Exercise']}", value=int(row['Sets']), key=f"sets_{i}")
            reps = st.text_input(f"Reps for {row['Exercise']}", value=row['Reps'], key=f"reps_{i}")
            weight = st.text_input(f"Weight for {row['Exercise']}", value=row['Weight'], key=f"weight_{i}")
            notes = st.text_input(f"Notes for {row['Exercise']}", value=row['Notes'], key=f"notes_{i}")
            edited.append({
                "row_number": i + 2,  # +2 because Google Sheets rows are 1-indexed and header is row 1
                "Sets": sets,
                "Reps": reps,
                "Weight": weight,
                "Notes": notes
            })

        if st.button("💾 Save Edits to Google Sheets"):
            for update in edited:
                sheet.update_cell(update["row_number"], 6, update["Sets"])
                sheet.update_cell(update["row_number"], 7, update["Reps"])
                sheet.update_cell(update["row_number"], 8, update["Weight"])
                sheet.update_cell(update["row_number"], 10, update["Notes"])
            st.success("✅ Updates saved!")

# === Generate NEW Workout ===
if st.button("Generate Workout") and sheet_url:
    with st.spinner("Generating workout..."):
        prompt = (
            f"You are an elite strength coach writing a {goal} '{selected_day}' workout "
            "using proven programs (PHUL, 5x5, DUP). "
            f"Here are the last 3 {selected_day} logs: {last.to_dict(orient='records')}. "
            "Create 5 exercises with name, primary muscle, target detail, sets (int), reps (range), superset ID, weight 'Auto'. "
            "Return only a JSON array. No extra text."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()
        exercises = json.loads(text)

        st.session_state["new_workout"] = [
            {
                "Workout ID": f"{custom_date.strftime('%Y%m%d')}-{selected_day}",
                "Date": custom_date.strftime("%Y-%m-%d"),
                "Workout Type": selected_day,
                "Exercise": ex["name"],
                "Primary Muscle": ex["primary_muscle"],
                "Target Muscle Detail": ex["target_muscle_detail"],
                "Sets": ex["sets"],
                "Reps": ex["reps"],
                "Weight": ex["weight"],
                "Superset Group ID": ex["superset_group_id"],
                "Notes": ""
            }
            for ex in exercises
        ]

# === Show NEW Workout & Log ===
if "new_workout" in st.session_state:
    st.subheader(f"{selected_day} Workout for {custom_date.strftime('%Y-%m-%d')}")
    for idx, ex in enumerate(st.session_state["new_workout"]):
        st.markdown(f"**{idx+1}. {ex['Exercise']}**")
        st.caption(f"{ex['Primary Muscle']} → {ex['Target Muscle Detail']} | Sets: {ex['Sets']} x Reps: {ex['Reps']}")
        note_key = f"note_{idx}"
        st.session_state["new_workout"][idx]["Notes"] = st.text_input(
            f"Notes for {ex['Exercise']}", value=ex["Notes"], key=note_key
        )

    if st.button("Log New Workout"):
        for row in st.session_state["new_workout"]:
            sheet.append_row([
                row["Workout ID"],
                row["Date"],
                row["Workout Type"],
                row["Exercise"],
                row["Primary Muscle"],
                row["Target Muscle Detail"],
                row["Sets"],
                row["Reps"],
                row["Weight"],
                row["Superset Group ID"],
                row["Notes"]
            ])
        st.success("✅ New Workout Logged!")
        del st.session_state["new_workout"]
