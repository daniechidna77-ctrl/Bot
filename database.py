import sqlite3
import os
import shutil
from datetime import datetime, timedelta
from config import DEFAULT_CHANNELS

# ========================================
# ===== بکاپ خودکار =====
# ========================================

def backup_db():
    """گرفتن بکاپ از دیتابیس"""
    if os.path.exists("bot.db"):
        shutil.copy("bot.db", "bot_backup.db")
        print("📁 بکاپ گرفته شد!")
        return True
    return False

def restore_db():
    """بازیابی از بکاپ"""
    if os.path.exists("bot_backup.db"):
        shutil.copy("bot_backup.db", "bot.db")
        print("✅ دیتابیس از بکاپ بازیابی شد!")
        return True
    return False

# ========================================
# ===== بررسی وجود دیتابیس =====
# ========================================

if not os.path.exists("bot.db"):
    print("📁 فایل دیتابیس پیدا نشد!")
    if restore_db():
        print("✅ دیتابیس از بکاپ بازیابی شد!")
    else:
        print("📁 در حال ساخت دیتابیس جدید...")

# ========================================
# ===== اتصال به دیتابیس =====
# ========================================

db = sqlite3.connect("bot.db", check_same_thread=False)
c = db.cursor()

print("🔗 اتصال به دیتابیس برقرار شد!")

# ========================================
# ===== ساخت جدول‌ها =====
# ========================================

c.execute("""
    CREATE TABLE IF NOT EXISTS files (
        code TEXT PRIMARY KEY,
        file_id TEXT NOT NULL,
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
    CREATE TABLE IF NOT EXISTS banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT DEFAULT 'text',
        file_id TEXT,
        text TEXT,
        expire_date TEXT,
        schedule_time TEXT,
        created_at TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        join_date TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        date TEXT
    )
""")

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

c.execute("""
    CREATE TABLE IF NOT EXISTS broadcast (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        date TEXT,
        status TEXT DEFAULT 'pending'
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS reaction_post (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_link TEXT
    )
""")

db.commit()
print("✅ تمام جدول‌ها با موفقیت ساخته شدند!")

# ========================================
# ===== اضافه کردن کانال‌های پیش‌فرض =====
# ========================================

for ch in DEFAULT_CHANNELS:
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (ch,))
db.commit()
print(f"✅ کانال‌های پیش‌فرض اضافه شدند: {', '.join(DEFAULT_CHANNELS)}")

# ========================================
# ===== بکاپ خودکار =====
# ========================================

backup_db()

# ========================================
# ===== توابع فایل‌ها =====
# ========================================

def save_file(code, file_id, file_type="document", caption=""):
    c.execute("""
        INSERT OR REPLACE INTO files (code, file_id, type, caption)
        VALUES (?, ?, ?, ?)
    """, (code, file_id, file_type, caption))
    db.commit()
    backup_db()  # بعد از هر تغییر، بکاپ بگیر
    print(f"📁 فایل با کد '{code}' ذخیره شد")
    return True

def find_file(code):
    c.execute("""
        SELECT file_id, type, caption
        FROM files
        WHERE code = ?
    """, (code,))
    row = c.fetchone()
    return row if row else None

def delete_file(code):
    c.execute("DELETE FROM files WHERE code = ?", (code,))
    db.commit()
    backup_db()
    return True

def get_all_files():
    c.execute("""
        SELECT code, type, caption
        FROM files
        ORDER BY code
    """)
    return c.fetchall()

def increment_download(code):
    c.execute("""
        UPDATE files
        SET downloads = downloads + 1
        WHERE code = ?
    """, (code,))
    db.commit()
    return True

# ========================================
# ===== توابع کانال‌ها =====
# ========================================

def add_channel(username):
    username = username.replace("@", "").strip()
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()
    backup_db()
    return True

def delete_channel(username):
    username = username.replace("@", "").strip()
    c.execute("DELETE FROM channels WHERE username = ?", (username,))
    db.commit()
    backup_db()
    return True

def get_channels():
    c.execute("SELECT username FROM channels ORDER BY username")
    rows = c.fetchall()
    return [row[0] for row in rows]

# ========================================
# ===== توابع بنر =====
# ========================================

def add_banner(banner_type, file_id=None, text="", expire_date=None, schedule_time=None):
    c.execute("""
        INSERT INTO banners (type, file_id, text, expire_date, schedule_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (banner_type, file_id, text, expire_date, schedule_time, datetime.now().isoformat()))
    db.commit()
    backup_db()
    return c.lastrowid

def get_all_banners():
    c.execute("""
        SELECT id, type, file_id, text, expire_date, schedule_time
        FROM banners
        ORDER BY created_at DESC
    """)
    rows = c.fetchall()
    banners = []
    for row in rows:
        banners.append({
            "id": row[0],
            "type": row[1],
            "file_id": row[2],
            "text": row[3] or "",
            "expire_date": row[4],
            "schedule_time": row[5]
        })
    return banners

def get_active_banner():
    now = datetime.now().isoformat()
    c.execute("DELETE FROM banners WHERE expire_date IS NOT NULL AND expire_date < ?", (now,))
    db.commit()
    
    c.execute("""
        SELECT id, type, file_id, text
        FROM banners
        WHERE (expire_date IS NULL OR expire_date > ?)
        AND (schedule_time IS NULL OR schedule_time <= ?)
        ORDER BY created_at DESC
        LIMIT 1
    """, (now, now))
    
    row = c.fetchone()
    if row:
        return {
            "id": row[0],
            "type": row[1],
            "file_id": row[2],
            "text": row[3] or ""
        }
    return {"type": "text", "file_id": None, "text": "📢 به ربات خوش اومدی!"}

def delete_banner(banner_id):
    c.execute("DELETE FROM banners WHERE id = ?", (banner_id,))
    db.commit()
    backup_db()
    return True

def get_banner_count():
    c.execute("SELECT COUNT(*) FROM banners")
    return c.fetchone()[0]

# ========================================
# ===== توابع کاربران =====
# ========================================

def add_user(user_id):
    c.execute("""
        INSERT OR IGNORE INTO users (user_id, join_date)
        VALUES (?, ?)
    """, (user_id, datetime.now().isoformat()))
    db.commit()
    return True

def get_all_users():
    c.execute("SELECT user_id FROM users ORDER BY user_id")
    rows = c.fetchall()
    return [row[0] for row in rows]

def get_user_count():
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]

# ========================================
# ===== توابع نظرات =====
# ========================================

def add_feedback(user_id, message):
    c.execute("""
        INSERT INTO feedback (user_id, message, date)
        VALUES (?, ?, ?)
    """, (user_id, message, datetime.now().isoformat()))
    db.commit()
    return True

def get_all_feedback():
    c.execute("""
        SELECT id, user_id, message, date
        FROM feedback
        ORDER BY date DESC
    """)
    return c.fetchall()

# ========================================
# ===== توابع سوالات =====
# ========================================

def add_question(user_id, question):
    c.execute("""
        INSERT INTO questions (user_id, question, date, status)
        VALUES (?, ?, ?, ?)
    """, (user_id, question, datetime.now().isoformat(), "pending"))
    db.commit()
    return True

def get_pending_questions():
    c.execute("""
        SELECT id, user_id, question, date
        FROM questions
        WHERE status = 'pending'
        ORDER BY date ASC
    """)
    return c.fetchall()

def get_question_data(question_id):
    c.execute("""
        SELECT user_id, question
        FROM questions
        WHERE id = ?
    """, (question_id,))
    return c.fetchone()

def answer_question(question_id, answer):
    c.execute("""
        UPDATE questions
        SET answer = ?, status = 'answered'
        WHERE id = ?
    """, (answer, question_id))
    db.commit()
    return True

# ========================================
# ===== توابع زمان‌بندی =====
# ========================================

def add_scheduled_broadcast(message, send_date, status="pending"):
    c.execute("""
        INSERT INTO broadcast (message, date, status)
        VALUES (?, ?, ?)
    """, (message, send_date, status))
    db.commit()
    return True

def get_pending_broadcasts():
    c.execute("""
        SELECT id, message, date
        FROM broadcast
        WHERE status = 'pending'
        ORDER BY date ASC
    """)
    return c.fetchall()

def update_broadcast_status(broadcast_id, status):
    c.execute("""
        UPDATE broadcast
        SET status = ?
        WHERE id = ?
    """, (status, broadcast_id))
    db.commit()
    return True

# ========================================
# ===== توابع ری اکشن پست =====
# ========================================

def set_reaction_post(post_link):
    c.execute("DELETE FROM reaction_post")
    c.execute("INSERT INTO reaction_post (post_link) VALUES (?)", (post_link,))
    db.commit()
    return True

def get_reaction_post():
    c.execute("SELECT post_link FROM reaction_post ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row else None

def delete_reaction_post():
    c.execute("DELETE FROM reaction_post")
    db.commit()
    return True

# ========================================
# ===== توابع کمکی =====
# ========================================

def get_db_stats():
    return {
        "files": len(get_all_files()),
        "channels": len(get_channels()),
        "banners": get_banner_count(),
        "users": get_user_count(),
        "feedback": len(get_all_feedback()),
        "questions": len(get_pending_questions())
    }

def close_db():
    db.close()
    return True

print("✅ دیتابیس با موفقیت راه‌اندازی شد!")
print("=" * 50)
