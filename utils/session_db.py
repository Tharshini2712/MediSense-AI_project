"""
utils/session_db.py  —  MediSense AI
Saves and retrieves patient consultations from SQLite.

Uses:
    sqlite3  →  Python built-in, zero installs needed
    json     →  Python built-in, zero installs needed

Functions used by app.py:
    init_db()                    →  create tables on startup
    save_consultation(...)       →  save one full patient session to DB
    get_consultations(user_id)   →  return all past consultations for a user
    get_consultation(id)         →  return one consultation by its ID
"""

import sqlite3
import json
import os
from datetime import datetime

# ── Path to your database file ────────────────────────────────────────────────
# Points to:  MediSense-AI/database/medisense_ai.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "database", "medisense_ai.db")


def _connect():
    """Open connection. row_factory lets us read columns by name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create the users and consultations tables if they don't exist.
    Call this once when Flask starts.
    Safe to call multiple times — uses IF NOT EXISTS.
    """
    conn = _connect()
    conn.executescript("""

        -- User accounts table (from Task 3 auth)
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER  PRIMARY KEY AUTOINCREMENT,
            name      TEXT     NOT NULL,
            email     TEXT     NOT NULL UNIQUE,
            password  TEXT     NOT NULL,
            created   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- One row per completed consultation
        CREATE TABLE IF NOT EXISTS consultations (
            id            INTEGER   PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER   REFERENCES users(id),
            patient_type  TEXT,
            gender        TEXT,
            age           TEXT,
            care_level    TEXT,
            intensity     TEXT,
            symptoms      TEXT,     -- stored as JSON array string
            diseases      TEXT,     -- stored as JSON array of [name, confidence] pairs
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

    """)
    conn.commit()
    conn.close()


def save_consultation(
    user_id:      int,
    patient_type: str,
    gender:       str,
    age:          str,
    care_level:   str,
    intensity:    str,
    symptoms:     list,
    diseases:     list,
) -> int:
    """
    Save one complete patient consultation to the database.

    Args:
        user_id      : session['user_id']   (0 or None if not using Task 3 auth yet)
        patient_type : session['patient_type']
        gender       : session['gender']
        age          : session['age']
        care_level   : session['care_level']
        intensity    : session['intensity']
        symptoms     : list of strings  e.g. ['fever', 'headache']
        diseases     : list of tuples   e.g. [('Malaria', 72), ('Dengue', 18)]

    Returns:
        int  →  the new consultation's database ID
    """
    conn = _connect()
    cursor = conn.execute("""
        INSERT INTO consultations
            (user_id, patient_type, gender, age,
             care_level, intensity, symptoms, diseases)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id       or 0,
        patient_type  or "Not Selected",
        gender        or "Not Selected",
        age           or "Not Selected",
        care_level    or "Not Selected",
        intensity     or "Not Selected",
        json.dumps(symptoms),   # ['fever', 'headache'] → stored as string
        json.dumps(diseases),   # [['Malaria',72], ...] → stored as string
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_consultations(user_id: int) -> list:
    """
    Get all past consultations for a user, newest first.

    Returns a list of dicts, each like:
    {
        'id': 3,
        'patient_type': 'Adult',
        'gender': 'Male',
        'age': '24 Years',
        'care_level': 'Hospital',
        'intensity': '7/10',
        'symptoms': ['fever', 'chills'],
        'diseases': [['Malaria', 57], ['Dengue', 22]],
        'created_at': '05 Jun 2026, 11:30'
    }
    """
    conn = _connect()
    rows = conn.execute("""
        SELECT id, patient_type, gender, age, care_level,
               intensity, symptoms, diseases, created_at
        FROM   consultations
        WHERE  user_id = ?
        ORDER  BY created_at DESC
    """, (user_id,)).fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id"          : row["id"],
            "patient_type": row["patient_type"],
            "gender"      : row["gender"],
            "age"         : row["age"],
            "care_level"  : row["care_level"],
            "intensity"   : row["intensity"],
            "symptoms"    : json.loads(row["symptoms"]  or "[]"),
            "diseases"    : json.loads(row["diseases"]  or "[]"),
            "created_at"  : _fmt(row["created_at"]),
        })
    return results


def get_consultation(consultation_id: int) -> dict | None:
    """
    Get one specific consultation by its ID.
    Returns a dict (same structure as above) or None if not found.
    """
    conn = _connect()
    row  = conn.execute("""
        SELECT c.*, u.name as user_name
        FROM   consultations c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE  c.id = ?
    """, (consultation_id,)).fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id"          : row["id"],
        "user_name"   : row["user_name"] or "Guest",
        "patient_type": row["patient_type"],
        "gender"      : row["gender"],
        "age"         : row["age"],
        "care_level"  : row["care_level"],
        "intensity"   : row["intensity"],
        "symptoms"    : json.loads(row["symptoms"]  or "[]"),
        "diseases"    : json.loads(row["diseases"]  or "[]"),
        "created_at"  : _fmt(row["created_at"]),
    }


def _fmt(ts: str) -> str:
    """Format  '2026-06-05 11:30:00'  →  '05 Jun 2026, 11:30'"""
    if not ts:
        return ""
    try:
        dt = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return ts