import asyncio
import sqlite3
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ===== تنظیمات =====
TOKEN = "توکن_ربات_اینجا"
ADMIN_ID = 8255361263

# ===== مسیر دیتابیس =====
DB_PATH = os.environ.get("DB_PATH", "bot.db")

# ===== ساخت پوشه دیتابیس (اگه وجود نداشت) =====
db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)
    print(f"📁 پوشه {db_dir} ساخته شد!")

# ===== دیتابیس =====
db = sqlite3.connect(DB_PATH)
c = db.cursor()
c.execute("CREATE TABLE IF NOT EXISTS files (code TEXT PRIMARY KEY, file_id TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)")
c.execute("CREATE TABLE IF NOT EXISTS banner (text TEXT)")
db.commit()

def save_file(code, file_id):
    c.execute("INSERT OR REPLACE INTO files VALUES (?,?)", (code, file_id))
    db.commit()

def find_file(code):
    c.execute("SELECT file_id FROM files WHERE code=?", (code,))
    row = c.fetchone()
    return row[0] if row else None

def get_all_files():
    c.execute("SELECT code FROM files")
    return [row[0] for row in c.fetchall()]

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

def set_banner(text):
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?)", (text,))
    db.commit()

def get_banner():
    c.execute("SELECT text FROM banner")
    row = c.fetchone()
    return row[0] if row else "📢 به ربات خوش اومدی!"

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

# ========================================
# ===== استارت =====
# ========================================
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    
    if len(args) == 1:
        await message.answer("👋 سلام! برای دریافت چپتر از لینک مخصوص استفاده کن.")
        return
    
    code = args[1]
    channels = get_channels()
    
    if channels:
        with open("temp.json", "w") as f:
            json.dump({"code": code}, f)
        await message.answer(
            "🔒 **لطفاً عضو کانال‌ها شوید:**",
            reply_markup=join_keyboard()
        )
        return
    
    file_id = find_file(code)
    if file_id:
        await message.answer_document(file_id, caption=f"📖 چپتر {code}")
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
    
    for ch in get_channels():
        try:
            member = await bot.get_chat_member(f"@{ch}", call.from_user.id)
            if member.status not in ["member", "administrator", "creator"]:
                await call.answer("❌ هنوز عضو نشدی!", show_alert=True)
                return
        except:
            await call.answer("❌ خطا!", show_alert=True)
            return
    
    await call.message.delete()
    file_id = find_file(code)
    if file_id:
        await call.message.answer_document(file_id, caption=f"📖 چپتر {code}")
    else:
        await call.message.answer(f"❌ چپتر {code} پیدا نشد!")

# ========================================
# ===== پنل ادمین =====
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
            [types.KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    await message.answer("⚙️ پنل مدیریت:", reply_markup=keyboard)

# ===== افزودن چپتر =====
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
    save_file(dp["code"], message.document.file_id)
    dp["state"] = None
    await message.answer(f"✅ چپتر {dp['code']} ذخیره شد!")

# ===== لیست چپترها =====
@dp.message(lambda m: m.text == "📋 لیست چپترها" and m.from_user.id == ADMIN_ID)
async def list_files(message: types.Message):
    files = get_all_files()
    if not files:
        await message.answer("❌ هیچ چپتری وجود نداره!")
        return
    await message.answer("📋 لیست چپترها:\n" + "\n".join(f"• {f}" for f in files))

# ===== حذف چپتر =====
@dp.message(lambda m: m.text == "🗑 حذف چپتر" and m.from_user.id == ADMIN_ID)
async def delete_file_start(message: types.Message):
    dp["state"] = "waiting_delete"
    await message.answer("📝 کد چپتر رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_delete")
async def delete_file_confirm(message: types.Message):
    delete_file(message.text)
    dp["state"] = None
    await message.answer(f"✅ چپتر {message.text} حذف شد!")

# ===== افزودن کانال =====
@dp.message(lambda m: m.text == "➕ افزودن کانال" and m.from_user.id == ADMIN_ID)
async def add_channel_start(message: types.Message):
    dp["state"] = "waiting_channel"
    await message.answer("📢 نام کانال رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_channel")
async def add_channel_confirm(message: types.Message):
    add_channel(message.text)
    dp["state"] = None
    await message.answer(f"✅ کانال @{message.text} اضافه شد!")

# ===== لیست کانال‌ها =====
@dp.message(lambda m: m.text == "📋 لیست کانال‌ها" and m.from_user.id == ADMIN_ID)
async def list_channels(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ هیچ کانالی وجود نداره!")
        return
    await message.answer("📋 لیست کانال‌ها:\n" + "\n".join(f"• @{ch}" for ch in channels))

# ===== حذف کانال =====
@dp.message(lambda m: m.text == "➖ حذف کانال" and m.from_user.id == ADMIN_ID)
async def delete_channel_start(message: types.Message):
    dp["state"] = "waiting_del_channel"
    await message.answer("📝 نام کانال رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_del_channel")
async def delete_channel_confirm(message: types.Message):
    delete_channel(message.text)
    dp["state"] = None
    await message.answer(f"✅ کانال @{message.text} حذف شد!")

# ===== تنظیم بنر =====
@dp.message(lambda m: m.text == "📝 تنظیم بنر" and m.from_user.id == ADMIN_ID)
async def set_banner_start(message: types.Message):
    dp["state"] = "waiting_banner"
    await message.answer("📝 متن بنر رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_banner")
async def set_banner_confirm(message: types.Message):
    set_banner(message.text)
    dp["state"] = None
    await message.answer(f"✅ بنر ذخیره شد!")

# ===== بستن پنل =====
@dp.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())

# ========================================
# ===== اجرا =====
# ========================================
async def main():
    print("🤖 ربات روشن شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
