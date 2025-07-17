import sqlite3
import hashlib
import json

DATABASE = 'backend/db/users.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_verified INTEGER DEFAULT 0,
                verification_token TEXT,
                paid_plans TEXT DEFAULT '{}'
            )
        """)
        conn.commit()

def add_user(full_name, email, password, verification_token):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (full_name, email, password, verification_token)
                VALUES (?, ?, ?, ?)
            """, (full_name, email, hashed_password, verification_token))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # User with this email already exists

def verify_user(token):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET is_verified = 1, verification_token = NULL WHERE verification_token = ?
        """, (token,))
        conn.commit()
        return cursor.rowcount > 0

def authenticate_user(email, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users WHERE email = ? AND password = ? AND is_verified = 1
        """, (email, hashed_password))
        user = cursor.fetchone()
        if user:
            # Convert row to dictionary for easier access
            user_dict = {
                "id": user[0],
                "full_name": user[1],
                "email": user[2],
                "is_verified": bool(user[4]),
                "paid_plans": json.loads(user[5]) if user[5] else {}
            }
            return user_dict
        return None

def get_user_by_email(email):
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email,))
        user = cursor.fetchone()
        if user:
            return dict(user)
        return None

def update_user_paid_plans(user_id, new_plans):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET paid_plans = ? WHERE id = ?
        """, (json.dumps(new_plans), user_id))
        conn.commit()
        return cursor.rowcount > 0

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
