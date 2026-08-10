import sqlite3
import os

print("📁 در حال ساخت دیتابیس...")

# حذف دیتابیس قدیمی (اگه خراب باشه)
if os.path.exists("bot.db"):
    os.remove("bot.db")
    print("🗑 دیتابیس قدیمی حذف شد")

# ساخت دیتابیس جدید
db = sqlite3.connect("bot.db")
c = db.cursor()

# ===== ساخت جدول‌ها =====
c.execute("CREATE TABLE IF NOT EXISTS files (code TEXT PRIMARY KEY, file_id TEXT, type TEXT, caption TEXT, downloads INTEGER DEFAULT 0)")
c.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)")
c.execute("CREATE TABLE IF NOT EXISTS banner (text TEXT, expire_date TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, join_date TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, message TEXT, date TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, question TEXT, answer TEXT, date TEXT, status TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS broadcast (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, date TEXT, status TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS reaction_post (id INTEGER PRIMARY KEY AUTOINCREMENT, post_link TEXT)")

db.commit()
db.close()

print("✅ دیتابیس با موفقیت ساخته شد!")
print("📁 فایل bot.db ایجاد شد")
