import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8255361263))

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN تنظیم نشده!")
