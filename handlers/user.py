from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import *
import json
import os

router = Router()

# ========================================
# ===== کیبورد منوی کاربر =====
# ========================================
def user_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📖 راهنما")],
            [KeyboardButton(text="📢 کانال‌ها")],
            [KeyboardButton(text="👤 پروفایل")],
            [KeyboardButton(text="🛒 فروشگاه")],
            [KeyboardButton(text="❓ سوال")],
            [KeyboardButton(text="📤 دعوت به ربات")]
        ],
        resize_keyboard=True
    )

# ========================================
# ===== کیبورد عضویت =====
# ========================================
def join_keyboard():
    channels = get_channels()
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========================================
# ===== تابع ارسال بنر =====
# ========================================
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
# ===== تابع ارسال فایل =====
# ========================================
async def send_file_and_banner(message, code):
    file_info = find_file(code)
    if file_info:
        file_id, file_type, caption = file_info
        increment_download(code)
        
        if file_type == "document":
            await message.answer_document(file_id, caption=caption or f"📖 چپتر {code}")
        elif file_type == "photo":
            await message.answer_photo(file_id, caption=caption or f"📖 چپتر {code}")
        elif file_type == "video":
            await message.answer_video(file_id, caption=caption or f"📖 چپتر {code}")
        else:
            await message.answer_document(file_id, caption=caption or f"📖 چپتر {code}")
        
        await send_banner(message)
        return True
    return False

# ========================================
# ===== استارت =====
# ========================================
@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    
    add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or ""
    )
    
    if len(args) == 1:
        await send_banner(message)
        await message.answer(
            f"👋 **سلام {message.from_user.first_name}!**\n\n"
            "به ربات خوش اومدی!\n"
            "برای دریافت چپتر از لینک مخصوص استفاده کن.\n"
            "مثال: `https://t.me/ربات?start=1`",
            reply_markup=user_menu_keyboard()
        )
        return
    
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
    
    await send_file_and_banner(message, code)

# ========================================
# ===== بررسی عضویت =====
# ========================================
@router.callback_query(lambda c: c.data == "check_mem")
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
            member = await call.bot.get_chat_member(f"@{ch}", call.from_user.id)
            if member.status not in ["member", "administrator", "creator"]:
                await call.answer(f"❌ در کانال @{ch} عضو نشدی!", show_alert=True)
                return
        except:
            await call.answer(f"❌ خطا در بررسی کانال @{ch}!", show_alert=True)
            return
    
    await call.message.delete()
    await send_file_and_banner(call.message, code)

# ========================================
# ===== منوی کاربر =====
# ========================================
@router.message(Command("menu"))
async def menu(message: types.Message):
    await message.answer(
        "📋 **منوی اصلی**\n\n"
        "از دکمه‌های زیر استفاده کن:",
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
        "`https://t.me/ربات?start=1_2`\n\n"
        "🔹 اول عضو کانال‌ها شو، بعد فایل میاد!\n"
        "🔹 اگه سوالی داری، از منو بپرس 😊"
    )

# ========================================
# ===== کانال‌ها =====
# ========================================
@router.message(lambda m: m.text == "📢 کانال‌ها")
async def channels_list(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ هیچ کانالی ثبت نشده!")
        return
    text = "📢 **لیست کانال‌ها:**\n\n" + "\n".join([f"• @{ch}" for ch in channels])
    await message.answer(text)

# ========================================
# ===== پروفایل =====
# ========================================
@router.message(lambda m: m.text == "👤 پروفایل")
async def profile(message: types.Message):
    user = get_user_by_id(message.from_user.id)
    if not user:
        await message.answer("❌ کاربر پیدا نشد!")
        return
    
    await message.answer(
        f"👤 **پروفایل شما:**\n\n"
        f"🆔 آیدی: `{user[0]}`\n"
        f"📛 نام: {user[2] or 'نامشخص'}\n"
        f"👤 یوزرنیم: @{user[1] or 'ندارد'}"
    )

# ========================================
# ===== سوال =====
# ========================================
@router.message(lambda m: m.text == "❓ سوال")
async def ask_question(message: types.Message):
    add_question(message.from_user.id, message.text)
    await message.answer("✅ سوال شما ثبت شد! به زودی پاسخ داده میشه.")

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

@router.callback_query(lambda c: c.data == "copy_bot_link")
async def copy_bot_link(call: types.CallbackQuery):
    await call.answer(f"✅ لینک کپی شد!", show_alert=True)
