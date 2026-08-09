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
        [InlineKeyboardButton(text="🎨 تغییر تم", callback_data="change_theme")],
        [InlineKeyboardButton(text="📤 دعوت به ربات", callback_data="share_bot")]
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

# ===== ارسال فایل با دکمه اشتراک‌گذاری =====
async def send_file_with_share(message, file_id, file_type, code):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 اشتراک‌گذاری چپتر", callback_data=f"share_{code}")],
        [InlineKeyboardButton(text="📋 منو", callback_data="menu")]
    ])
    
    if file_type == "document":
        await message.answer_document(file_id, caption=f"📖 چپتر {code}", reply_markup=keyboard)
    elif file_type == "photo":
        await message.answer_photo(file_id, caption=f"📖 چپتر {code}", reply_markup=keyboard)
    elif file_type == "video":
        await message.answer_video(file_id, caption=f"📖 چپتر {code}", reply_markup=keyboard)
    else:
        await message.answer_document(file_id, caption=f"📖 چپتر {code}", reply_markup=keyboard)

# ===== استارت =====
@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    banner = get_banner()
    add_user(message.from_user.id)
    theme = get_user_theme(message.from_user.id)
    
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
        increment_download(code)
        await send_file_with_share(message, file_id, file_type, code)
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
        await send_file_with_share(call.message, file_id, file_type, code)
    else:
        await call.message.answer(f"❌ چپتر {code} پیدا نشد!")

# ===== عضویت در همه کانال‌ها =====
@router.callback_query(lambda c: c.data == "join_all")
async def join_all(call: types.CallbackQuery):
    channels = get_channels()
    if not channels:
        await call.answer("❌ کانالی وجود نداره!", show_alert=True)
        return
    
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

# ===== اشتراک‌گذاری چپتر =====
@router.callback_query(lambda c: c.data.startswith("share_") and not c.data == "share_bot")
async def share_chapter(call: types.CallbackQuery):
    code = call.data.split("_")[1]
    bot_username = (await call.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={code}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 اشتراک‌گذاری در تلگرام", url=f"https://t.me/share/url?url={share_link}&text=📖 چپتر {code} رو دریافت کن!")],
        [InlineKeyboardButton(text="📋 کپی لینک", callback_data=f"copy_{code}")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_menu")]
    ])
    
    await call.message.edit_text(
        f"📤 لینک اشتراک‌گذاری چپتر {code}:\n\n"
        f"`{share_link}`\n\n"
        f"این لینک رو برای دوستانت بفرست تا چپتر رو دریافت کنن.",
        reply_markup=keyboard
    )

# ===== کپی لینک چپتر =====
@router.callback_query(lambda c: c.data.startswith("copy_"))
async def copy_link(call: types.CallbackQuery):
    code = call.data.split("_")[1]
    bot_username = (await call.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={code}"
    
    await call.answer(f"✅ لینک کپی شد!", show_alert=True)
    await call.message.edit_text(
        f"📤 لینک چپتر {code}:\n\n"
        f"`{share_link}`\n\n"
        f"لینک رو کپی کن و برای دوستانت بفرست.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"share_{code}")]
        ])
    )

# ===== دعوت به ربات =====
@router.callback_query(lambda c: c.data == "share_bot")
async def share_bot(call: types.CallbackQuery):
    bot_username = (await call.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 دعوت به ربات", url=f"https://t.me/share/url?url={share_link}&text=🤖 به این ربات بپیوند!")],
        [InlineKeyboardButton(text="📋 کپی لینک", callback_data="copy_bot_link")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu")]
    ])
    
    await call.message.edit_text(
        f"🤖 لینک ربات:\n\n"
        f"`{share_link}`\n\n"
        f"دوستانت رو به ربات دعوت کن!",
        reply_markup=keyboard
    )

# ===== کپی لینک ربات =====
@router.callback_query(lambda c: c.data == "copy_bot_link")
async def copy_bot_link(call: types.CallbackQuery):
    bot_username = (await call.bot.get_me()).username
    await call.answer(f"✅ لینک ربات کپی شد!", show_alert=True)

# ===== دکمه برگشت به منو =====
@router.callback_query(lambda c: c.data == "back_menu" or c.data == "menu")
async def back_menu(call: types.CallbackQuery):
    await call.message.edit_text("📋 منوی اصلی:", reply_markup=user_menu_keyboard())
