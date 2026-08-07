import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8255361263))

# کانال‌های پیش‌فرض (همینجا اضافه کن)
DEFAULT_CHANNELS = [
    "melorina77",
    "Yuriii789",
    "yuriii42"
]

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN تنظیم نشده!")
