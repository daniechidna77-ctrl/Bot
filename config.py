import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 8255361263))
DB_PATH = os.getenv("DB_PATH", "bot.db")

# ===== جیمینای با دیباگ کامل =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("=" * 50)
print("🔍 بررسی متغیرهای محیطی:")
print(f"BOT_TOKEN: {'✅ موجود' if BOT_TOKEN else '❌ پیدا نشد'}")
print(f"ADMIN_ID: {ADMIN_ID}")
print(f"DB_PATH: {DB_PATH}")
print(f"GEMINI_API_KEY: {'✅ موجود' if GEMINI_API_KEY else '❌ پیدا نشد'}")
if GEMINI_API_KEY:
    print(f"🔑 کلید جیمینای: {GEMINI_API_KEY[:15]}...")
print("=" * 50)

if not BOT_TOKEN:
    raise ValueError("❌ توکن ربات تنظیم نشده!")
