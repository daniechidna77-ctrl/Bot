from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import *
import asyncio

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
        [KeyboardButton(text="🗑 حذف بنر")],
        [KeyboardButton(text="📊 آمار")],
        [KeyboardButton(text="📢 ارسال همگانی")],
        [KeyboardButton(text="💬 نظرات")],
        [KeyboardButton(text="❓ سوالات")],
        [KeyboardButton(text="🎨 تغییر تم")],
        [KeyboardButton(text="🔙 بستن پنل")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ===== دکمه‌های عضویت (Inline) =====
def join_keyboard(channels):
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}")])
    # دکمه عضویت در همه کانال‌ها
    if len(channels) > 1:
        buttons.append([InlineKeyboardButton(text="🔗 عضویت در همه کانال‌ها", callback_data="join_all")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===== منوی کاربر =====
def user_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 راهنما", callback_data="help")],
        [InlineKeyboardButton(text="📢 کانال‌ها", callback_data="channels_list")],
        [InlineKeyboardButton(text="👤 پروفایل", callback_data="profile")],
        [InlineKeyboardButton(text="💬 نظر یا پیشنهاد", callback_data="feedback")],
        [InlineKeyboardButton(text="❓ سوال", callback_data="ask_question")],
        [InlineKeyboardButton(text="🎨 تغییر تم", callback_data="change_theme")]
    ])
    return keyboard

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
    add_user(message.from_user.id)  # ذخیره کاربر
    
    if len(args) == 1:
        await message.answer(
            f"👋 سلام {message.from_user.first_name}!\n{banner}",
            reply_markup=user_menu_keyboard()
        )
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
    
    file_info = find_file(code)
    if file_info:
        file_id, file_type = file_info
        increment_download(code)  # افزایش تعداد دانلود
        
        if file_type == "document":
            await message.answer_document(file_id, caption=f"📖 {code}")
        elif file_type == "photo":
            await message.answer_photo(file_id, caption=f"📖 {code}")
        elif file_type == "video":
            await message.answer_video(file_id, caption=f"📖 {code}")
        else:
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
    
    file_info = find_file(code)
    await call.message.delete()
    if file_info:
        file_id, file_type = file_info
        increment_download(code)
        
        if file_type == "document":
            await call.message.answer_document(file_id, caption=f"📖 {code}")
        elif file_type == "photo":
            await call.message.answer_photo(file_id, caption=f"📖 {code}")
        elif file_type == "video":
            await call.message.answer_video(file_id, caption=f"📖 {code}")
        else:
            await call.message.answer_document(file_id, caption=f"📖 {code}")
    else:
        await call.message.answer(f"❌ چپتر {code} پیدا نشد!")

# ===== عضویت در همه کانال‌ها =====
@router.callback_query(lambda c: c.data == "join_all")
async def join_all(call: types.CallbackQuery):
    channels = get_channels()
    if not channels:
        await call.answer("❌ کانالی وجود نداره!", show_alert=True)
        return
    
    # ساخت لینک‌های عضویت
    links = "\n".join([f"• @{ch}" for ch in channels])
    await call.message.edit_text(
        f"🔗 برای عضویت در همه کانال‌ها روی لینک‌ها کلیک کن:\n\n{links}\n\n✅ بعد از عضویت، روی «عضو شدم» کلیک کن."
    )

# ===== منوی کاربر =====
@router.message(Command("menu"))
async def menu(message: types.Message):
    await message.answer("📋 منوی اصلی:", reply_markup=user_menu_keyboard())

# ===== راهنما =====
@router.callback_query(lambda c: c.data == "help")
async def help_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "📖 راهنما:\n\n"
        "برای دریافت چپتر از لینک مخصوص استفاده کن.\n"
        "مثال: https://t.me/Yuri199bot?start=1_2\n\n"
        "🔹 بعد از عضویت در کانال‌ها، فایل برات ارسال میشه.\n"
        "🔹 می‌تونی از منو برای دسترسی به بخش‌های مختلف استفاده کنی."
    )

# ===== لیست کانال‌ها =====
@router.callback_query(lambda c: c.data == "channels_list")
async def channels_list_menu(call: types.CallbackQuery):
    channels = get_channels()
    if not channels:
        await call.message.edit_text("❌ کانالی ثبت نشده!")
        return
    text = "📢 لیست کانال‌ها:\n" + "\n".join([f"• @{ch}" for ch in channels])
    await call.message.edit_text(text)

# ===== پروفایل =====
@router.callback_query(lambda c: c.data == "profile")
async def profile_menu(call: types.CallbackQuery):
    theme = get_user_theme(call.from_user.id)
    await call.message.edit_text(
        f"👤 پروفایل:\n\n"
        f"آیدی: {call.from_user.id}\n"
        f"نام: {call.from_user.full_name}\n"
        f"تم: {'🌙 شب' if theme == 'dark' else '☀️ روز'}"
    )

# ===== نظر یا پیشنهاد =====
@router.callback_query(lambda c: c.data == "feedback")
async def feedback_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_feedback"}
    await call.message.edit_text("💬 نظر یا پیشنهادت رو بفرست:")

@router.message(lambda m: m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_feedback")
async def get_feedback(message: types.Message):
    add_feedback(message.from_user.id, message.text)
    user_states[message.from_user.id] = {}
    await message.answer("✅ نظرت با موفقیت ثبت شد! ممنون 🙏")

# ===== سوال =====
@router.callback_query(lambda c: c.data == "ask_question")
async def ask_question_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_question"}
    await call.message.edit_text("❓ سوالت رو بفرست:")

@router.message(lambda m: m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_question")
async def get_question(message: types.Message):
    add_question(message.from_user.id, message.text)
    user_states[message.from_user.id] = {}
    await message.answer("✅ سوال شما ثبت شد! به زودی پاسخ داده میشه.")

# ===== تغییر تم =====
@router.callback_query(lambda c: c.data == "change_theme")
async def change_theme_start(call: types.CallbackQuery):
    current_theme = get_user_theme(call.from_user.id)
    new_theme = "dark" if current_theme == "light" else "light"
    set_user_theme(call.from_user.id, new_theme)
    emoji = "🌙" if new_theme == "dark" else "☀️"
    await call.message.edit_text(f"✅ تم به {emoji} {'شب' if new_theme == 'dark' else 'روز'} تغییر کرد!")

# ===== پنل ادمین (ادامه در فایل بعدی) =====
# ... (ادمین پنل در فایل admin_panel.py جداگانه)
