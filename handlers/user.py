from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import *
import json

router = Router()

def join_keyboard():
    channels = get_channels()
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_banner(message):
    banner = get_banner()
    if banner["type"] == "photo" and banner["file_id"]:
        await message.answer_photo(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "video" and banner["file_id"]:
        await message.answer_video(banner["file_id"], caption=banner["text"])
    else:
        await message.answer(banner["text"])

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
        await message.answer("👋 سلام! برای دریافت چپتر از لینک مخصوص استفاده کن.")
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
            await call.answer(f"❌ خطا!", show_alert=True)
            return
    
    await call.message.delete()
    await send_file_and_banner(call.message, code)
