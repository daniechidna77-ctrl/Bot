import sqlite3
import os
from datetime import datetime, timedelta
from config import DB_PATH, DEFAULT_CHANNELS

# ========================================
# ===== اتصال به دیتابیس =====
# ========================================
db = sqlite3.connect(DB_PATH, check_same_thread=False)
c = db.cursor()

# ========================================
# ===== ساخت جدول‌ها =====
# ========================================

# ۱. فایل‌ها (چپترها)
c.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        file_id TEXT,
        type TEXT DEFAULT 'document',
        caption TEXT,
        downloads INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )
""")

# ۲. کانال‌های اجباری
c.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        username TEXT PRIMARY KEY,
        added_at TEXT
    )
""")

# ۳. بنرها
c.execute("""
    CREATE TABLE IF NOT EXISTS banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT DEFAULT 'text',
        file_id TEXT,
        text TEXT,
        expire_date TEXT,
        created_at TEXT
    )
""")

# ۴. کاربران
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        join_date TEXT,
        last_activity TEXT
    )
""")

# ۵. اشتراک‌ها
c.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'active'
    )
""")

# ۶. تراکنش‌ها
c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )
""")

# ۷. کدهای تخفیف
c.execute("""
    CREATE TABLE IF NOT EXISTS coupons (
        code TEXT PRIMARY KEY,
        discount INTEGER,
        expires_at TEXT,
        usage_limit INTEGER,
        used_count INTEGER DEFAULT 0
    )
""")

# ۸. تبلیغات
c.execute("""
    CREATE TABLE IF NOT EXISTS advertisements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        file_id TEXT,
        text TEXT,
        link TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT
    )
""")

# ۹. تنظیمات
c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
""")

# ۱۰. فایل‌های موقت برای کلینر
c.execute("""
    CREATE TABLE IF NOT EXISTS temp_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        file_id TEXT,
        file_type TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )
""")

# ۱۱. سوالات کاربران
c.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question TEXT,
        answer TEXT,
        date TEXT,
        status TEXT DEFAULT 'pending'
    )
""")

db.commit()

# ========================================
# ===== اضافه کردن کانال‌های پیش‌فرض =====
# ========================================
for ch in DEFAULT_CHANNELS:
    c.execute("INSERT OR IGNORE INTO channels VALUES (?, ?)", (ch, datetime.now().isoformat()))
db.commit()

# ========================================
# ===== توابع فایل‌ها =====
# ========================================
def save_file(code, file_id, file_type="document", caption=""):
    now = datetime.now().isoformat()
    c.execute("""
        INSERT OR REPLACE INTO files (code, file_id, type, caption, updated_at, created_at)
        VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM files WHERE code=?), ?))
    """, (code, file_id, file_type, caption, now, code, now))
    db.commit()

def find_file(code):
    c.execute("SELECT file_id, type, caption FROM files WHERE code=?", (code,))
    return c.fetchone()

def get_all_files():
    c.execute("SELECT code, type, caption, downloads FROM files ORDER BY code")
    return c.fetchall()

def delete_file(code):
    c.execute("DELETE FROM files WHERE code=?", (code,))
    db.commit()

def increment_download(code):
    c.execute("UPDATE files SET downloads = downloads + 1 WHERE code=?", (code,))
    db.commit()

def search_files(query):
    c.execute("SELECT code, type, caption FROM files WHERE code LIKE ? OR caption LIKE ?", (f"%{query}%", f"%{query}%"))
    return c.fetchall()

# ========================================
# ===== توابع کانال‌ها =====
# ========================================
def add_channel(username):
    c.execute("INSERT OR IGNORE INTO channels VALUES (?, ?)", (username, datetime.now().isoformat()))
    db.commit()

def get_channels():
    c.execute("SELECT username FROM channels ORDER BY username")
    return [row[0] for row in c.fetchall()]

def delete_channel(username):
    c.execute("DELETE FROM channels WHERE username=?", (username,))
    db.commit()

# ========================================
# ===== توابع بنر =====
# ========================================
def set_banner(banner_type, file_id=None, text="", expire_date=None):
    c.execute("DELETE FROM banners")
    c.execute("""
        INSERT INTO banners (type, file_id, text, expire_date, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (banner_type, file_id, text, expire_date, datetime.now().isoformat()))
    db.commit()

def get_banner():
    c.execute("""
        SELECT type, file_id, text FROM banners
        WHERE expire_date IS NULL OR expire_date > ?
        ORDER BY id DESC LIMIT 1
    """, (datetime.now().isoformat(),))
    row = c.fetchone()
    if row:
        return {"type": row[0], "file_id": row[1], "text": row[2] or ""}
    return {"type": "text", "file_id": None, "text": "📢 به ربات خوش اومدی!"}

def delete_banner():
    c.execute("DELETE FROM banners")
    db.commit()

# ========================================
# ===== توابع کاربران =====
# ========================================
def add_user(user_id, username="", full_name=""):
    now = datetime.now().isoformat()
    c.execute("""
        INSERT OR REPLACE INTO users (user_id, username, full_name, join_date, last_activity)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, full_name, now, now))
    db.commit()

def get_all_users():
    c.execute("SELECT user_id, username, full_name FROM users")
    return c.fetchall()

def get_user_count():
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]

def get_user_by_id(user_id):
    c.execute("SELECT user_id, username, full_name FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()

# ========================================
# ===== توابع اشتراک =====
# ========================================
def add_subscription(user_id, plan, days):
    start = datetime.now().isoformat()
    end = (datetime.now() + timedelta(days=days)).isoformat()
    c.execute("""
        INSERT OR REPLACE INTO subscriptions (user_id, plan, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, plan, start, end, "active"))
    db.commit()

def get_user_subscription(user_id):
    c.execute("""
        SELECT plan, end_date FROM subscriptions
        WHERE user_id=? AND status='active' AND end_date > ?
        ORDER BY end_date DESC LIMIT 1
    """, (user_id, datetime.now().isoformat()))
    return c.fetchone()

def get_all_subscriptions():
    c.execute("SELECT user_id, plan, end_date FROM subscriptions WHERE status='active'")
    return c.fetchall()

# ========================================
# ===== توابع تبلیغات =====
# ========================================
def add_advertisement(ad_type, file_id=None, text="", link=""):
    c.execute("""
        INSERT INTO advertisements (type, file_id, text, link, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (ad_type, file_id, text, link, datetime.now().isoformat()))
    db.commit()

def get_all_ads():
    c.execute("SELECT id, type, text, link, active FROM advertisements WHERE active=1")
    return c.fetchall()

def delete_ad(ad_id):
    c.execute("UPDATE advertisements SET active=0 WHERE id=?", (ad_id,))
    db.commit()

# ========================================
# ===== توابع سوالات =====
# ========================================
def add_question(user_id, question):
    c.execute("""
        INSERT INTO questions (user_id, question, date, status)
        VALUES (?, ?, ?, ?)
    """, (user_id, question, datetime.now().isoformat(), "pending"))
    db.commit()

def get_pending_questions():
    c.execute("SELECT id, user_id, question, date FROM questions WHERE status='pending'")
    return c.fetchall()

def answer_question(q_id, answer):
    c.execute("""
        UPDATE questions SET answer=?, status='answered' WHERE id=?
    """, (answer, q_id))
    db.commit()

# ========================================
# ===== توابع تنظیمات =====
# ========================================
def get_setting(key):
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    return row[0] if row else None

def set_setting(key, value):
    c.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, value))
    db.commit()

# ========================================
# ===== بستن دیتابیس =====
# ========================================
def close_db():
    db.close()

print("✅ دیتابیس راه‌اندازی شد!")
