from aiogram import Router, types
from aiogram.filters import Command
from database import get_channels

router = Router()

# ========================================
# ===== لیست کانال‌ها =====
# ========================================
@router.message(Command("channels"))
async def list_channels(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ هیچ کانالی ثبت نشده!")
        return
    text = "📢 **لیست کانال‌ها:**\n\n" + "\n".join([f"• @{ch}" for ch in channels])
    await message.answer(text)
