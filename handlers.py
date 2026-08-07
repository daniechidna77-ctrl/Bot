from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import find_file, get_channels, add_channel, delete_channel, get_banner, set_banner, save_file

router = Router()
user_chapters = {}

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

# ===== دکمه‌های عضویت =====
def join_keyboard(channels):
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===== استارت =====
@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    banner = get_banner()
    
    # استارت معمولی
    if len(args) == 1:
        await message.answer(f"👋 سلام!\n{banner}")
        return
    
    # استارت با کد چپتر
    code = args[1]
    user_chapters[message.from_user.id] = code
    
    if not await is_member(message.bot, message.from_user.id):
        channels = get_channels()
        await message.answer(
            "🔒 برای دریافت فایل، عضو کانال‌ها شو:",
            reply_markup=join_keyboard(channels)
        )
        return
    
    file_id = find_file(code)
    if file_id:
        await message.answer_document(file_id, caption=f"📖 چپتر {code}")
    else:
        await message.answer(f"❌ چپتر {code} پیدا نشد!")

# ===== بررسی عضویت =====
@router.callback_query(lambda c: c.data == "check_mem")
async def check_mem(call: types.CallbackQuery):
    code = user_chapters.get(call.from_user.id)
    if not code:
        await call.message.edit_text("❌ لینک نامعتبر!")
        return
    
    if not await is_member(call.bot, call.from_user.id):
        await call.answer("❌ هنوز عضو نشدی!", show_alert=True)
        return
    
    file_id = find_file(code)
    await call.message.delete()
    if file_id:
        await call.message.answer_document(file_id, caption=f"📖 چپتر {code}")
    else:
        await call.message.answer(f"❌ چپتر {code} پیدا نشد!")

# ===== پنل ادمین =====
@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن چپتر", callback_data="add_file")],
        [InlineKeyboardButton(text="➕ افزودن کانال", callback_data="add_ch")],
        [InlineKeyboardButton(text="➖ حذف کانال", callback_data="del_ch")],
        [InlineKeyboardButton(text="📝 تنظیم بنر", callback_data="set_banner")],
        [InlineKeyboardButton(text="📋 لیست کانال‌ها", callback_data="list_ch")]
    ])
    await message.answer("⚙️ پنل مدیریت:", reply_markup=keyboard)

# ===== افزودن چپتر =====
@router.callback_query(lambda c: c.data == "add_file")
async def add_file(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_chapters[call.from_user.id] = "waiting_code"
    await call.message.answer("📝 کد چپتر رو بفرست (مثال: 1_2)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text)
async def get_code(message: types.Message):
    if user_chapters.get(message.from_user.id) != "waiting_code":
        return
    user_chapters[message.from_user.id] = message.text.strip()
    await message.answer("📄 حالا PDF رو ارسال کن")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document)
async def get_pdf(message: types.Message):
    code = user_chapters.get(message.from_user.id)
    if not code or code == "waiting_code":
        return
    save_file(code, message.document.file_id)
    del user_chapters[message.from_user.id]
    await message.answer(f"✅ چپتر {code} ذخیره شد!")

# ===== افزودن کانال =====
@router.callback_query(lambda c: c.data == "add_ch")
async def add_ch(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_chapters[call.from_user.id] = "waiting_ch"
    await call.message.answer("📢 نام کاربری کانال رو بفرست (بدون @)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_chapters.get(m.from_user.id) == "waiting_ch")
async def get_ch(message: types.Message):
    add_channel(message.text.strip())
    del user_chapters[message.from_user.id]
    await message.answer(f"✅ کانال @{message.text} اضافه شد!")

# ===== حذف کانال =====
@router.callback_query(lambda c: c.data == "del_ch")
async def del_ch(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    channels = get_channels()
    if not channels:
        await call.message.answer("❌ کانالی وجود نداره!")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"❌ @{ch}", callback_data=f"del_{ch}")] for ch in channels
    ])
    await call.message.answer("🗑 کانال مورد نظر رو انتخاب کن:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("del_"))
async def confirm_del(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    ch = call.data[4:]
    delete_channel(ch)
    await call.message.edit_text(f"✅ کانال @{ch} حذف شد!")

# ===== لیست کانال‌ها =====
@router.callback_query(lambda c: c.data == "list_ch")
async def list_ch(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    channels = get_channels()
    if not channels:
        await call.message.answer("❌ کانالی ثبت نشده!")
        return
    text = "📋 لیست کانال‌ها:\n" + "\n".join([f"• @{ch}" for ch in channels])
    await call.message.answer(text)

# ===== تنظیم بنر =====
@router.callback_query(lambda c: c.data == "set_banner")
async def set_banner_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_chapters[call.from_user.id] = "waiting_banner"
    await call.message.answer("📝 متن بنر جدید رو بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_chapters.get(m.from_user.id) == "waiting_banner")
async def get_banner_text(message: types.Message):
    set_banner(message.text)
    del user_chapters[message.from_user.id]
    await message.answer("✅ بنر ذخیره شد!")
