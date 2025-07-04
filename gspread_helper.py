import gspread
import streamlit as st

def get_gsheet_connection():
    creds_dict = {
        "type": st.secrets["gspread_creds"]["type"],
        "project_id": st.secrets["gspread_creds"]["project_id"],
        "private_key_id": st.secrets["gspread_creds"]["private_key_id"],
        "private_key": st.secrets["gspread_creds"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["gspread_creds"]["client_email"],
        "client_id": st.secrets["gspread_creds"]["client_id"],
        "auth_uri": st.secrets["gspread_creds"]["auth_uri"],
        "token_uri": st.secrets["gspread_creds"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gspread_creds"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gspread_creds"]["client_x509_cert_url"]
    }
    return gspread.service_account_from_dict(creds_dict)
