import sqlite3
import os
from datetime import datetime, timedelta
from config import DEFAULT_CHANNELS

# ========================================
# ===== بررسی وجود دیتابیس =====
# ========================================

if not os.path.exists("bot.db"):
    print("📁 فایل دیتابیس پیدا نشد، در حال ساخت دیتابیس جدید...")

# ========================================
# ===== اتصال به دیتابیس =====
# ========================================

db = sqlite3.connect("bot.db", check_same_thread=False)
c = db.cursor()

print("🔗 اتصال به دیتابیس برقرار شد!")

# ========================================
# ===== ساخت جدول‌ها =====
# ========================================

# جدول فایل‌ها (چپترها)
c.execute("""
    CREATE TABLE IF NOT EXISTS files (
        code TEXT PRIMARY KEY,
        file_id TEXT NOT NULL,
        type TEXT DEFAULT 'document',
        caption TEXT,
        downloads INTEGER DEFAULT 0
    )
""")

# جدول کانال‌های اجباری
c.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        username TEXT PRIMARY KEY
    )
""")

# جدول بنر (با پشتیبانی از عکس و ویدیو)
c.execute("""
    CREATE TABLE IF NOT EXISTS banner (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT DEFAULT 'text',
        file_id TEXT,
        text TEXT,
        expire_date TEXT
    )
""")

# جدول کاربران
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        join_date TEXT
    )
""")

# جدول نظرات و پیشنهادات
c.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        date TEXT
    )
""")

# جدول سوالات کاربران
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

# جدول پیام‌های زمان‌بندی شده
c.execute("""
    CREATE TABLE IF NOT EXISTS broadcast (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        date TEXT,
        status TEXT DEFAULT 'pending'
    )
""")

# جدول لینک پست برای ری اکشن
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
# ===== توابع مربوط به فایل‌ها (چپترها) =====
# ========================================

def save_file(code, file_id, file_type="document", caption=""):
    c.execute("""
        INSERT OR REPLACE INTO files (code, file_id, type, caption)
        VALUES (?, ?, ?, ?)
    """, (code, file_id, file_type, caption))
    db.commit()
    print(f"📁 فایل با کد '{code}' ذخیره شد (نوع: {file_type})")
    return True

def find_file(code):
    c.execute("""
        SELECT file_id, type, caption
        FROM files
        WHERE code = ?
    """, (code,))
    row = c.fetchone()
    if row:
        print(f"🔍 فایل با کد '{code}' پیدا شد")
        return row
    print(f"❌ فایل با کد '{code}' پیدا نشد")
    return None

def delete_file(code):
    c.execute("DELETE FROM files WHERE code = ?", (code,))
    db.commit()
    print(f"🗑 فایل با کد '{code}' حذف شد")
    return True

def get_all_files():
    c.execute("""
        SELECT code, type, caption
        FROM files
        ORDER BY code
    """)
    rows = c.fetchall()
    print(f"📋 تعداد کل فایل‌ها: {len(rows)}")
    return rows

def increment_download(code):
    c.execute("""
        UPDATE files
        SET downloads = downloads + 1
        WHERE code = ?
    """, (code,))
    db.commit()
    print(f"📥 دانلود چپتر '{code}' ثبت شد")
    return True

def get_download_count(code):
    c.execute("""
        SELECT downloads
        FROM files
        WHERE code = ?
    """, (code,))
    row = c.fetchone()
    return row[0] if row else 0

# ========================================
# ===== توابع مربوط به کانال‌ها =====
# ========================================

def add_channel(username):
    username = username.replace("@", "").strip()
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()
    print(f"📢 کانال @{username} اضافه شد")
    return True

def delete_channel(username):
    username = username.replace("@", "").strip()
    c.execute("DELETE FROM channels WHERE username = ?", (username,))
    db.commit()
    print(f"🗑 کانال @{username} حذف شد")
    return True

def get_channels():
    c.execute("SELECT username FROM channels ORDER BY username")
    rows = c.fetchall()
    channels = [row[0] for row in rows]
    print(f"📋 تعداد کانال‌های اجباری: {len(channels)}")
    return channels

def get_channels_count():
    c.execute("SELECT COUNT(*) FROM channels")
    return c.fetchone()[0]

# ========================================
# ===== توابع مربوط به بنر (با عکس و ویدیو) =====
# ========================================

def set_banner_text(text, expire_date=None):
    """تنظیم بنر به صورت متن"""
    c.execute("DELETE FROM banner")
    c.execute("""
        INSERT INTO banner (type, text, expire_date)
        VALUES (?, ?, ?)
    """, ("text", text, expire_date))
    db.commit()
    print(f"📝 بنر متنی ذخیره شد: {text}")
    return True

def set_banner_photo(file_id, caption="", expire_date=None):
    """تنظیم بنر به صورت عکس"""
    c.execute("DELETE FROM banner")
    c.execute("""
        INSERT INTO banner (type, file_id, text, expire_date)
        VALUES (?, ?, ?, ?)
    """, ("photo", file_id, caption, expire_date))
    db.commit()
    print(f"🖼 بنر عکس ذخیره شد")
    return True

def set_banner_video(file_id, caption="", expire_date=None):
    """تنظیم بنر به صورت ویدیو"""
    c.execute("DELETE FROM banner")
    c.execute("""
        INSERT INTO banner (type, file_id, text, expire_date)
        VALUES (?, ?, ?, ?)
    """, ("video", file_id, caption, expire_date))
    db.commit()
    print(f"🎬 بنر ویدیو ذخیره شد")
    return True

def get_banner():
    """دریافت بنر فعلی (متن، عکس یا ویدیو)"""
    c.execute("""
        SELECT type, file_id, text, expire_date
        FROM banner
        ORDER BY id DESC LIMIT 1
    """)
    row = c.fetchone()
    
    if row:
        banner_type, file_id, text, expire_date = row
        
        # بررسی تاریخ انقضا
        if expire_date:
            try:
                expire_datetime = datetime.fromisoformat(expire_date)
                if datetime.now() > expire_datetime:
                    print("⏰ بنر منقضی شده است")
                    return {"type": "text", "file_id": None, "text": "📢 به ربات خوش اومدی!"}
            except:
                pass
        
        print(f"📝 بنر فعلی دریافت شد (نوع: {banner_type})")
        return {
            "type": banner_type,
            "file_id": file_id,
            "text": text or ""
        }
    
    print("📝 هیچ بنری تنظیم نشده، بنر پیش‌فرض استفاده می‌شود")
    return {"type": "text", "file_id": None, "text": "📢 به ربات خوش اومدی!"}

def delete_banner():
    """حذف بنر فعلی"""
    c.execute("DELETE FROM banner")
    db.commit()
    print("🗑 بنر حذف شد")
    return True

def get_banner_expire_date():
    """دریافت تاریخ انقضای بنر"""
    c.execute("SELECT expire_date FROM banner ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row and row[0] else None

def get_banner_type():
    """دریافت نوع بنر (text, photo, video)"""
    c.execute("SELECT type FROM banner ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    return row[0] if row else "text"

# ========================================
# ===== توابع مربوط به کاربران =====
# ========================================

def add_user(user_id):
    c.execute("""
        INSERT OR IGNORE INTO users (user_id, join_date)
        VALUES (?, ?)
    """, (user_id, datetime.now().isoformat()))
    db.commit()
    print(f"👤 کاربر {user_id} ثبت شد")
    return True

def get_all_users():
    c.execute("SELECT user_id FROM users ORDER BY user_id")
    rows = c.fetchall()
    users = [row[0] for row in rows]
    print(f"👥 تعداد کل کاربران: {len(users)}")
    return users

def get_user_count():
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    print(f"👥 تعداد کاربران: {count}")
    return count

def get_user_join_date(user_id):
    c.execute("SELECT join_date FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    return row[0] if row else None

# ========================================
# ===== توابع مربوط به نظرات =====
# ========================================

def add_feedback(user_id, message):
    c.execute("""
        INSERT INTO feedback (user_id, message, date)
        VALUES (?, ?, ?)
    """, (user_id, message, datetime.now().isoformat()))
    db.commit()
    print(f"💬 نظر جدید از کاربر {user_id} ثبت شد")
    return True

def get_all_feedback():
    c.execute("""
        SELECT id, user_id, message, date
        FROM feedback
        ORDER BY date DESC
    """)
    rows = c.fetchall()
    print(f"💬 تعداد کل نظرات: {len(rows)}")
    return rows

def get_feedback_by_user(user_id):
    c.execute("""
        SELECT id, message, date
        FROM feedback
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    return c.fetchall()

def delete_feedback(feedback_id):
    c.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    db.commit()
    print(f"🗑 نظر {feedback_id} حذف شد")
    return True

# ========================================
# ===== توابع مربوط به سوالات =====
# ========================================

def add_question(user_id, question):
    c.execute("""
        INSERT INTO questions (user_id, question, date, status)
        VALUES (?, ?, ?, ?)
    """, (user_id, question, datetime.now().isoformat(), "pending"))
    db.commit()
    print(f"❓ سوال جدید از کاربر {user_id} ثبت شد")
    return True

def get_pending_questions():
    c.execute("""
        SELECT id, user_id, question, date
        FROM questions
        WHERE status = 'pending'
        ORDER BY date ASC
    """)
    rows = c.fetchall()
    print(f"❓ تعداد سوالات بدون پاسخ: {len(rows)}")
    return rows

def get_all_questions():
    c.execute("""
        SELECT id, user_id, question, answer, date, status
        FROM questions
        ORDER BY date DESC
    """)
    return c.fetchall()

def get_question_data(question_id):
    c.execute("""
        SELECT user_id, question
        FROM questions
        WHERE id = ?
    """, (question_id,))
    row = c.fetchone()
    return row if row else None

def answer_question(question_id, answer):
    c.execute("""
        UPDATE questions
        SET answer = ?, status = 'answered'
        WHERE id = ?
    """, (answer, question_id))
    db.commit()
    print(f"✏️ پاسخ سوال {question_id} ثبت شد")
    return True

def get_user_questions(user_id):
    c.execute("""
        SELECT question, answer, status, date
        FROM questions
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    return c.fetchall()

# ========================================
# ===== توابع مربوط به زمان‌بندی =====
# ========================================

def add_scheduled_broadcast(message, send_date, status="pending"):
    c.execute("""
        INSERT INTO broadcast (message, date, status)
        VALUES (?, ?, ?)
    """, (message, send_date, status))
    db.commit()
    print(f"⏰ پیام زمان‌بندی شده در {send_date} ثبت شد")
    return True

def get_pending_broadcasts():
    c.execute("""
        SELECT id, message, date
        FROM broadcast
        WHERE status = 'pending'
        ORDER BY date ASC
    """)
    rows = c.fetchall()
    print(f"⏰ تعداد پیام‌های زمان‌بندی شده: {len(rows)}")
    return rows

def update_broadcast_status(broadcast_id, status):
    c.execute("""
        UPDATE broadcast
        SET status = ?
        WHERE id = ?
    """, (status, broadcast_id))
    db.commit()
    print(f"⏰ وضعیت پیام {broadcast_id} به {status} تغییر کرد")
    return True

def get_all_broadcasts():
    c.execute("""
        SELECT id, message, date, status
        FROM broadcast
        ORDER BY date DESC
    """)
    return c.fetchall()

# ========================================
# ===== توابع مربوط به ری اکشن پست =====
# ========================================

def set_reaction_post(post_link):
    c.execute("DELETE FROM reaction_post")
    c.execute("INSERT INTO reaction_post (post_link) VALUES (?)", (post_link,))
    db.commit()
    print(f"👍 لینک پست ری اکشن ذخیره شد: {post_link}")
    return True

def get_reaction_post():
    c.execute("SELECT post_link FROM reaction_post ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    if row:
        print(f"👍 لینک پست ری اکشن: {row[0]}")
        return row[0]
    print("👍 هیچ پست ری اکشنی تنظیم نشده")
    return None

def delete_reaction_post():
    c.execute("DELETE FROM reaction_post")
    db.commit()
    print("🗑 پست ری اکشن حذف شد")
    return True

# ========================================
# ===== توابع کمکی و ابزاری =====
# ========================================

def clear_all_data():
    c.execute("DELETE FROM files")
    c.execute("DELETE FROM channels")
    c.execute("DELETE FROM banner")
    c.execute("DELETE FROM users")
    c.execute("DELETE FROM feedback")
    c.execute("DELETE FROM questions")
    c.execute("DELETE FROM broadcast")
    c.execute("DELETE FROM reaction_post")
    db.commit()
    print("🗑 تمام داده‌ها پاک شدند")
    return True

def get_db_stats():
    stats = {
        "files": len(get_all_files()),
        "channels": len(get_channels()),
        "users": get_user_count(),
        "feedback": len(get_all_feedback()),
        "questions": len(get_pending_questions()),
        "broadcast": len(get_pending_broadcasts())
    }
    print(f"📊 آمار دیتابیس: {stats}")
    return stats

def close_db():
    db.close()
    print("🔗 اتصال دیتابیس بسته شد")
    return True

print("✅ دیتابیس با موفقیت راه‌اندازی شد!")
print("=" * 50)
