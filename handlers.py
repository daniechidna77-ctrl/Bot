from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
import asyncio

router = Router()
user_states = {}

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

# ===== دکمه‌های عضویت =====
def join_keyboard(channels):
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}")])
    if len(channels) > 1:
        buttons.append([InlineKeyboardButton(text="🔗 عضویت در همه", callback_data="join_all")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===== دکمه‌های امتیازدهی =====
def rating_keyboard(code):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐", callback_data=f"rate_{code}_1"),
         InlineKeyboardButton(text="⭐⭐", callback_data=f"rate_{code}_2"),
         InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rate_{code}_3"),
         InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rate_{code}_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rate_{code}_5")]
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

# ===== ارسال فایل با امتیازدهی =====
async def send_file_with_share(message, file_id, file_type, code, caption=""):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 اشتراک‌گذاری", callback_data=f"share_{code}")],
        [InlineKeyboardButton(text="⭐ امتیاز بده", callback_data=f"show_rating_{code}")],
        [InlineKeyboardButton(text="📋 منو", callback_data="menu")]
    ])
    
    final_caption = f"📖 **چپتر {code}**\n"
    if caption:
        final_caption += f"\n{caption}"
    final_caption += f"\n\n⭐ به این چپتر امتیاز بده!"
    
    if file_type == "document":
        await message.answer_document(file_id, caption=final_caption, reply_markup=keyboard)
    elif file_type == "photo":
        await message.answer_photo(file_id, caption=final_caption, reply_markup=keyboard)
    elif file_type == "video":
        await message.answer_video(file_id, caption=final_caption, reply_markup=keyboard)
    else:
        await message.answer_document(file_id, caption=final_caption, reply_markup=keyboard)

# ===== نمایش امتیازدهی =====
@router.callback_query(lambda c: c.data.startswith("show_rating_"))
async def show_rating(call: types.CallbackQuery):
    code = call.data.split("_")[2]
    await call.message.edit_reply_markup(reply_markup=rating_keyboard(code))
    await call.answer("⭐ امتیاز بده!", show_alert=False)

# ===== دریافت امتیاز =====
@router.callback_query(lambda c: c.data.startswith("rate_"))
async def get_rating(call: types.CallbackQuery):
    _, code, rating = call.data.split("_")
    rating = int(rating)
    
    # ذخیره امتیاز در دیتابیس
    save_rating(code, call.from_user.id, rating)
    
    emojis = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"✅ **امتیاز شما ثبت شد!**\n{emojis[rating-1]}")
    await call.answer(f"امتیاز {rating} ثبت شد!", show_alert=False)

# ===== استارت =====
@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    banner = get_banner()
    add_user(message.from_user.id)
    
    if len(args) == 1:
        await message.answer(
            f"👋 **سلام {message.from_user.first_name}!**\n\n"
            f"{banner}\n\n"
            f"😊 خوش اومدی!",
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
                reply_markup=join_keyboard(channels)
            )
            return
    
    file_info = find_file(code)
    if file_info:
        file_id, file_type, caption = file_info
        increment_download(code)
        await send_file_with_share(message, file_id, file_type, code, caption or "")
    else:
        await message.answer(f"❌ **چپتر {code} پیدا نشد!** 😅")

# ===== بررسی عضویت =====
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

# ===== عضویت در همه =====
@router.callback_query(lambda c: c.data == "join_all")
async def join_all(call: types.CallbackQuery):
    channels = get_channels()
    if not channels:
        await call.answer("❌ کانالی وجود نداره!", show_alert=True)
        return
    links = "\n".join([f"• @{ch}" for ch in channels])
    await call.message.edit_text(
        f"🔗 **برای عضویت در همه کانال‌ها:**\n\n"
        f"{links}\n\n"
        f"✅ بعد از عضویت، بزن **عضو شدم**!"
    )

# ===== منوی کاربر =====
@router.message(Command("menu"))
async def menu(message: types.Message):
    await message.answer(
        "📋 **منوی اصلی:**\n\n"
        "😊 هر چی نیاز داری، اینجاست!",
        reply_markup=user_menu_keyboard()
    )

# ===== راهنما =====
@router.callback_query(lambda c: c.data == "help")
async def help_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "📖 **راهنما:**\n\n"
        "🔹 برای دریافت چپتر از لینک مخصوص استفاده کن:\n"
        "`https://t.me/Yuri199bot?start=1_2`\n\n"
        "🔹 اول عضو کانال‌ها شو، بعد فایل میاد!\n"
        "🔹 اگه سوالی داری، از منو بپرس 😊"
    )

# ===== لیست کانال‌ها =====
@router.callback_query(lambda c: c.data == "channels_list")
async def channels_list_menu(call: types.CallbackQuery):
    channels = get_channels()
    if not channels:
        await call.message.edit_text("❌ کانالی ثبت نشده! 😅")
        return
    text = "📢 **لیست کانال‌ها:**\n\n" + "\n".join([f"• @{ch}" for ch in channels])
    await call.message.edit_text(text)

# ===== پروفایل =====
@router.callback_query(lambda c: c.data == "profile")
async def profile_menu(call: types.CallbackQuery):
    theme = get_user_theme(call.from_user.id)
    await call.message.edit_text(
        f"👤 **پروفایل:**\n\n"
        f"🆔 آیدی: `{call.from_user.id}`\n"
        f"📛 نام: {call.from_user.full_name}\n"
        f"🎨 تم: {'🌙 شب' if theme == 'dark' else '☀️ روز'}"
    )

# ===== نظر یا پیشنهاد =====
@router.callback_query(lambda c: c.data == "feedback")
async def feedback_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_feedback"}
    await call.message.edit_text("💬 **نظر یا پیشنهادت رو بفرست:**\n\n(هر چی دوست داری بگو، خوشحال میشم بشنوم 😊)")

@router.message(lambda m: m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_feedback")
async def get_feedback(message: types.Message):
    add_feedback(message.from_user.id, message.text)
    user_states[message.from_user.id] = {}
    await message.answer("✅ **نظرت ثبت شد!** 🙏\n\nممنون که کمک میکنی بهتر بشم 😊")

# ===== سوال =====
@router.callback_query(lambda c: c.data == "ask_question")
async def ask_question_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_question"}
    await call.message.edit_text("❓ **سوالت رو بفرست:**\n\n(هر چی هست بپرس، جواب میدم 😊)")

@router.message(lambda m: m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_question")
async def get_question(message: types.Message):
    add_question(message.from_user.id, message.text)
    user_states[message.from_user.id] = {}
    await message.answer("✅ **سوال شما ثبت شد!** 📝\n\nبه زودی جواب میدم 😊")

# ===== تغییر تم =====
@router.callback_query(lambda c: c.data == "change_theme")
async def change_theme_start(call: types.CallbackQuery):
    current_theme = get_user_theme(call.from_user.id)
    new_theme = "dark" if current_theme == "light" else "light"
    set_user_theme(call.from_user.id, new_theme)
    emoji = "🌙" if new_theme == "dark" else "☀️"
    await call.message.edit_text(f"✅ **تم به {emoji} {'شب' if new_theme == 'dark' else 'روز'} تغییر کرد!**")

# ===== اشتراک‌گذاری =====
@router.callback_query(lambda c: c.data.startswith("share_") and c.data != "share_bot")
async def share_chapter(call: types.CallbackQuery):
    code = call.data.split("_")[1]
    bot_username = (await call.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={code}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 اشتراک‌گذاری", url=f"https://t.me/share/url?url={share_link}&text=📖 چپتر {code} رو دریافت کن!")],
        [InlineKeyboardButton(text="📋 کپی لینک", callback_data=f"copy_{code}")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu")]
    ])
    
    await call.message.edit_text(
        f"📤 **لینک اشتراک‌گذاری چپتر {code}:**\n\n"
        f"`{share_link}`\n\n"
        f"این لینک رو برای دوستانت بفرست! 😊",
        reply_markup=keyboard
    )

# ===== کپی لینک =====
@router.callback_query(lambda c: c.data.startswith("copy_"))
async def copy_link(call: types.CallbackQuery):
    code = call.data.split("_")[1]
    bot_username = (await call.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={code}"
    
    await call.answer(f"✅ لینک کپی شد!", show_alert=True)
    await call.message.edit_text(
        f"📤 **لینک چپتر {code}:**\n\n"
        f"`{share_link}`",
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
        [InlineKeyboardButton(text="📤 دعوت", url=f"https://t.me/share/url?url={share_link}&text=🤖 به این ربات بپیوند!")],
        [InlineKeyboardButton(text="📋 کپی لینک", callback_data="copy_bot_link")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu")]
    ])
    
    await call.message.edit_text(
        f"🤖 **لینک ربات:**\n\n"
        f"`{share_link}`\n\n"
        f"دوستانت رو دعوت کن! 😊",
        reply_markup=keyboard
    )

# ===== کپی لینک ربات =====
@router.callback_query(lambda c: c.data == "copy_bot_link")
async def copy_bot_link(call: types.CallbackQuery):
    await call.answer(f"✅ لینک کپی شد!", show_alert=True)

# ===== برگشت به منو =====
@router.callback_query(lambda c: c.data == "menu")
async def back_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "📋 **منوی اصلی:**\n\n"
        "😊 هر چی نیاز داری، اینجاست!",
        reply_markup=user_menu_keyboard()
    )
