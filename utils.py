import openai
import json
from datetime import datetime

def get_today():
    return datetime.today().strftime("%A")

def generate_workout(day_type):
    prompt = f"Generate a unique {day_type} workout with 6 exercises. For each, return JSON: name, muscle, equipment."
    messages = [
        {"role": "system", "content": "You are a strength and hypertrophy coach."},
        {"role": "user", "content": prompt}
    ]
    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    try:
        return json.loads(response['choices'][0]['message']['content'])
    except Exception:
        return [{"name": f"{day_type} Exercise {i+1}", "muscle": "Various", "equipment": "Barbell"} for i in range(6)]
