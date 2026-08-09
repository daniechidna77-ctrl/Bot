import sqlite3
from datetime import datetime
from config import DEFAULT_CHANNELS

db = sqlite3.connect("bot.db", check_same_thread=False)
c = db.cursor()

# ===== ساخت جدول‌ها =====
c.execute("CREATE TABLE IF NOT EXISTS files (code TEXT PRIMARY KEY, file_id TEXT, type TEXT, downloads INTEGER DEFAULT 0)")
c.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)")
c.execute("CREATE TABLE IF NOT EXISTS banner (text TEXT, expire_date TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, join_date TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, message TEXT, date TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, question TEXT, answer TEXT, date TEXT, status TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS broadcast (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, date TEXT, status TEXT)")  # جدید
c.execute("CREATE TABLE IF NOT EXISTS user_settings (user_id INTEGER PRIMARY KEY, theme TEXT DEFAULT 'light')")
db.commit()

# ===== اضافه کردن کانال‌های پیش‌فرض =====
for ch in DEFAULT_CHANNELS:
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (ch,))
db.commit()

# ===== توابع فایل‌ها =====
def save_file(code, file_id, file_type="document"):
    c.execute("INSERT OR REPLACE INTO files (code, file_id, type) VALUES (?,?,?)", (code, file_id, file_type))
    db.commit()

def find_file(code):
    c.execute("SELECT file_id, type FROM files WHERE code=?", (code,))
    row = c.fetchone()
    return row if row else None

def delete_file(code):
    c.execute("DELETE FROM files WHERE code=?", (code,))
    db.commit()

def get_all_files():
    c.execute("SELECT code, type FROM files")
    return c.fetchall()

def increment_download(code):
    c.execute("UPDATE files SET downloads = downloads + 1 WHERE code=?", (code,))
    db.commit()

# ===== توابع کانال‌ها =====
def add_channel(username):
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()

def delete_channel(username):
    c.execute("DELETE FROM channels WHERE username=?", (username,))
    db.commit()

def get_channels():
    c.execute("SELECT username FROM channels")
    return [row[0] for row in c.fetchall()]

# ===== توابع بنر =====
def set_banner(text, expire_date=None):
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?,?)", (text, expire_date))
    db.commit()

def get_banner():
    c.execute("SELECT text, expire_date FROM banner")
    row = c.fetchone()
    if row:
        if row[1] and datetime.now().isoformat() > row[1]:
            return "📢 به ربات خوش اومدی!"
        return row[0]
    return "📢 به ربات خوش اومدی!"

def delete_banner():
    c.execute("DELETE FROM banner")
    db.commit()

# ===== توابع کاربران =====
def add_user(user_id):
    c.execute("INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?,?)", (user_id, datetime.now().isoformat()))
    db.commit()

def get_all_users():
    c.execute("SELECT user_id FROM users")
    return [row[0] for row in c.fetchall()]

def get_user_count():
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]

# ===== توابع نظرات =====
def add_feedback(user_id, message):
    c.execute("INSERT INTO feedback (user_id, message, date) VALUES (?,?,?)", (user_id, message, datetime.now().isoformat()))
    db.commit()

def get_all_feedback():
    c.execute("SELECT id, user_id, message, date FROM feedback ORDER BY date DESC")
    return c.fetchall()

# ===== توابع سوالات =====
def add_question(user_id, question):
    c.execute("INSERT INTO questions (user_id, question, date, status) VALUES (?,?,?,?)", (user_id, question, datetime.now().isoformat(), "pending"))
    db.commit()

def get_pending_questions():
    c.execute("SELECT id, user_id, question, date FROM questions WHERE status='pending'")
    return c.fetchall()

def answer_question(id, answer):
    c.execute("UPDATE questions SET answer=?, status='answered' WHERE id=?", (answer, id))
    db.commit()

# ===== توابع تنظیمات کاربر =====
def set_user_theme(user_id, theme):
    c.execute("INSERT OR REPLACE INTO user_settings (user_id, theme) VALUES (?,?)", (user_id, theme))
    db.commit()

def get_user_theme(user_id):
    c.execute("SELECT theme FROM user_settings WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else "light"

# ===== توابع زمان‌بندی (جدید) =====
def add_scheduled_broadcast(message, send_date, status="pending"):
    c.execute("INSERT INTO broadcast (message, date, status) VALUES (?,?,?)", (message, send_date, status))
    db.commit()

def get_pending_broadcasts():
    c.execute("SELECT id, message, date FROM broadcast WHERE status='pending'")
    return c.fetchall()

def update_broadcast_status(id, status):
    c.execute("UPDATE broadcast SET status=? WHERE id=?", (status, id))
    db.commit()
