import gspread
from datetime import datetime

def get_gsheet_connection(creds_dict):
    return gspread.service_account_from_dict(creds_dict)

def log_workout(gc, sheet_url, day_type, exercises, logs):
    sheet = gc.open_by_url(sheet_url).sheet1
    date = datetime.today().strftime("%Y-%m-%d")
    for ex, log in zip(exercises, logs):
        sheet.append_row([date, day_type, ex["name"], ex["muscle"], ex["equipment"], log])
