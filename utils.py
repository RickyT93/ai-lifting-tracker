import openai
import json
import streamlit as st

def generate_workout(day_type, goal):
    prompt = (
        f"Generate a {goal.lower()} workout for a '{day_type}' day. "
        "Return 5 exercises in strict JSON format like this:\n"
        "[\n"
        "  {\n"
        "    \"name\": \"Exercise Name\",\n"
        "    \"muscle\": \"Targeted Muscle\",\n"
        "    \"equipment\": \"Equipment Needed\",\n"
        "    \"sets\": 4,\n"
        "    \"reps\": \"8–12\",\n"
        "    \"weight\": \"Auto\"\n"
        "  }, ...\n"
        "]"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        content = response["choices"][0]["message"]["content"]

        # Extract JSON from the response
        start = content.find("[")
        end = content.rfind("]") + 1
        json_str = content[start:end]

        # Safely parse JSON
        workout = json.loads(json_str)
        if not isinstance(workout, list) or len(workout) < 3:
            st.warning("GPT returned too few exercises. Please try again.")
            return []
        return workout

    except Exception as e:
        st.error(f"❌ GPT error: {e}")
        return []
