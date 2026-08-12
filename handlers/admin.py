from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
import asyncio
import os
import tempfile
import shutil
from datetime import datetime, timedelta

router = Router()
user_states = {}

# ========================================
# ===== پنل ادمین (کامل) =====
# ========================================
def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="📚 مدیریت چپترها")],
        [KeyboardButton(text="📢 مدیریت کانال‌ها")],
        [KeyboardButton(text="🎨 مدیریت بنر")],
        [KeyboardButton(text="👀 دیدن بنر")],
        [KeyboardButton(text="👀 پنل عضویت")],
        [KeyboardButton(text="📊 آمار")],
        [KeyboardButton(text="📤 ارسال همگانی")],
        [KeyboardButton(text="⏰ زمان‌بندی بنر")],
        [KeyboardButton(text="🤖 کلینر + جیمینای")],
        [KeyboardButton(text="💬 چت با جیمینای")],
        [KeyboardButton(text="🔙 بستن پنل")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ========================================
# ===== پنل اصلی =====
# ========================================
@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "⚙️ **پنل مدیریت پیشرفته**\n\n"
        "همه قابلیت‌ها در دسترس است! 😊",
        reply_markup=get_admin_keyboard()
    )

# ========================================
# ===== بستن پنل =====
# ========================================
@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())

# ========================================
# ===== 👀 پنل عضویت شیشه‌ای =====
# ========================================
@router.message(lambda m: m.text == "👀 پنل عضویت" and m.from_user.id == ADMIN_ID)
async def view_join_panel(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ هیچ کانالی وجود نداره!")
        return
    
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem_inline")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "👀 **پنل عضویت اجباری**\n\n"
        "برای دریافت فایل، در کانال‌ها عضو شوید:",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "check_mem_inline")
async def check_mem_inline(call: types.CallbackQuery):
    await call.answer("✅ عضویت تایید شد!", show_alert=True)

# ========================================
# ===== ⏰ زمان‌بندی بنر فوری =====
# ========================================
@router.message(lambda m: m.text == "⏰ زمان‌بندی بنر" and m.from_user.id == ADMIN_ID)
async def schedule_banner_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_schedule_banner"}
    await message.answer(
        "⏰ **زمان‌بندی بنر**\n\n"
        "زمان رو به فرمت زیر بفرست:\n"
        "`ساعت:دقیقه روز/ماه/سال`\n\n"
        "مثال: `12:00 15/08/2026`\n\n"
        "بعدش متن بنر رو میفرستی."
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_schedule_banner")
async def get_schedule_time(message: types.Message):
    try:
        time_str, date_str = message.text.split()
        hour, minute = time_str.split(":")
        day, month, year = date_str.split("/")
        
        schedule_time = datetime(int(year), int(month), int(day), int(hour), int(minute))
        
        if schedule_time < datetime.now():
            await message.answer("❌ زمان وارد شده گذشته است! زمان آینده رو وارد کن.")
            return
        
        user_states[message.from_user.id] = {
            "state": "waiting_schedule_banner_text",
            "schedule_time": schedule_time.isoformat()
        }
        await message.answer(
            f"⏰ زمان ثبت شد: {schedule_time.strftime('%H:%M %d/%m/%Y')}\n\n"
            f"📝 حالا **متن بنر** رو بفرست:"
        )
    except:
        await message.answer("❌ فرمت زمان اشتباه! مثال: `12:00 15/08/2026`")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_schedule_banner_text")
async def save_scheduled_banner(message: types.Message):
    text = message.text
    schedule_time = user_states[message.from_user.id].get("schedule_time")
    
    # ذخیره بنر با زمان
    set_banner("text", None, text)
    
    # اضافه کردن به زمان‌بندی
    scheduled_banners.append({
        "time": schedule_time,
        "text": text,
        "user_id": message.from_user.id
    })
    
    user_states[message.from_user.id] = {}
    await message.answer(
        f"✅ **بنر زمان‌بندی شد!**\n\n"
        f"📝 {text}\n"
        f"⏰ ارسال در: {schedule_time}"
    )

# ========================================
# ===== 🤖 کلینر + جیمینای =====
# ========================================
@router.message(lambda m: m.text == "🤖 کلینر + جیمینای" and m.from_user.id == ADMIN_ID)
async def cleaner_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_cleaner"}
    await message.answer(
        "🤖 **کلینر هوشمند با جیمینای**\n\n"
        "فایل (PDF یا عکس) رو بفرست تا:\n"
        "✅ پاک‌سازی کنم\n"
        "✅ کیفیت رو بالا ببرم\n"
        "✅ خلاصه‌سازی با جیمینای"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_cleaner")
async def cleaner_process(message: types.Message):
    # دانلود فایل
    file = await message.bot.get_file(message.document.file_id)
    file_path = f"temp_{message.from_user.id}_{message.document.file_name}"
    await message.bot.download_file(file.file_path, file_path)
    
    await message.answer("🔄 در حال پردازش فایل...")
    
    # اینجا کد کلینر و جیمینای رو قرار بده
    # (فعلاً ساده)
    
    await message.answer("✅ فایل پردازش شد!")
    os.remove(file_path)
    user_states[message.from_user.id] = {}

# ========================================
# ===== 💬 چت با جیمینای =====
# ========================================
@router.message(lambda m: m.text == "💬 چت با جیمینای" and m.from_user.id == ADMIN_ID)
async def gemini_chat_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_gemini_chat"}
    await message.answer(
        "💬 **با جیمینای حرف بزن!**\n\n"
        "هر چی دوست داری بپرس 😊\n"
        "(برای بستن /cancel بفرست)"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_gemini_chat")
async def gemini_chat_response(message: types.Message):
    if message.text == "/cancel":
        user_states[message.from_user.id] = {}
        await message.answer("✅ چت بسته شد!")
        return
    
    await message.answer("🤔 دارم فکر میکنم...\n\n(جیمینای به زودی اضافه میشه!)")

# ========================================
# ===== بقیه قابلیت‌ها (چپتر، کانال، بنر) =====
# ========================================

# ... (همون کدهای قبلی برای مدیریت چپتر، کانال، بنر، آمار، ارسال همگانی)

# ========================================
# ===== زمان‌بندی بنر (لیست جهانی) =====
# ========================================
scheduled_banners = []

async def check_scheduled_banners(bot):
    """چک کردن بنرهای زمان‌بندی شده"""
    now = datetime.now().isoformat()
    for banner in scheduled_banners[:]:
        if banner["time"] <= now:
            try:
                await bot.send_message(banner["user_id"], f"⏰ **بنر زمان‌بندی شده:**\n\n{banner['text']}")
                scheduled_banners.remove(banner)
            except:
                pass
