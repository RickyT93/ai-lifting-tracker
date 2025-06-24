# --------------------------
# FINAL APP.PY - AI Lifting Tracker
# --------------------------

import streamlit as st
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import json
from openai import OpenAI
import pandas as pd

# --------------------------
# === CONFIG ===
# --------------------------
st.set_page_config(
    page_title="🏋️ AI Lifting Tracker",
    layout="centered",
)

# Palantir-inspired theme (basic)
st.markdown("""
<style>
body {
    background-color: #000000;
    color: #FFFFFF;
}
.stButton>button {
    background-color: #00B4FF;
    color: black;
    border-radius: 4px;
}
input, select, textarea {
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

# --------------------------
# === SETUP ===
# --------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["gspread_creds"], scopes=scope)
gc = gspread.authorize(creds)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --------------------------
# === INPUTS ===
# --------------------------
st.title("🏋️ AI Lifting Tracker")

sheet_url = st.text_input(
    "📄 Paste your Google Sheet URL (must be shared with the service account as Editor)"
)
day_type = st.selectbox("📆 Workout Type", ["Push", "Pull", "Legs"])
goal = st.radio("🎯 Goal", ["Hypertrophy", "Strength", "Endurance"], index=0)
workout_date = st.date_input("📅 Workout Date", value=date.today())

# --------------------------
# === LOAD SHEET ===
# --------------------------
def get_sheet(sheet_url):
    key = sheet_url.split("/d/")[1].split("/")[0]
    return gc.open_by_key(key).worksheet("WorkoutLog")

# --------------------------
# === GET PREVIOUS WORKOUT ===
# --------------------------
def fetch_previous_workouts(sheet, day_type, n=3):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[df["Workout Type"] == day_type]
    latest_dates = df["Date"].drop_duplicates().sort_values(ascending=False).head(n)
    return df[df["Date"].isin(latest_dates)].sort_values(by=["Date", "Exercise"])

# --------------------------
# === GPT WORKOUT GENERATION ===
# --------------------------
def generate_workout(day_type, goal):
    prompt = (
        f"You are a world-class strength training coach. Generate a detailed {goal} workout "
        f"for a {day_type} day, following modern progressive overload principles, using "
        f"evidence-based rep and set schemes for intermediate lifters. Include exact target muscle detail, "
        f"primary muscle group, sets (int), reps (string), weight ('Auto'), and suggested superset pairings "
        f"(assign a Superset Group ID integer, 1 means not superset). Return only JSON array of 5 exercises."
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
        return json.loads(text)
    except Exception as e:
        st.error(f"❌ GPT Error: {e}")
        return []

# --------------------------
# === LOG TO SHEET ===
# --------------------------
def log_workout(sheet, data):
    for row in data:
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

# --------------------------
# === MAIN ACTION ===
# --------------------------
if sheet_url:
    sheet = get_sheet(sheet_url)

    # Display previous workouts
    prev_df = fetch_previous_workouts(sheet, day_type)
    if not prev_df.empty:
        st.subheader(f"📜 Last {day_type} Workouts")
        st.dataframe(prev_df)

        st.subheader("✏️ Edit Previous")
        editable = prev_df.copy()
        edited = st.data_editor(editable, num_rows="dynamic", use_container_width=True)
        if st.button("Save Edits"):
            # Overwrite: Clear old & re-upload
            all_records = sheet.get_all_records()
            all_df = pd.DataFrame(all_records)
            all_df = all_df[~(
                (all_df["Workout Type"] == day_type) &
                (all_df["Date"].isin(prev_df["Date"].unique()))
            )]
            final_df = pd.concat([all_df, edited]).sort_values(by=["Date"])
            sheet.clear()
            sheet.append_row(list(final_df.columns))
            for _, row in final_df.iterrows():
                sheet.append_row(row.tolist())
            st.success("✅ Edits Saved!")

    # Generate new workout
    if st.button("Generate New Workout"):
        st.session_state.workout = generate_workout(day_type, goal)
        if not st.session_state.workout:
            st.stop()

    if "workout" in st.session_state:
        st.subheader(f"{day_type} Workout for {workout_date}")
        for idx, ex in enumerate(st.session_state.workout):
            st.markdown(f"**{idx+1}. {ex['name']}**")
            st.caption(f"{ex['Primary Muscle']} → {ex['Target Muscle Detail']} | Sets: {ex['sets']} | Reps: {ex['reps']}")
            st.session_state.workout[idx]["Notes"] = st.text_input(
                f"Notes for {ex['name']}",
                key=f"note_{idx}"
            )

        if st.button("Log New Workout"):
            today_id = f"{workout_date.strftime('%Y%m%d')}-{day_type}"
            rows_to_log = []
            for ex in st.session_state.workout:
                rows_to_log.append({
                    "Workout ID": today_id,
                    "Date": workout_date.strftime("%Y-%m-%d"),
                    "Workout Type": day_type,
                    "Exercise": ex["name"],
                    "Primary Muscle": ex["Primary Muscle"],
                    "Target Muscle Detail": ex["Target Muscle Detail"],
                    "Sets": ex["sets"],
                    "Reps": ex["reps"],
                    "Weight": ex["weight"],
                    "Superset Group ID": ex.get("Superset Group ID", 1),
                    "Notes": ex["Notes"]
                })
            log_workout(sheet, rows_to_log)
            st.success("✅ Workout Logged!")
            del st.session_state.workout
