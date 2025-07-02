import sqlite3
import streamlit as st
from typing import List, Dict, Any
from contextlib import contextmanager

# === DB CONFIG ===
DB_PATH = "scif.db"

@contextmanager
def get_db_connection():
    """Context-managed SQLite connection with Row access as dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def init_db() -> bool:
    """Create tables for workouts and PRs if they don't exist."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    workout_type TEXT NOT NULL,
                    exercise TEXT NOT NULL,
                    primary_muscle TEXT,
                    target_muscle_detail TEXT,
                    sets TEXT,
                    reps TEXT,
                    weight TEXT,
                    superset_group_id INTEGER,
                    notes TEXT,
                    rpe INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS personal_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exercise TEXT UNIQUE NOT NULL,
                    one_rep_max REAL,
                    date_achieved TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            return True
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return False

def log_to_db(workout_data: List[Dict[str, Any]]) -> bool:
    """Batch insert workout rows into the database."""
    if not workout_data:
        st.warning("No workout data to log.")
        return False
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            for row in workout_data:
                c.execute("""
                    INSERT INTO workouts (workout_id, date, workout_type, exercise, primary_muscle,
                        target_muscle_detail, sets, reps, weight, superset_group_id, notes, rpe)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("Workout ID"),
                    row.get("Date"),
                    row.get("Workout Type"),
                    row.get("Exercise"),
                    row.get("Primary Muscle"),
                    row.get("Target Muscle Detail"),
                    str(row.get("Sets", "")),
                    str(row.get("Reps", "")),
                    str(row.get("Weight", "")),
                    row.get("Superset Group ID", 0),
                    row.get("Notes", ""),
                    row.get("RPE", None)
                ))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Logging to DB failed: {e}")
        return False

def update_workout_row(row: Dict[str, Any]) -> bool:
    """Update a single row in the DB based on Workout ID + Exercise."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE workouts SET
                    sets = ?, reps = ?, weight = ?, notes = ?, rpe = ?
                WHERE workout_id = ? AND exercise = ?
            """, (
                str(row.get("Sets", "")),
                str(row.get("Reps", "")),
                str(row.get("Weight", "")),
                row.get("Notes", ""),
                row.get("RPE", None),
                row.get("Workout ID"),
                row.get("Exercise")
            ))
            conn.commit()
            return c.rowcount > 0
    except Exception as e:
        st.error(f"Update failed: {e}")
        return False

def get_workouts_by_date(target_date: str) -> List[Dict[str, Any]]:
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM workouts WHERE date = ? ORDER BY id", (target_date,))
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        st.error(f"Fetch failed: {e}")
        return []

def delete_workout_by_date(target_date: str) -> bool:
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM workouts WHERE date = ?", (target_date,))
            conn.commit()
            return c.rowcount > 0
    except Exception as e:
        st.error(f"Delete failed: {e}")
        return False

def backup_db(backup_path: str = None) -> bool:
    import shutil
    from datetime import datetime
    try:
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"scif_backup_{timestamp}.db"
        shutil.copy2(DB_PATH, backup_path)
        st.success(f"Database backed up to {backup_path}")
        return True
    except Exception as e:
        st.error(f"Backup failed: {e}")
        return False
