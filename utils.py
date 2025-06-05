# utils.py

from openai import OpenAI
import datetime
import streamlit as st

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

def get_today():
    return datetime.datetime.today().strftime('%Y-%m-%d')

def generate_workout(day_type):
    messages = [
        {"role": "system", "content": "You are a strength and hypertrophy training coach."},
        {"role": "user", "content": f"Generate a unique {day_type} day workout focused on both muscle growth and strength. Include coaching cues and specific muscles targeted."}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # You can change to gpt-4 if your key supports it
        messages=messages
    )

    return response.choices[0].message.content
