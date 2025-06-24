import sqlite3

def init_db():
    conn = sqlite3.connect("scif.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id TEXT,
            date TEXT,
            type TEXT,
            exercise TEXT,
            sets TEXT,
            reps TEXT,
            weight TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_to_db(workout_data):
    conn = sqlite3.connect("scif.db")
    c = conn.cursor()
    for row in workout_data:
        c.execute("""
            INSERT INTO workouts (workout_id, date, type, exercise, sets, reps, weight, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["Workout ID"], row["Date"], row["Workout Type"],
            row["Exercise"], row["Sets"], row["Reps"], row["Weight"], row["Notes"]
        ))
    conn.commit()
    conn.close()
