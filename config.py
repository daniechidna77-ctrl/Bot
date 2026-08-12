import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 8255361263))
DB_PATH = os.getenv("DB_PATH", "bot.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # ← این خط مونده ولی از ریلیوی میخونه

DEFAULT_CHANNELS = [
    "animee56",
    "meloriiina",
    "Yuriiteam77"
]

if not BOT_TOKEN:
    raise ValueError("❌ توکن ربات تنظیم نشده!")
