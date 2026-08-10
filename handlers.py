from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import *
import asyncio

router = Router()
user_states = {}

# ===== کیبورد شیشه‌ای منو =====
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

# ===== دکمه‌های عضویت =====
def join_keyboard(channels, post_link=None):
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
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

# ===== نمایش بنر =====
async def send_banner(message, banner_data):
    banner_type = banner_data.get("type", "text")
    file_id = banner_data.get("file_id")
    text = banner_data.get("text", "")
    
    if banner_type == "photo" and file_id:
        await message.answer_photo(file_id, caption=text)
    elif banner_type == "video" and file_id:
        await message.answer_video(file_id, caption=text)
    else:
        await message.answer(text)

# ===== ارسال فایل =====
async def send_file_only(message, file_id, file_type, caption=""):
    final_caption = caption if caption else ""
    
    if file_type == "document":
        await message.answer_document(file_id, caption=final_caption)
    elif file_type == "photo":
        await message.answer_photo(file_id, caption=final_caption)
    elif file_type == "video":
        await message.answer_video(file_id, caption=final_caption)
    else:
        await message.answer_document(file_id, caption=final_caption)

# ========================================
# ===== استارت (با ترتیب درست) =====
# ========================================

@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    banner_data = get_active_banner()
    add_user(message.from_user.id)
    post_link = get_reaction_post()
    
    # استارت معمولی (بدون کد)
    if len(args) == 1:
        await send_banner(message, banner_data)
        await message.answer(
            f"👋 **سلام {message.from_user.first_name}!**\n\n"
            f"😊 خوش اومدی! از منو استفاده کن.",
            reply_markup=user_menu_keyboard()
        )
        return
    
    # استارت با کد چپتر
    code = args[1]
    user_states[message.from_user.id] = {"code": code}
    
    # ===== مرحله ۱: عضویت اجباری =====
    channels = get_channels()
    if channels:
        if not await is_member(message.bot, message.from_user.id):
            await message.answer(
                "🔒 **مرحله ۱: عضویت اجباری**\n\n"
                "برای دریافت فایل، باید در کانال‌های زیر عضو شوید:",
                reply_markup=join_keyboard(channels, post_link)
            )
            return
    
    # ===== مرحله ۲: ری اکشن پست (اگه تنظیم شده باشه) =====
    if post_link:
        await message.answer(
            "👍 **مرحله ۲: ری اکشن پست**\n\n"
            f"روی لینک زیر کلیک کنید و ری اکشن بزنید:\n"
            f"{post_link}\n\n"
            "✅ بعد از ری اکشن، فایل ارسال میشود."
        )
        # صبر برای ری اکشن (کاربر باید خودش بزنه)
        # فعلاً ادامه میدیم چون ری اکشن رو خود کاربر باید بزنه
    
    # ===== مرحله ۳: دریافت فایل =====
    file_info = find_file(code)
    if file_info:
        file_id, file_type, caption = file_info
        increment_download(code)
        
        # ===== مرحله ۴: بنر پایین فایل =====
        await send_banner(message, banner_data)
        await send_file_only(message, file_id, file_type, caption or "")
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
    
    # چک کردن عضویت
    if not await is_member(call.bot, call.from_user.id):
        await call.answer("❌ هنوز عضو نشدی! برو عضو شو 😊", show_alert=True)
        return
    
    # حذف پیام عضویت
    await call.message.delete()
    
    # ===== ادامه مراحل =====
    post_link = get_reaction_post()
    
    # مرحله ۲: ری اکشن
    if post_link:
        await call.message.answer(
            "👍 **مرحله ۲: ری اکشن پست**\n\n"
            f"روی لینک زیر کلیک کنید و ری اکشن بزنید:\n"
            f"{post_link}\n\n"
            "✅ بعد از ری اکشن، فایل ارسال میشود."
        )
    
    # مرحله ۳: فایل
    file_info = find_file(code)
    if file_info:
        file_id, file_type, caption = file_info
        increment_download(code)
        
        # مرحله ۴: بنر + فایل
        banner_data = get_active_banner()
        await send_banner(call.message, banner_data)
        await send_file_only(call.message, file_id, file_type, caption or "")
    else:
        await call.message.answer(f"❌ **چپتر {code} پیدا نشد!** 😅")

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
# ===== پاک کردن حالت کاربر =====
# ========================================

def clear_user_state(user_id):
    if user_id in user_states:
        del user_states[user_id]
