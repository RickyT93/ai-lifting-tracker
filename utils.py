import os
from datetime import date
from openai import OpenAI
import streamlit as st

# Initialize OpenAI client with API key from secrets
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

def get_today():
    return date.today().strftime("%Y-%m-%d")

def generate_workout(day_type):
    prompt = f"Create a {day_type.lower()} day gym workout with 5 exercises. " \
             f"For each exercise, return JSON with 'name', 'muscle', and 'equipment'."

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a fitness coach who formats responses as JSON arrays."},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract and safely parse workout response
    try:
        raw = response.choices[0].message.content.strip()
        workout = eval(raw) if raw.startswith("[") else []  # Basic fallback parser
        return workout
    except Exception as e:
        st.error(f"❌ Failed to parse workout: {e}")
        return []
