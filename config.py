import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 8255361263))
DB_PATH = os.getenv("DB_PATH", "bot.db")

# ===== اینجا کلید جیمینای رو مستقیم بذار (فعلاً برای تست) =====
GEMINI_API_KEY = "AQ.Ab8RN6Il2BXtpIfnOmM5DftCPSNoZeb4d3zUIRxMFGJ0me_zBw"

if not BOT_TOKEN:
    raise ValueError("❌ توکن ربات تنظیم نشده!")
