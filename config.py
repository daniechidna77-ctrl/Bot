import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 8255361263))
DB_PATH = os.getenv("DB_PATH", "bot.db")

# ===== جیمینای - با پرینت برای دیباگ =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"🔍 GEMINI_API_KEY found: {GEMINI_API_KEY is not None}")
if GEMINI_API_KEY:
    print(f"🔍 GEMINI_API_KEY starts with: {GEMINI_API_KEY[:10]}...")
else:
    print("❌ GEMINI_API_KEY NOT FOUND!")

if not BOT_TOKEN:
    raise ValueError("❌ توکن ربات تنظیم نشده!")
