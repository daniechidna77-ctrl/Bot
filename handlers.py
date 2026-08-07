from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import find_file, get_channels, add_channel, delete_channel, get_banner, set_banner, save_file, get_all_files, delete_file

router = Router()
user_states = {}

# ===== کیبورد شیشه‌ای (پنل ادمین) =====
def admin_panel_keyboard():
    buttons = [
        [KeyboardButton(text="➕ افزودن چپتر")],
        [KeyboardButton(text="📋 لیست چپترها")],
        [KeyboardButton(text="🗑 حذف چپتر")],
        [KeyboardButton(text="➕ افزودن کانال")],
        [KeyboardButton(text="➖ حذف کانال")],
        [KeyboardButton(text="📋 لیست کانال‌ها")],
        [KeyboardButton(text="📝 تنظیم بنر")],
        [KeyboardButton(text="📊 آمار")],
        [KeyboardButton(text="🔙 بستن پنل")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ===== دکمه‌های عضویت (Inline) =====
def join_keyboard(channels):
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===== چک کردن عضویت =====
async def is_member(bot, user_id):
    channels = get_channels()
    if not channels:
        return True
    for ch in channels:
        try:
            member = await bot.get_chat_member(f"@{ch}", user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ===== استارت =====
@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    banner = get_banner()
    
    if len(args) == 1:
        await message.answer(f"👋 سلام!\n{banner}")
        return
    
    code = args[1]
    user_states[message.from_user.id] = {"code": code}
    
    if not await is_member(message.bot, message.from_user.id):
        channels = get_channels()
        await message.answer(
            "🔒 برای دریافت فایل، عضو کانال‌ها شو:",
            reply_markup=join_keyboard(channels)
        )
        return
    
    file_id = find_file(code)
    if file_id:
        await message.answer_document(file_id, caption=f"📖 {code}")
    else:
        await message.answer(f"❌ چپتر {code} پیدا نشد!")

# ===== بررسی عضویت =====
@router.callback_query(lambda c: c.data == "check_mem")
async def check_mem(call: types.CallbackQuery):
    state = user_states.get(call.from_user.id)
    if not state:
        await call.message.edit_text("❌ لینک نامعتبر!")
        return
    
    code = state.get("code")
    if not await is_member(call.bot, call.from_user.id):
        await call.answer("❌ هنوز عضو نشدی!", show_alert=True)
        return
    
    file_id = find_file(code)
    await call.message.delete()
    if file_id:
        await call.message.answer_document(file_id, caption=f"📖 {code}")
    else:
        await call.message.answer(f"❌ چپتر {code} پیدا نشد!")

# ===== پنل ادمین (شیشه‌ای) =====
@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ پنل مدیریت:", reply_markup=admin_panel_keyboard())

# ===== بستن پنل =====
@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())

# ===== افزودن چپتر =====
@router.message(lambda m: m.text == "➕ افزودن چپتر" and m.from_user.id == ADMIN_ID)
async def add_file_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_code"}
    await message.answer("📝 کد چپتر رو بفرست:\nمثال: 1_2")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_code")
async def get_code(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_pdf", "code": message.text.strip()}
    await message.answer("📄 حالا PDF رو ارسال کن")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document)
async def get_pdf(message: types.Message):
    state = user_states.get(message.from_user.id, {})
    if state.get("state") != "waiting_pdf":
        return
    code = state.get("code")
    if not code:
        return
    save_file(code, message.document.file_id)
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ چپتر {code} ذخیره شد!")

# ===== لیست چپترها =====
@router.message(lambda m: m.text == "📋 لیست چپترها" and m.from_user.id == ADMIN_ID)
async def list_files(message: types.Message):
    files = get_all_files()
    if not files:
        await message.answer("❌ هیچ چپتری ذخیره نشده!")
        return
    await message.answer("📋 لیست چپترها:\n" + "\n".join([f"• {f}" for f in files]))

# ===== حذف چپتر =====
@router.message(lambda m: m.text == "🗑 حذف چپتر" and m.from_user.id == ADMIN_ID)
async def delete_file_start(message: types.Message):
    files = get_all_files()
    if not files:
        await message.answer("❌ هیچ چپتری وجود نداره!")
        return
    user_states[message.from_user.id] = {"state": "waiting_delete"}
    await message.answer("📝 کد چپتر رو برای حذف بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete")
async def delete_file_confirm(message: types.Message):
    code = message.text.strip()
    if find_file(code):
        delete_file(code)
        await message.answer(f"✅ چپتر {code} حذف شد!")
    else:
        await message.answer(f"❌ چپتر {code} پیدا نشد!")
    user_states[message.from_user.id] = {}

# ===== افزودن کانال =====
@router.message(lambda m: m.text == "➕ افزودن کانال" and m.from_user.id == ADMIN_ID)
async def add_channel_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_channel"}
    await message.answer("📢 نام کاربری کانال رو بفرست (بدون @):")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_channel")
async def get_channel(message: types.Message):
    ch = message.text.strip().replace("@", "")
    add_channel(ch)
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ کانال @{ch} اضافه شد!")

# ===== حذف کانال =====
@router.message(lambda m: m.text == "➖ حذف کانال" and m.from_user.id == ADMIN_ID)
async def delete_channel_start(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی وجود نداره!")
        return
    user_states[message.from_user.id] = {"state": "waiting_del_channel"}
    await message.answer("📝 نام کاربری کانال رو برای حذف بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_del_channel")
async def delete_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")
    delete_channel(ch)
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ کانال @{ch} حذف شد!")

# ===== لیست کانال‌ها =====
@router.message(lambda m: m.text == "📋 لیست کانال‌ها" and m.from_user.id == ADMIN_ID)
async def list_channels(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی ثبت نشده!")
        return
    await message.answer("📋 لیست کانال‌ها:\n" + "\n".join([f"• @{ch}" for ch in channels]))

# ===== تنظیم بنر =====
@router.message(lambda m: m.text == "📝 تنظیم بنر" and m.from_user.id == ADMIN_ID)
async def set_banner_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_banner"}
    await message.answer("📝 متن بنر جدید رو بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner")
async def get_banner_text(message: types.Message):
    set_banner(message.text)
    user_states[message.from_user.id] = {}
    await message.answer("✅ بنر ذخیره شد!")

# ===== آمار =====
@router.message(lambda m: m.text == "📊 آمار" and m.from_user.id == ADMIN_ID)
async def stats(message: types.Message):
    files = get_all_files()
    channels = get_channels()
    await message.answer(f"📊 آمار ربات:\n\n📁 تعداد چپترها: {len(files)}\n📢 تعداد کانال‌ها: {len(channels)}")
