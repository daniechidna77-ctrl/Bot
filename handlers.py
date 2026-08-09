from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import *
import asyncio

router = Router()
user_states = {}

# ===== کیبورد شیشه‌ای منو (برای کاربر) =====
def user_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📖 راهنما")],
            [KeyboardButton(text="📢 کانال‌ها")],
            [KeyboardButton(text="👤 پروفایل")],
            [KeyboardButton(text="💬 نظر یا پیشنهاد")],
            [KeyboardButton(text="❓ سوال")],
            [KeyboardButton(text="📤 دعوت به ربات")]
        ],
        resize_keyboard=True
    )
    return keyboard

# ===== دکمه‌های عضویت (اینلاین) - بدون "عضویت در همه" =====
def join_keyboard(channels, post_link=None):
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    # ===== "عضویت در همه" حذف شد =====
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    
    if post_link:
        buttons.append([InlineKeyboardButton(text="👍 ری اکشن بزن", url=post_link)])
    
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

# ===== ارسال فایل با اشتراک‌گذاری =====
async def send_file_with_share(message, file_id, file_type, code, caption=""):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 اشتراک‌گذاری", callback_data=f"share_{code}")],
        [InlineKeyboardButton(text="📋 منو", callback_data="menu")]
    ])
    
    final_caption = f"📖 **چپتر {code}**\n"
    if caption:
        final_caption += f"\n{caption}"
    
    if file_type == "document":
        await message.answer_document(file_id, caption=final_caption, reply_markup=keyboard)
    elif file_type == "photo":
        await message.answer_photo(file_id, caption=final_caption, reply_markup=keyboard)
    elif file_type == "video":
        await message.answer_video(file_id, caption=final_caption, reply_markup=keyboard)
    else:
        await message.answer_document(file_id, caption=final_caption, reply_markup=keyboard)

# ========================================
# ===== اشتراک‌گذاری =====
# ========================================

@router.callback_query(lambda c: c.data and c.data.startswith("share_"))
async def share_chapter(call: types.CallbackQuery):
    code = call.data.replace("share_", "")
    bot_username = (await call.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={code}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 اشتراک‌گذاری در تلگرام", url=f"https://t.me/share/url?url={share_link}&text=📖 چپتر {code} رو دریافت کن!")],
        [InlineKeyboardButton(text="📋 کپی لینک", callback_data=f"copy_{code}")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_file")]
    ])
    
    await call.message.edit_text(
        f"📤 **لینک اشتراک‌گذاری چپتر {code}:**\n\n"
        f"`{share_link}`\n\n"
        f"این لینک رو برای دوستانت بفرست! 😊",
        reply_markup=keyboard
    )
    
    await call.answer("✅ لینک ساخته شد!")

# ===== کپی لینک =====
@router.callback_query(lambda c: c.data and c.data.startswith("copy_"))
async def copy_link(call: types.CallbackQuery):
    code = call.data.replace("copy_", "")
    bot_username = (await call.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={code}"
    
    await call.answer(f"✅ لینک کپی شد!", show_alert=True)
    
    await call.message.edit_text(
        f"📤 **لینک چپتر {code}:**\n\n"
        f"`{share_link}`\n\n"
        f"لینک رو کپی کن و برای دوستانت بفرست.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"share_{code}")]
        ])
    )

# ===== برگشت به فایل =====
@router.callback_query(lambda c: c.data == "back_to_file")
async def back_to_file(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer("✅ برگشتی به منو!\nبرای دریافت فایل دوباره لینک رو بزن.")

# ========================================
# ===== استارت =====
# ========================================

@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    banner = get_banner()
    add_user(message.from_user.id)
    post_link = get_reaction_post()
    
    if len(args) == 1:
        await message.answer(
            f"👋 **سلام {message.from_user.first_name}!**\n\n"
            f"{banner}\n\n"
            f"😊 خوش اومدی! از منو استفاده کن.",
            reply_markup=user_menu_keyboard()
        )
        return
    
    code = args[1]
    user_states[message.from_user.id] = {"code": code}
    
    channels = get_channels()
    if channels:
        if not await is_member(message.bot, message.from_user.id):
            await message.answer(
                "🔒 **اول عضو کانال‌ها شو!** 😊\n\n"
                "برای دریافت فایل، باید تو این کانال‌ها عضو بشی:",
                reply_markup=join_keyboard(channels, post_link)
            )
            return
    
    file_info = find_file(code)
    if file_info:
        file_id, file_type, caption = file_info
        increment_download(code)
        await send_file_with_share(message, file_id, file_type, code, caption or "")
    else:
        await message.answer(f"❌ **چپتر {code} پیدا نشد!** 😅")

# ========================================
# ===== بررسی عضویت =====
# ========================================

@router.callback_query(lambda c: c.data == "check_mem")
async def check_mem(call: types.CallbackQuery):
    state = user_states.get(call.from_user.id)
    if not state:
        await call.message.edit_text("❌ لینک نامعتبر! 😅")
        return
    
    code = state.get("code")
    if not await is_member(call.bot, call.from_user.id):
        await call.answer("❌ هنوز عضو نشدی! برو عضو شو 😊", show_alert=True)
        return
    
    file_info = find_file(code)
    await call.message.delete()
    if file_info:
        file_id, file_type, caption = file_info
        increment_download(code)
        await send_file_with_share(call.message, file_id, file_type, code, caption or "")
    else:
        await call.message.answer(f"❌ چپتر {code} پیدا نشد! 😅")

# ========================================
# ===== منوی کاربر =====
# ========================================

@router.message(Command("menu"))
async def menu(message: types.Message):
    await message.answer(
        "📋 **منوی اصلی:**\n\n"
        "😊 هر چی نیاز داری، اینجاست!",
        reply_markup=user_menu_keyboard()
    )

# ========================================
# ===== راهنما =====
# ========================================

@router.message(lambda m: m.text == "📖 راهنما")
async def help_menu(message: types.Message):
    await message.answer(
        "📖 **راهنما:**\n\n"
        "🔹 برای دریافت چپتر از لینک مخصوص استفاده کن:\n"
        "`https://t.me/Yuri199bot?start=1_2`\n\n"
        "🔹 اول عضو کانال‌ها شو، بعد فایل میاد!\n"
        "🔹 اگه سوالی داری، از منو بپرس 😊"
    )

# ========================================
# ===== لیست کانال‌ها =====
# ========================================

@router.message(lambda m: m.text == "📢 کانال‌ها")
async def channels_list_menu(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی ثبت نشده! 😅")
        return
    text = "📢 **لیست کانال‌ها:**\n\n" + "\n".join([f"• @{ch}" for ch in channels])
    await message.answer(text)

# ========================================
# ===== پروفایل =====
# ========================================

@router.message(lambda m: m.text == "👤 پروفایل")
async def profile_menu(message: types.Message):
    await message.answer(
        f"👤 **پروفایل:**\n\n"
        f"🆔 آیدی: `{message.from_user.id}`\n"
        f"📛 نام: {message.from_user.full_name}"
    )

# ========================================
# ===== نظر یا پیشنهاد =====
# ========================================

@router.message(lambda m: m.text == "💬 نظر یا پیشنهاد")
async def feedback_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_feedback"}
    await message.answer("💬 **نظر یا پیشنهادت رو بفرست:**\n\n(هر چی دوست داری بگو، خوشحال میشم بشنوم 😊)")

@router.message(lambda m: m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_feedback")
async def get_feedback(message: types.Message):
    add_feedback(message.from_user.id, message.text)
    clear_user_state(message.from_user.id)
    await message.answer("✅ **نظرت ثبت شد!** 🙏\n\nممنون که کمک میکنی بهتر بشم 😊")

# ========================================
# ===== سوال =====
# ========================================

@router.message(lambda m: m.text == "❓ سوال")
async def ask_question_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_question"}
    await message.answer("❓ **سوالت رو بفرست:**\n\n(هر چی هست بپرس، جواب میدم 😊)")

@router.message(lambda m: m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_question")
async def get_question(message: types.Message):
    add_question(message.from_user.id, message.text)
    clear_user_state(message.from_user.id)
    await message.answer("✅ **سوال شما ثبت شد!** 📝\n\nبه زودی جواب میدم 😊")

# ========================================
# ===== دعوت به ربات =====
# ========================================

@router.message(lambda m: m.text == "📤 دعوت به ربات")
async def share_bot(message: types.Message):
    bot_username = (await message.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 دعوت", url=f"https://t.me/share/url?url={share_link}&text=🤖 به این ربات بپیوند!")],
        [InlineKeyboardButton(text="📋 کپی لینک", callback_data="copy_bot_link")]
    ])
    
    await message.answer(
        f"🤖 **لینک ربات:**\n\n"
        f"`{share_link}`\n\n"
        f"دوستانت رو دعوت کن! 😊",
        reply_markup=keyboard
    )

# ========================================
# ===== کپی لینک ربات =====
# ========================================

@router.callback_query(lambda c: c.data == "copy_bot_link")
async def copy_bot_link(call: types.CallbackQuery):
    await call.answer(f"✅ لینک کپی شد!", show_alert=True)

# ========================================
# ===== برگشت به منو (از اینلاین) =====
# ========================================

@router.callback_query(lambda c: c.data == "menu")
async def back_menu(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        "📋 **منوی اصلی:**\n\n"
        "😊 هر چی نیاز داری، اینجاست!",
        reply_markup=user_menu_keyboard()
    )

# ========================================
# ===== پاک کردن حالت کاربر =====
# ========================================

def clear_user_state(user_id):
    if user_id in user_states:
        del user_states[user_id]
