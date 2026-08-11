import asyncio
import sqlite3
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ===== تنظیمات =====
TOKEN = "توکن_ربات_اینجا"  # از @BotFather بگیر
ADMIN_ID = 8255361263  # آیدی عددی خودت

# ===== دیتابیس =====
DB_PATH = os.environ.get("DB_PATH", "bot.db")
db = sqlite3.connect(DB_PATH)
c = db.cursor()

# ===== ساخت جدول‌ها =====
c.execute("CREATE TABLE IF NOT EXISTS files (code TEXT PRIMARY KEY, file_id TEXT, type TEXT, caption TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)")
c.execute("CREATE TABLE IF NOT EXISTS banner (type TEXT, file_id TEXT, text TEXT)")
db.commit()

# ===== کانال‌های پیش‌فرض =====
default_channels = ["animee56", "meloriiina", "Yuriiteam77"]
for ch in default_channels:
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (ch,))
db.commit()

# ===== توابع دیتابیس =====
def save_file(code, file_id, file_type="document", caption=""):
    c.execute("INSERT OR REPLACE INTO files VALUES (?,?,?,?)", (code, file_id, file_type, caption))
    db.commit()

def find_file(code):
    c.execute("SELECT file_id, type, caption FROM files WHERE code=?", (code,))
    return c.fetchone()

def get_all_files():
    c.execute("SELECT code, type, caption FROM files")
    return c.fetchall()

def delete_file(code):
    c.execute("DELETE FROM files WHERE code=?", (code,))
    db.commit()

def add_channel(username):
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()

def get_channels():
    c.execute("SELECT username FROM channels")
    return [row[0] for row in c.fetchall()]

def delete_channel(username):
    c.execute("DELETE FROM channels WHERE username=?", (username,))
    db.commit()

def set_banner(banner_type, file_id=None, text=""):
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?,?,?)", (banner_type, file_id, text))
    db.commit()

def get_banner():
    c.execute("SELECT type, file_id, text FROM banner")
    row = c.fetchone()
    if row:
        return {"type": row[0], "file_id": row[1], "text": row[2] or ""}
    return {"type": "text", "file_id": None, "text": "📢 به ربات خوش اومدی!"}

def delete_banner():
    c.execute("DELETE FROM banner")
    db.commit()

# ===== ربات =====
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== کیبورد عضویت =====
def join_keyboard():
    channels = get_channels()
    buttons = []
    for ch in channels:
        buttons.append([types.InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    buttons.append([types.InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

# ===== تابع ارسال بنر =====
async def send_banner(message):
    banner = get_banner()
    if banner["type"] == "photo" and banner["file_id"]:
        await message.answer_photo(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "video" and banner["file_id"]:
        await message.answer_video(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "document" and banner["file_id"]:
        await message.answer_document(banner["file_id"], caption=banner["text"])
    else:
        await message.answer(banner["text"])

# ========================================
# ===== استارت =====
# ========================================
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    
    # استارت معمولی
    if len(args) == 1:
        await send_banner(message)
        await message.answer(
            f"👋 **سلام {message.from_user.first_name}!**\n\n"
            "برای دریافت چپتر از لینک مخصوص استفاده کن.\n"
            "مثال: `https://t.me/ربات?start=1`"
        )
        return
    
    # استارت با کد چپتر
    code = args[1]
    channels = get_channels()
    
    if channels:
        with open("temp.json", "w") as f:
            json.dump({"code": code}, f)
        await message.answer(
            "🔒 **لطفاً در کانال‌های زیر عضو شوید:**",
            reply_markup=join_keyboard()
        )
        return
    
    # اگه کانالی نبود، مستقیم فایل و بنر بفرست
    await send_file_and_banner(message, code)

# ========================================
# ===== تابع ارسال فایل + بنر =====
# ========================================
async def send_file_and_banner(message, code):
    file_info = find_file(code)
    if file_info:
        file_id, file_type, caption = file_info
        if file_type == "document":
            await message.answer_document(file_id, caption=caption or f"📖 چپتر {code}")
        elif file_type == "photo":
            await message.answer_photo(file_id, caption=caption or f"📖 چپتر {code}")
        elif file_type == "video":
            await message.answer_video(file_id, caption=caption or f"📖 چپتر {code}")
        else:
            await message.answer_document(file_id, caption=caption or f"📖 چپتر {code}")
        
        # ارسال بنر پایین فایل
        await send_banner(message)
    else:
        await message.answer(f"❌ چپتر {code} پیدا نشد!")

# ========================================
# ===== بررسی عضویت =====
# ========================================
@dp.callback_query(lambda c: c.data == "check_mem")
async def check_mem(call: types.CallbackQuery):
    try:
        with open("temp.json", "r") as f:
            data = json.load(f)
        code = data.get("code")
    except:
        await call.message.edit_text("❌ لینک نامعتبر!")
        return
    
    # چک کردن عضویت در همه کانال‌ها
    for ch in get_channels():
        try:
            member = await bot.get_chat_member(f"@{ch}", call.from_user.id)
            if member.status not in ["member", "administrator", "creator"]:
                await call.answer(f"❌ در کانال @{ch} عضو نشدی!", show_alert=True)
                return
        except:
            await call.answer(f"❌ خطا در بررسی کانال @{ch}!", show_alert=True)
            return
    
    await call.message.delete()
    await send_file_and_banner(call.message, code)

# ========================================
# ===== پنل ادمین (شیشه‌ای) =====
# ========================================
@dp.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ افزودن چپتر")],
            [types.KeyboardButton(text="📋 لیست چپترها")],
            [types.KeyboardButton(text="🗑 حذف چپتر")],
            [types.KeyboardButton(text="➕ افزودن کانال")],
            [types.KeyboardButton(text="📋 لیست کانال‌ها")],
            [types.KeyboardButton(text="➖ حذف کانال")],
            [types.KeyboardButton(text="📝 تنظیم بنر")],
            [types.KeyboardButton(text="🗑 حذف بنر")],
            [types.KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    await message.answer("⚙️ **پنل مدیریت**", reply_markup=keyboard)

# ========================================
# ===== بستن پنل =====
# ========================================
@dp.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())

# ========================================
# ===== افزودن چپتر =====
# ========================================
@dp.message(lambda m: m.text == "➕ افزودن چپتر" and m.from_user.id == ADMIN_ID)
async def add_file_start(message: types.Message):
    dp["state"] = "waiting_code"
    await message.answer("📝 کد چپتر رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_code")
async def get_code(message: types.Message):
    dp["code"] = message.text
    dp["state"] = "waiting_file"
    await message.answer("📄 حالا فایل رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and m.document and dp.get("state") == "waiting_file")
async def get_file(message: types.Message):
    code = dp.get("code")
    if not code:
        return
    file_type = "document"
    if message.document.mime_type == "application/pdf":
        file_type = "document"
    elif message.document.mime_type and message.document.mime_type.startswith("image"):
        file_type = "photo"
    elif message.document.mime_type and message.document.mime_type.startswith("video"):
        file_type = "video"
    save_file(code, message.document.file_id, file_type, message.caption or "")
    dp["state"] = None
    await message.answer(f"✅ چپتر {code} ذخیره شد!")

# ========================================
# ===== لیست چپترها =====
# ========================================
@dp.message(lambda m: m.text == "📋 لیست چپترها" and m.from_user.id == ADMIN_ID)
async def list_files(message: types.Message):
    files = get_all_files()
    if not files:
        await message.answer("❌ هیچ چپتری وجود نداره!")
        return
    text = "📋 لیست چپترها:\n" + "\n".join(f"• {f[0]} ({f[1]})" for f in files)
    await message.answer(text)

# ========================================
# ===== حذف چپتر =====
# ========================================
@dp.message(lambda m: m.text == "🗑 حذف چپتر" and m.from_user.id == ADMIN_ID)
async def delete_file_start(message: types.Message):
    dp["state"] = "waiting_delete"
    await message.answer("📝 کد چپتر رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_delete")
async def delete_file_confirm(message: types.Message):
    code = message.text
    if find_file(code):
        delete_file(code)
        await message.answer(f"✅ چپتر {code} حذف شد!")
    else:
        await message.answer(f"❌ چپتر {code} پیدا نشد!")
    dp["state"] = None

# ========================================
# ===== افزودن کانال =====
# ========================================
@dp.message(lambda m: m.text == "➕ افزودن کانال" and m.from_user.id == ADMIN_ID)
async def add_channel_start(message: types.Message):
    dp["state"] = "waiting_channel"
    await message.answer("📢 نام کانال رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_channel")
async def add_channel_confirm(message: types.Message):
    add_channel(message.text)
    dp["state"] = None
    await message.answer(f"✅ کانال @{message.text} اضافه شد!")

# ========================================
# ===== لیست کانال‌ها =====
# ========================================
@dp.message(lambda m: m.text == "📋 لیست کانال‌ها" and m.from_user.id == ADMIN_ID)
async def list_channels(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ هیچ کانالی وجود نداره!")
        return
    await message.answer("📋 لیست کانال‌ها:\n" + "\n".join(f"• @{ch}" for ch in channels))

# ========================================
# ===== حذف کانال =====
# ========================================
@dp.message(lambda m: m.text == "➖ حذف کانال" and m.from_user.id == ADMIN_ID)
async def delete_channel_start(message: types.Message):
    dp["state"] = "waiting_del_channel"
    await message.answer("📝 نام کانال رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_del_channel")
async def delete_channel_confirm(message: types.Message):
    delete_channel(message.text)
    dp["state"] = None
    await message.answer(f"✅ کانال @{message.text} حذف شد!")

# ========================================
# ===== تنظیم بنر =====
# ========================================
@dp.message(lambda m: m.text == "📝 تنظیم بنر" and m.from_user.id == ADMIN_ID)
async def set_banner_start(message: types.Message):
    dp["state"] = "waiting_banner"
    await message.answer(
        "📝 **بنر رو بفرست**\n\n"
        "می‌تونی اینا رو بفرستی:\n"
        "• متن\n"
        "• عکس\n"
        "• ویدیو\n"
        "• فایل"
    )

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_banner")
async def set_banner_confirm(message: types.Message):
    if message.text:
        set_banner("text", None, message.text)
        await message.answer(f"✅ بنر متنی ذخیره شد!")
    elif message.photo:
        set_banner("photo", message.photo[-1].file_id, message.caption or "")
        await message.answer("✅ بنر عکس ذخیره شد!")
    elif message.video:
        set_banner("video", message.video.file_id, message.caption or "")
        await message.answer("✅ بنر ویدیو ذخیره شد!")
    elif message.document:
        set_banner("document", message.document.file_id, message.caption or "")
        await message.answer("✅ بنر فایل ذخیره شد!")
    else:
        await message.answer("❌ نوع فایل پشتیبانی نمیشه!")
        return
    dp["state"] = None

# ========================================
# ===== حذف بنر =====
# ========================================
@dp.message(lambda m: m.text == "🗑 حذف بنر" and m.from_user.id == ADMIN_ID)
async def delete_banner_confirm(message: types.Message):
    delete_banner()
    await message.answer("✅ بنر حذف شد!")

# ========================================
# ===== اجرا =====
# ========================================
async def main():
    print("🤖 ربات روشن شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
