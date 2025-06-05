from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

def generate_workout(day_type):
    messages = [
        {"role": "system", "content": "You are a strength and hypertrophy training coach."},
        {"role": "user", "content": f"Generate a unique {day_type} day workout focused on both muscle growth and strength. Include coaching cues and list specific muscles targeted."}
    ]

    response = client.chat.completions.create(
        model="gpt-4",  # If this fails, switch to "gpt-3.5-turbo"
        messages=messages
    )

    return response.choices[0].message.content
