import sqlite3

db = sqlite3.connect("bot.db", check_same_thread=False)
c = db.cursor()

# ساخت جدول‌ها
c.execute("CREATE TABLE IF NOT EXISTS files (code TEXT PRIMARY KEY, file_id TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)")
c.execute("CREATE TABLE IF NOT EXISTS banner (text TEXT)")
db.commit()

# ===== توابع فایل‌ها =====
def save_file(code, file_id):
    c.execute("INSERT OR REPLACE INTO files VALUES (?,?)", (code, file_id))
    db.commit()

def find_file(code):
    c.execute("SELECT file_id FROM files WHERE code=?", (code,))
    row = c.fetchone()
    return row[0] if row else None

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
def set_banner(text):
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?)", (text,))
    db.commit()

def get_banner():
    c.execute("SELECT text FROM banner")
    row = c.fetchone()
    return row[0] if row else "📢 به ربات خوش اومدی!"
