import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 📂 GSheet connect
scope = ["https://www.googleapis.com/auth/spreadsheets"]
gspread_creds = st.secrets["gspread_creds"]
credentials = Credentials.from_service_account_info(gspread_creds, scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="🏋️ PR Baseline", layout="centered")
st.title("📊 PR Baseline Manager")

sheet_url = st.text_input("📄 Paste your Google Sheet URL", key="pr_sheet_url")

if sheet_url:
    try:
        clean_url = sheet_url.split("/edit")[0]
        sheet = gc.open_by_url(clean_url).worksheet("PR_Baseline")

        st.subheader("🗂️ Current Baselines")
        data = sheet.get_all_records()
        st.dataframe(data)

        st.subheader("➕ Add New PR")
        exercise = st.text_input("Exercise Name")
        max_weight = st.number_input("Max Weight", min_value=0)
        reps = st.number_input("Reps", min_value=1)

        if st.button("Add PR"):
            sheet.append_row([exercise, max_weight, reps])
            st.success("✅ PR Added! Refresh to see it.")

    except Exception as e:
        st.error(f"❌ Error: {e}")
