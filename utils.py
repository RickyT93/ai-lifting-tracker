def generate_workout(day_type, goal):
    prompt = (
        f"Create a {goal.lower()} workout for a '{day_type}' day. "
        "Return ONLY a JSON array of 5 exercises. No explanation. Each exercise must include:\n"
        "- name (string)\n"
        "- muscle (string)\n"
        "- equipment (string)\n"
        "- sets (integer)\n"
        "- reps (string)\n"
        "- weight (string, always 'Auto')\n\n"
        "Example:\n"
        '[{"name": "Squat", "muscle": "Quads", "equipment": "Barbell", "sets": 4, "reps": "8-10", "weight": "Auto"}]'
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = response.choices[0].message.content.strip()

        st.text_area("🧠 GPT Raw Output", text, height=200)

        # Remove code block markers if present
        if text.startswith("```json") and text.endswith("```"):
            text = text[len("```json"): -3].strip()
        elif text.startswith("```") and text.endswith("```"):
            text = text[3:-3].strip()

        workout = json.loads(text)
        return workout if isinstance(workout, list) else []
    except json.JSONDecodeError as je:
        st.error(f"⚠️ GPT returned invalid JSON: {je}")
        st.warning("Try regenerating. GPT may have returned extra explanation.")
        return []
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {e}")
        return []
