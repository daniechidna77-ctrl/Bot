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

# جدول بنر (با تاریخ انقضا)
c.execute("""
    CREATE TABLE IF NOT EXISTS banner (
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
    """
    ذخیره فایل جدید در دیتابیس
    اگر فایل با همین کد وجود داشته باشد، جایگزین می‌شود
    """
    c.execute("""
        INSERT OR REPLACE INTO files (code, file_id, type, caption)
        VALUES (?, ?, ?, ?)
    """, (code, file_id, file_type, caption))
    db.commit()
    print(f"📁 فایل با کد '{code}' ذخیره شد (نوع: {file_type})")
    return True

def find_file(code):
    """
    پیدا کردن فایل بر اساس کد چپتر
    بازگشت: (file_id, type, caption) یا None
    """
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
    """
    حذف فایل بر اساس کد چپتر
    """
    c.execute("DELETE FROM files WHERE code = ?", (code,))
    db.commit()
    print(f"🗑 فایل با کد '{code}' حذف شد")
    return True

def get_all_files():
    """
    دریافت لیست همه فایل‌ها
    بازگشت: لیستی از (code, type, caption)
    """
    c.execute("""
        SELECT code, type, caption
        FROM files
        ORDER BY code
    """)
    rows = c.fetchall()
    print(f"📋 تعداد کل فایل‌ها: {len(rows)}")
    return rows

def increment_download(code):
    """
    افزایش تعداد دانلود یک چپتر
    """
    c.execute("""
        UPDATE files
        SET downloads = downloads + 1
        WHERE code = ?
    """, (code,))
    db.commit()
    print(f"📥 دانلود چپتر '{code}' ثبت شد")
    return True

def get_download_count(code):
    """
    دریافت تعداد دانلود یک چپتر
    """
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
    """
    اضافه کردن کانال جدید به لیست عضویت اجباری
    """
    username = username.replace("@", "").strip()
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()
    print(f"📢 کانال @{username} اضافه شد")
    return True

def delete_channel(username):
    """
    حذف کانال از لیست عضویت اجباری
    """
    username = username.replace("@", "").strip()
    c.execute("DELETE FROM channels WHERE username = ?", (username,))
    db.commit()
    print(f"🗑 کانال @{username} حذف شد")
    return True

def get_channels():
    """
    دریافت لیست همه کانال‌های اجباری
    بازگشت: لیستی از نام‌های کاربری
    """
    c.execute("SELECT username FROM channels ORDER BY username")
    rows = c.fetchall()
    channels = [row[0] for row in rows]
    print(f"📋 تعداد کانال‌های اجباری: {len(channels)}")
    return channels

def get_channels_count():
    """
    دریافت تعداد کانال‌های اجباری
    """
    c.execute("SELECT COUNT(*) FROM channels")
    return c.fetchone()[0]

# ========================================
# ===== توابع مربوط به بنر =====
# ========================================

def set_banner(text, expire_date=None):
    """
    تنظیم بنر جدید با تاریخ انقضا (اختیاری)
    """
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?, ?)", (text, expire_date))
    db.commit()
    if expire_date:
        print(f"📝 بنر جدید با تاریخ انقضا {expire_date} ذخیره شد")
    else:
        print("📝 بنر جدید بدون تاریخ انقضا ذخیره شد")
    return True

def get_banner():
    """
    دریافت بنر فعلی
    اگر تاریخ انقضا گذشته باشد، بنر پیش‌فرض برمی‌گردد
    """
    c.execute("SELECT text, expire_date FROM banner LIMIT 1")
    row = c.fetchone()
    
    if row:
        text, expire_date = row
        # بررسی تاریخ انقضا
        if expire_date:
            try:
                expire_datetime = datetime.fromisoformat(expire_date)
                if datetime.now() > expire_datetime:
                    print("⏰ بنر منقضی شده است")
                    return "📢 به ربات خوش اومدی!"
            except:
                pass
        print("📝 بنر فعلی دریافت شد")
        return text
    
    print("📝 هیچ بنری تنظیم نشده، بنر پیش‌فرض استفاده می‌شود")
    return "📢 به ربات خوش اومدی!"

def delete_banner():
    """
    حذف بنر فعلی
    """
    c.execute("DELETE FROM banner")
    db.commit()
    print("🗑 بنر حذف شد")
    return True

def get_banner_expire_date():
    """
    دریافت تاریخ انقضای بنر
    """
    c.execute("SELECT expire_date FROM banner LIMIT 1")
    row = c.fetchone()
    return row[0] if row and row[0] else None

# ========================================
# ===== توابع مربوط به کاربران =====
# ========================================

def add_user(user_id):
    """
    ثبت کاربر جدید در دیتابیس
    اگر کاربر وجود داشته باشد، نادیده گرفته می‌شود
    """
    c.execute("""
        INSERT OR IGNORE INTO users (user_id, join_date)
        VALUES (?, ?)
    """, (user_id, datetime.now().isoformat()))
    db.commit()
    print(f"👤 کاربر {user_id} ثبت شد")
    return True

def get_all_users():
    """
    دریافت لیست همه کاربران
    """
    c.execute("SELECT user_id FROM users ORDER BY user_id")
    rows = c.fetchall()
    users = [row[0] for row in rows]
    print(f"👥 تعداد کل کاربران: {len(users)}")
    return users

def get_user_count():
    """
    دریافت تعداد کل کاربران
    """
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    print(f"👥 تعداد کاربران: {count}")
    return count

def get_user_join_date(user_id):
    """
    دریافت تاریخ ثبت‌نام یک کاربر
    """
    c.execute("SELECT join_date FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    return row[0] if row else None

# ========================================
# ===== توابع مربوط به نظرات =====
# ========================================

def add_feedback(user_id, message):
    """
    ثبت نظر یا پیشنهاد جدید
    """
    c.execute("""
        INSERT INTO feedback (user_id, message, date)
        VALUES (?, ?, ?)
    """, (user_id, message, datetime.now().isoformat()))
    db.commit()
    print(f"💬 نظر جدید از کاربر {user_id} ثبت شد")
    return True

def get_all_feedback():
    """
    دریافت لیست همه نظرات (به ترتیب جدیدترین)
    """
    c.execute("""
        SELECT id, user_id, message, date
        FROM feedback
        ORDER BY date DESC
    """)
    rows = c.fetchall()
    print(f"💬 تعداد کل نظرات: {len(rows)}")
    return rows

def get_feedback_by_user(user_id):
    """
    دریافت نظرات یک کاربر خاص
    """
    c.execute("""
        SELECT id, message, date
        FROM feedback
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    return c.fetchall()

def delete_feedback(feedback_id):
    """
    حذف یک نظر بر اساس ID
    """
    c.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    db.commit()
    print(f"🗑 نظر {feedback_id} حذف شد")
    return True

# ========================================
# ===== توابع مربوط به سوالات =====
# ========================================

def add_question(user_id, question):
    """
    ثبت سوال جدید
    """
    c.execute("""
        INSERT INTO questions (user_id, question, date, status)
        VALUES (?, ?, ?, ?)
    """, (user_id, question, datetime.now().isoformat(), "pending"))
    db.commit()
    print(f"❓ سوال جدید از کاربر {user_id} ثبت شد")
    return True

def get_pending_questions():
    """
    دریافت لیست سوالات بدون پاسخ
    """
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
    """
    دریافت لیست همه سوالات
    """
    c.execute("""
        SELECT id, user_id, question, answer, date, status
        FROM questions
        ORDER BY date DESC
    """)
    return c.fetchall()

def get_question_data(question_id):
    """
    دریافت اطلاعات یک سوال بر اساس ID
    """
    c.execute("""
        SELECT user_id, question
        FROM questions
        WHERE id = ?
    """, (question_id,))
    row = c.fetchone()
    return row if row else None

def answer_question(question_id, answer):
    """
    ثبت پاسخ برای یک سوال
    """
    c.execute("""
        UPDATE questions
        SET answer = ?, status = 'answered'
        WHERE id = ?
    """, (answer, question_id))
    db.commit()
    print(f"✏️ پاسخ سوال {question_id} ثبت شد")
    return True

def get_user_questions(user_id):
    """
    دریافت سوالات یک کاربر خاص
    """
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
    """
    ثبت پیام زمان‌بندی شده
    """
    c.execute("""
        INSERT INTO broadcast (message, date, status)
        VALUES (?, ?, ?)
    """, (message, send_date, status))
    db.commit()
    print(f"⏰ پیام زمان‌بندی شده در {send_date} ثبت شد")
    return True

def get_pending_broadcasts():
    """
    دریافت لیست پیام‌های زمان‌بندی شده که هنوز ارسال نشده‌اند
    """
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
    """
    به‌روزرسانی وضعیت یک پیام زمان‌بندی شده
    """
    c.execute("""
        UPDATE broadcast
        SET status = ?
        WHERE id = ?
    """, (status, broadcast_id))
    db.commit()
    print(f"⏰ وضعیت پیام {broadcast_id} به {status} تغییر کرد")
    return True

def get_all_broadcasts():
    """
    دریافت لیست همه پیام‌های زمان‌بندی شده
    """
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
    """
    ثبت لینک پست برای ری اکشن
    """
    c.execute("DELETE FROM reaction_post")
    c.execute("INSERT INTO reaction_post (post_link) VALUES (?)", (post_link,))
    db.commit()
    print(f"👍 لینک پست ری اکشن ذخیره شد: {post_link}")
    return True

def get_reaction_post():
    """
    دریافت لینک پست ری اکشن
    """
    c.execute("SELECT post_link FROM reaction_post ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    if row:
        print(f"👍 لینک پست ری اکشن: {row[0]}")
        return row[0]
    print("👍 هیچ پست ری اکشنی تنظیم نشده")
    return None

def delete_reaction_post():
    """
    حذف لینک پست ری اکشن
    """
    c.execute("DELETE FROM reaction_post")
    db.commit()
    print("🗑 پست ری اکشن حذف شد")
    return True

# ========================================
# ===== توابع کمکی و ابزاری =====
# ========================================

def clear_all_data():
    """
    پاک کردن همه داده‌ها (فقط برای مدیریت)
    """
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
    """
    دریافت آمار کلی دیتابیس
    """
    stats = {
        "files": get_all_files(),
        "channels": get_channels(),
        "users": get_user_count(),
        "feedback": len(get_all_feedback()),
        "questions": len(get_pending_questions()),
        "broadcast": len(get_pending_broadcasts())
    }
    print(f"📊 آمار دیتابیس: {stats}")
    return stats

# ========================================
# ===== بستن اتصال دیتابیس =====
# ========================================

def close_db():
    """
    بستن اتصال دیتابیس
    """
    db.close()
    print("🔗 اتصال دیتابیس بسته شد")
    return True

print("✅ دیتابیس با موفقیت راه‌اندازی شد!")
print("=" * 50)
