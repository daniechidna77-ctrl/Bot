import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "bot.db")

db = sqlite3.connect(DB_PATH, check_same_thread=False)
c = db.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS files (
        code TEXT PRIMARY KEY,
        file_id TEXT,
        type TEXT DEFAULT 'document',
        caption TEXT,
        downloads INTEGER DEFAULT 0
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        username TEXT PRIMARY KEY
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS banner (
        type TEXT DEFAULT 'text',
        file_id TEXT,
        text TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        join_date TEXT
    )
""")

db.commit()

def save_file(code, file_id, file_type="document", caption=""):
    c.execute("INSERT OR REPLACE INTO files VALUES (?,?,?,?,?)", 
              (code, file_id, file_type, caption, 0))
    db.commit()

def find_file(code):
    c.execute("SELECT file_id, type, caption FROM files WHERE code=?", (code,))
    return c.fetchone()

def get_all_files():
    c.execute("SELECT code, type, caption, downloads FROM files")
    return c.fetchall()

def delete_file(code):
    c.execute("DELETE FROM files WHERE code=?", (code,))
    db.commit()

def increment_download(code):
    c.execute("UPDATE files SET downloads = downloads + 1 WHERE code=?", (code,))
    db.commit()

def add_channel(username):
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()

def get_channels():
    c.execute("SELECT username FROM channels")
    return [row[0] for row in c.fetchall()]

def delete_channel(username):
    c.execute("DELETE FROM channels WHERE username=?", (username,))
    db.commit()

def set_banner(banner_type, file_id=None, text=""):
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?,?,?)", (banner_type, file_id, text))
    db.commit()

def get_banner():
    c.execute("SELECT type, file_id, text FROM banner")
    row = c.fetchone()
    if row:
        return {"type": row[0], "file_id": row[1], "text": row[2] or ""}
    return {"type": "text", "file_id": None, "text": "📢 به ربات خوش اومدی!"}

def delete_banner():
    c.execute("DELETE FROM banner")
    db.commit()

def add_user(user_id, username="", full_name=""):
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?)", 
              (user_id, username, full_name, datetime.now().isoformat()))
    db.commit()

def get_all_users():
    c.execute("SELECT user_id, username, full_name FROM users")
    return c.fetchall()

def get_user_count():
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]
