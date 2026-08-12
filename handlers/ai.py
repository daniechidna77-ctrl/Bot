from aiogram import Router, types
from aiogram.filters import Command
from config import ADMIN_ID, GEMINI_API_KEY
import aiohttp
import json
import os

router = Router()

# ========================================
# ===== کلینر با Gemini =====
# ========================================
@router.message(Command("clean"))
async def clean_file(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.answer("❌ لطفاً به یک فایل پاسخ بده!")
        return
    
    file = message.reply_to_message.document
    await message.answer(
        f"🔄 **در حال پردازش فایل با Gemini:** {file.file_name}\n\n"
        "🔹 پاک‌سازی\n"
        "🔹 بهینه‌سازی\n"
        "🔹 خلاصه‌سازی"
    )
    
    # دانلود فایل
    file_obj = await message.bot.get_file(file.file_id)
    file_path = f"temp_{message.from_user.id}_{file.file_name}"
    await message.bot.download_file(file_obj.file_path, file_path)
    
    # پردازش با Gemini
    try:
        from utils.cleaner import summarize_with_gemini
        summary = await summarize_with_gemini(file_path)
        if summary:
            await message.answer(f"📝 **خلاصه فایل:**\n\n{summary}")
        else:
            await message.answer("❌ خطا در پردازش با Gemini!")
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")
    
    os.remove(file_path)
