"""
utils/auth_db.py  —  MediSense AI
Handles all user database operations: create table, register, login check.

Uses:
    sqlite3     → Python built-in, no install needed
    werkzeug    → comes with Flask, no install needed

Used by app.py:
    from utils.auth_db import init_db, register_user, get_user_by_email
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# ── Path to your existing database file ───────────────────────────────────────
# This points to:  MediSense-AI/database/medisense_ai.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "database", "medisense_ai.db")


def _connect():
    """Open a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    Create the users table if it doesn't exist yet.
    Call this once when Flask starts (inside app.py with app context).
    """
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER  PRIMARY KEY AUTOINCREMENT,
            name     TEXT     NOT NULL,
            email    TEXT     NOT NULL UNIQUE,
            password TEXT     NOT NULL,
            created  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def register_user(name: str, email: str, password: str) -> dict:
    """
    Register a new user. Hashes the password before saving.

    Returns:
        {"success": True}                         on success
        {"success": False, "error": "..."}        if email already exists
    """
    pw_hash = generate_password_hash(password, method="pbkdf2:sha256")
    try:
        conn = _connect()
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name.strip(), email.strip().lower(), pw_hash)
        )
        conn.commit()
        conn.close()
        return {"success": True}

    except sqlite3.IntegrityError:
        # UNIQUE constraint failed → email already registered
        return {"success": False, "error": "This email is already registered. Please log in."}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_user_by_email(email: str) -> dict | None:
    """
    Fetch a user row by email.

    Returns:
        {"id": 1, "name": "...", "email": "...", "password": "..."}
        or None if not found.
    """
    conn = _connect()
    row  = conn.execute(
        "SELECT id, name, email, password FROM users WHERE email = ?",
        (email.strip().lower(),)
    ).fetchone()
    conn.close()

    if row:
        return {"id": row[0], "name": row[1], "email": row[2], "password": row[3]}
    return None


def check_login(email: str, password: str) -> dict | None:
    """
    Verify email + password combination.

    Returns:
        {"id": ..., "name": ..., "email": ...}   if credentials are correct
        None                                       if email not found or wrong password
    """
    user = get_user_by_email(email)
    if user is None:
        return None
    if check_password_hash(user["password"], password):
        return {"id": user["id"], "name": user["name"], "email": user["email"]}
    return None