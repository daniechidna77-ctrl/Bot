import asyncio
import sqlite3
import json
import os
import shutil
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ========================================
# ===== مسیر دیتابیس (برای ریلیوی) =====
# ========================================
DB_PATH = os.environ.get("DB_PATH", "bot.db")
print(f"📁 مسیر دیتابیس: {DB_PATH}")

# ========================================
# ===== بکاپ خودکار =====
# ========================================
def backup_db():
    if os.path.exists(DB_PATH):
        shutil.copy(DB_PATH, f"{DB_PATH}.backup")
        print("✅ بکاپ گرفته شد!")

def restore_db():
    if os.path.exists(f"{DB_PATH}.backup"):
        shutil.copy(f"{DB_PATH}.backup", DB_PATH)
        print("✅ دیتابیس از بکاپ بازیابی شد!")
        return True
    return False

# ========================================
# ===== تنظیمات =====
# ========================================
TOKEN = "توکن_ربات_اینجا"  # ← اینجا توکن خودتو بذار
ADMIN_ID = 8255361263  # ← آیدی عددی خودت

# ========================================
# ===== دیتابیس =====
# ========================================
if not os.path.exists(DB_PATH):
    if not restore_db():
        print("📁 دیتابیس جدید ساخته شد!")

db = sqlite3.connect(DB_PATH)
c = db.cursor()

# ساخت جدول‌ها
c.execute("CREATE TABLE IF NOT EXISTS files (code TEXT PRIMARY KEY, file_id TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)")
c.execute("CREATE TABLE IF NOT EXISTS banner (text TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS reaction_post (link TEXT)")
db.commit()
backup_db()

# ========================================
# ===== توابع دیتابیس =====
# ========================================
def save_file(code, file_id):
    c.execute("INSERT OR REPLACE INTO files VALUES (?,?)", (code, file_id))
    db.commit()
    backup_db()

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
    backup_db()

def add_channel(username):
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()
    backup_db()

def get_channels():
    c.execute("SELECT username FROM channels")
    return [row[0] for row in c.fetchall()]

def delete_channel(username):
    c.execute("DELETE FROM channels WHERE username=?", (username,))
    db.commit()
    backup_db()

# ===== توابع بنر =====
def set_banner(text):
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?)", (text,))
    db.commit()
    backup_db()

def get_banner():
    c.execute("SELECT text FROM banner")
    row = c.fetchone()
    return row[0] if row else "📢 به ربات خوش اومدی!"

# ===== توابع ری اکشن =====
def set_reaction_post(link):
    c.execute("DELETE FROM reaction_post")
    c.execute("INSERT INTO reaction_post VALUES (?)", (link,))
    db.commit()
    backup_db()

def get_reaction_post():
    c.execute("SELECT link FROM reaction_post")
    row = c.fetchone()
    return row[0] if row else None

# ========================================
# ===== ربات =====
# ========================================
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========================================
# ===== کیبوردها =====
# ========================================
def join_keyboard():
    channels = get_channels()
    buttons = []
    for ch in channels:
        buttons.append([types.InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    buttons.append([types.InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def reaction_keyboard():
    link = get_reaction_post()
    if not link:
        return None
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👍 ری اکشن بزن", url=link)],
        [types.InlineKeyboardButton(text="✅ ری اکشن زدم", callback_data="reaction_done")]
    ])

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
    
    # مرحله ۱: عضویت اجباری
    if channels:
        with open("temp.json", "w") as f:
            json.dump({"code": code, "step": "membership"}, f)
        await message.answer(
            "🔒 **مرحله ۱: عضویت اجباری**\n\nلطفاً در کانال‌های زیر عضو شوید:",
            reply_markup=join_keyboard()
        )
        return
    
    await proceed_to_reaction(message, code)

# ========================================
# ===== ادامه مراحل =====
# ========================================
async def proceed_to_reaction(message, code):
    reaction_link = get_reaction_post()
    if reaction_link:
        with open("temp.json", "w") as f:
            json.dump({"code": code, "step": "reaction"}, f)
        await message.answer(
            "👍 **مرحله ۲: ری اکشن**\n\n"
            "لطفاً روی دکمه زیر کلیک کنید و به آخرین پست ما ری اکشن بزنید:",
            reply_markup=reaction_keyboard()
        )
        return
    
    await send_file_and_banner(message, code)

async def send_file_and_banner(message, code):
    file_id = find_file(code)
    banner = get_banner()
    
    if file_id:
        await message.answer_document(file_id, caption=f"📖 چپتر {code}")
        await message.answer(f"📢 {banner}")
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
    await proceed_to_reaction(call.message, code)

# ========================================
# ===== ری اکشن زدم =====
# ========================================
@dp.callback_query(lambda c: c.data == "reaction_done")
async def reaction_done(call: types.CallbackQuery):
    try:
        with open("temp.json", "r") as f:
            data = json.load(f)
        code = data.get("code")
    except:
        await call.message.edit_text("❌ لینک نامعتبر!")
        return
    
    await call.message.delete()
    await send_file_and_banner(call.message, code)

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
            [types.KeyboardButton(text="👍 تنظیم ری اکشن")],
            [types.KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    await message.answer("⚙️ پنل مدیریت:", reply_markup=keyboard)

# ========================================
# ===== تنظیم بنر =====
# ========================================
@dp.message(lambda m: m.text == "📝 تنظیم بنر" and m.from_user.id == ADMIN_ID)
async def set_banner_start(message: types.Message):
    dp["state"] = "waiting_banner"
    await message.answer("📝 متن بنر رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_banner")
async def set_banner_confirm(message: types.Message):
    set_banner(message.text)
    dp["state"] = None
    await message.answer(f"✅ بنر ذخیره شد!")

# ========================================
# ===== تنظیم ری اکشن =====
# ========================================
@dp.message(lambda m: m.text == "👍 تنظیم ری اکشن" and m.from_user.id == ADMIN_ID)
async def set_reaction_start(message: types.Message):
    dp["state"] = "waiting_reaction"
    await message.answer("📢 لینک پست رو برای ری اکشن بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_reaction")
async def set_reaction_confirm(message: types.Message):
    set_reaction_post(message.text)
    dp["state"] = None
    await message.answer(f"✅ لینک ری اکشن ذخیره شد!")

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
    save_file(dp["code"], message.document.file_id)
    dp["state"] = None
    await message.answer(f"✅ چپتر {dp['code']} ذخیره شد!")

# ========================================
# ===== لیست چپترها =====
# ========================================
@dp.message(lambda m: m.text == "📋 لیست چپترها" and m.from_user.id == ADMIN_ID)
async def list_files(message: types.Message):
    files = get_all_files()
    if not files:
        await message.answer("❌ هیچ چپتری وجود نداره!")
        return
    await message.answer("📋 لیست چپترها:\n" + "\n".join(f"• {f}" for f in files))

# ========================================
# ===== حذف چپتر =====
# ========================================
@dp.message(lambda m: m.text == "🗑 حذف چپتر" and m.from_user.id == ADMIN_ID)
async def delete_file_start(message: types.Message):
    dp["state"] = "waiting_delete"
    await message.answer("📝 کد چپتر رو بفرست:")

@dp.message(lambda m: m.from_user.id == ADMIN_ID and dp.get("state") == "waiting_delete")
async def delete_file_confirm(message: types.Message):
    delete_file(message.text)
    dp["state"] = None
    await message.answer(f"✅ چپتر {message.text} حذف شد!")

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
# ===== بستن پنل =====
# ========================================
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
