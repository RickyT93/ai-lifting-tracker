import os
import json
from datetime import date
from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

def get_today():
    return date.today().strftime("%Y-%m-%d")

def generate_workout(day_type):
    prompt = (
        f"Generate a structured JSON list with 5 unique {day_type.lower()} exercises. "
        f"Each object should include: name, muscle, equipment."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Respond only in JSON format. No extra text."},
                {"role": "user", "content": prompt}
            ]
        )

        raw = response.choices[0].message.content.strip()

        # Try parsing JSON first
        try:
            workout = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: Try to extract JSON manually if ChatGPT adds extra text
            json_start = raw.find('[')
            json_end = raw.rfind(']')
            workout = json.loads(raw[json_start:json_end + 1])

        # Ensure each item has the required keys
        cleaned = []
        for ex in workout:
            if all(k in ex for k in ("name", "muscle", "equipment")):
                cleaned.append(ex)
        return cleaned

    except Exception as e:
        st.error(f"❌ Failed to generate workout: {e}")
        return []
