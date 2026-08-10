from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
import asyncio
import json
import os
import subprocess
import shutil
from datetime import datetime, timedelta
import re

router = Router()
user_states = {}

# ========================================
# ===== پنل ادمین =====
# ========================================

@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ افزودن چپتر"), KeyboardButton(text="📋 لیست چپترها")],
            [KeyboardButton(text="🗑 حذف چپتر"), KeyboardButton(text="➕ افزودن کانال")],
            [KeyboardButton(text="📁 افزودن پوشه"), KeyboardButton(text="📋 لیست کانال‌ها")],
            [KeyboardButton(text="👀 دیدن پنل عضویت"), KeyboardButton(text="📝 تنظیم بنر")],
            [KeyboardButton(text="🗑 حذف بنر"), KeyboardButton(text="👀 دیدن بنر")],
            [KeyboardButton(text="📊 آمار"), KeyboardButton(text="📢 ارسال همگانی")],
            [KeyboardButton(text="💬 نظرات"), KeyboardButton(text="❓ سوالات")],
            [KeyboardButton(text="👍 ری اکشن پست"), KeyboardButton(text="🧪 تست ربات")],
            [KeyboardButton(text="🤖 ساخت ربات جدید"), KeyboardButton(text="📂 پروژه‌های من")],
            [KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "🤖 **پنل مدیریت**\n\n"
        "👋 خوش اومدی! چیکار میخوای بکنی؟ 😊",
        reply_markup=keyboard
    )

# ========================================
# ===== بستن پنل =====
# ========================================

@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
    await message.answer("✅ پنل بسته شد! 😊", reply_markup=types.ReplyKeyboardRemove())

def clear_user_state(user_id):
    if user_id in user_states:
        del user_states[user_id]

# ========================================
# ===== 🧪 تست ربات (شبیه‌سازی کاربر) =====
# ========================================

@router.message(lambda m: m.text == "🧪 تست ربات" and m.from_user.id == ADMIN_ID)
async def test_robot(message: types.Message):
    """شبیه‌سازی کامل پروسه دریافت چپتر برای کاربر"""
    
    # ۱. گرفتن اولین چپتر
    files = get_all_files()
    if not files:
        await message.answer("❌ **هیچ چپتری ذخیره نشده!**\n\nلطفاً ابتدا یک چپتر اضافه کنید.")
        return
    
    first_code = files[0][0]
    
    # ۲. ساخت لینک تست
    bot_username = (await message.bot.get_me()).username
    test_link = f"https://t.me/{bot_username}?start={first_code}"
    
    # ۳. شبیه‌سازی پیام استارت
    await message.answer(
        f"🧪 **تست ربات - شبیه‌سازی کاربر**\n\n"
        f"📱 کاربر روی لینک زیر کلیک میکند:\n"
        f"`{test_link}`\n\n"
        f"🔄 در حال شبیه‌سازی...\n"
    )
    
    # ۴. شبیه‌سازی دریافت بنر و پیام خوش‌آمدگویی
    banner_data = get_active_banner()
    await message.answer("📝 **مرحله ۱: بنر و خوش‌آمدگویی**")
    await send_banner_test(message, banner_data)
    await message.answer(
        f"👋 **سلام کاربر تست!**\n\n"
        f"😊 خوش اومدی! از منو استفاده کن."
    )
    
    # ۵. شبیه‌سازی عضویت اجباری
    channels = get_channels()
    if channels:
        from handlers import join_keyboard
        post_link = get_reaction_post()
        
        await message.answer(
            "🔒 **مرحله ۲: عضویت اجباری**\n\n"
            "برای دریافت فایل، باید در کانال‌های زیر عضو شوید:",
            reply_markup=join_keyboard(channels, post_link)
        )
    else:
        await message.answer("✅ **مرحله ۲: عضویت اجباری**\n\nهیچ کانالی تنظیم نشده! (مرحله رد شد)")
    
    # ۶. شبیه‌سازی ری اکشن
    if post_link:
        await message.answer(
            "👍 **مرحله ۳: ری اکشن پست**\n\n"
            f"روی لینک زیر کلیک کنید و ری اکشن بزنید:\n"
            f"{post_link}\n\n"
            "✅ بعد از ری اکشن، فایل ارسال میشود."
        )
    else:
        await message.answer("👍 **مرحله ۳: ری اکشن پست**\n\nهیچ ری اکشنی تنظیم نشده! (مرحله رد شد)")
    
    # ۷. شبیه‌سازی دریافت فایل
    await message.answer(
        f"📄 **مرحله ۴: دریافت فایل**\n\n"
        f"در حال ارسال چپتر `{first_code}` ..."
    )
    
    file_info = find_file(first_code)
    if file_info:
        file_id, file_type, caption = file_info
        from handlers import send_file_only
        await send_file_only(message, file_id, file_type, caption or "")
    
    # ۸. شبیه‌سازی بنر پایین فایل
    await message.answer(
        "📝 **مرحله ۵: بنر پایین فایل**\n\n"
        "بنر فعلی ربات:"
    )
    await send_banner_test(message, banner_data)
    
    # ۹. جمع‌بندی
    await message.answer(
        "✅ **تست کامل شد!** 🎉\n\n"
        "اگر همه مراحل را دیدید، ربات شما سالم است.\n"
        "اگر مشکلی دیدید، لاگ را بررسی کنید."
    )

# ===== تابع ارسال بنر برای تست =====
async def send_banner_test(message, banner_data):
    if banner_data["type"] == "photo" and banner_data["file_id"]:
        await message.answer_photo(
            banner_data["file_id"],
            caption=banner_data["text"] or "📢 به ربات خوش اومدی!"
        )
    elif banner_data["type"] == "video" and banner_data["file_id"]:
        await message.answer_video(
            banner_data["file_id"],
            caption=banner_data["text"] or "📢 به ربات خوش اومدی!"
        )
    else:
        await message.answer(banner_data["text"] or "📢 به ربات خوش اومدی!")

# ========================================
# ===== دیدن پنل عضویت =====
# ========================================

@router.message(lambda m: m.text == "👀 دیدن پنل عضویت" and m.from_user.id == ADMIN_ID)
async def view_join_panel(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی برای عضویت اجباری تنظیم نشده! 😅")
        return
    
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem_inline")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "🎯 **پنل عضویت اجباری**\n\n"
        "برای دریافت فایل‌ها، اول باید تو این کانال‌ها عضو بشی! 😊",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "check_mem_inline")
async def check_mem_inline(call: types.CallbackQuery):
    await call.answer("✅ عضویت شما تایید شد! 😊", show_alert=True)
    await call.message.edit_text("✅ **عضویت شما تایید شد!**\n\nحالا میتونی از ربات استفاده کنی 😊")

# ========================================
# ===== ری اکشن پست =====
# ========================================

@router.message(lambda m: m.text == "👍 ری اکشن پست" and m.from_user.id == ADMIN_ID)
async def reaction_post(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_reaction_post"}
    await message.answer(
        "📢 **لینک پست کانال رو بفرست**\n\n"
        "مثال: `https://t.me/channel/123`\n\n"
        "کاربرا وقتی روی لینک کلیک کنن، باید ری اکشن بزنن و بعد فایل دریافت کنن."
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_reaction_post")
async def get_reaction_post(message: types.Message):
    post_link = message.text.strip()
    set_reaction_post(post_link)
    clear_user_state(message.from_user.id)
    await message.answer(f"✅ **لینک پست ذخیره شد!**\n\n{post_link}")

# ========================================
# ===== 👀 دیدن بنر =====
# ========================================

@router.message(lambda m: m.text == "👀 دیدن بنر" and m.from_user.id == ADMIN_ID)
async def view_banner(message: types.Message):
    banners = get_all_banners()
    if not banners:
        await message.answer("❌ هیچ بنری تنظیم نشده! 😅")
        return
    
    text = "📝 **لیست بنرها:**\n\n"
    for banner in banners:
        text += f"• ID: {banner['id']} | {banner['text'][:30]}... (نوع: {banner['type']}) - انقضا: {banner['expire_date'] or 'ندارد'}\n"
    
    await message.answer(text)

# ========================================
# ===== 🗑 حذف بنر =====
# ========================================

@router.message(lambda m: m.text == "🗑 حذف بنر" and m.from_user.id == ADMIN_ID)
async def delete_banner_start(message: types.Message):
    banners = get_all_banners()
    if not banners:
        await message.answer("❌ هیچ بنری وجود نداره!")
        return
    
    # ساخت دکمه‌های حذف
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"🗑 {b['id']} - {b['text'][:15]}") for b in banners[:2]],
            [KeyboardButton(text=f"🗑 {b['id']} - {b['text'][:15]}") for b in banners[2:4]],
            [KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    user_states[message.from_user.id] = {"state": "waiting_delete_banner"}
    await message.answer(
        "🗑 **برای حذف بنر، یکی رو انتخاب کن:**",
        reply_markup=keyboard
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and m.text.startswith("🗑 ") and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete_banner")
async def delete_banner_confirm(message: types.Message):
    # استخراج ID
    parts = message.text.replace("🗑 ", "").split(" - ")
    banner_id = int(parts[0])
    delete_banner(banner_id)
    clear_user_state(message.from_user.id)
    await message.answer(f"✅ **بنر {banner_id} حذف شد!**")

# ========================================
# ===== 📝 تنظیم بنر (با زمان‌بندی) =====
# ========================================

@router.message(lambda m: m.text == "📝 تنظیم بنر" and m.from_user.id == ADMIN_ID)
async def set_banner_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 بنر متنی")],
            [KeyboardButton(text="🖼 بنر عکس/فوروارد")],
            [KeyboardButton(text="🎬 بنر ویدیو/فوروارد")],
            [KeyboardButton(text="⏰ زمان‌بندی شده")],
            [KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    user_states[message.from_user.id] = {"state": "waiting_banner_type"}
    await message.answer(
        "📝 **نوع بنر رو انتخاب کن:**\n\n"
        "• متنی: فقط متن\n"
        "• عکس/فوروارد: عکس یا فوروارد شده\n"
        "• ویدیو/فوروارد: ویدیو یا فوروارد شده\n"
        "• زمان‌بندی شده: بنر در زمان مشخص ارسال بشه",
        reply_markup=keyboard
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner_type")
async def get_banner_type(message: types.Message):
    banner_type = message.text
    
    if banner_type == "📝 بنر متنی":
        user_states[message.from_user.id] = {"state": "waiting_banner_text"}
        await message.answer(
            "📝 **متن بنر رو بفرست**\n\n"
            "برای تنظیم زمان انقضا، بعد از متن بنویس:\n"
            "`/expire تعداد روز/هفته/ماه`\n\n"
            "مثال:\n"
            "`به ربات خوش اومدی! 😊 /expire 10 روز`\n"
            "`به ربات خوش اومدی! 😊 /expire 2 هفته`\n"
            "`به ربات خوش اومدی! 😊 /expire 1 ماه`"
        )
    
    elif banner_type == "🖼 بنر عکس/فوروارد":
        user_states[message.from_user.id] = {"state": "waiting_banner_photo"}
        await message.answer("🖼 **عکس یا پست فورواردی رو بفرست**\n\n(کپشن رو هم میتونی بنویسی)")
    
    elif banner_type == "🎬 بنر ویدیو/فوروارد":
        user_states[message.from_user.id] = {"state": "waiting_banner_video"}
        await message.answer("🎬 **ویدیو یا پست فورواردی رو بفرست**\n\n(کپشن رو هم میتونی بنویسی)")
    
    elif banner_type == "⏰ زمان‌بندی شده":
        user_states[message.from_user.id] = {"state": "waiting_banner_schedule"}
        await message.answer(
            "⏰ **زمان ارسال بنر رو بفرست**\n\n"
            "فرمت: `ساعت:دقیقه روز/ماه/سال`\n"
            "مثال: `12:00 10/08/2026`\n\n"
            "⏰ بعد از تنظیم زمان، متن بنر رو میفرستی."
        )
    
    else:
        await message.answer("❌ گزینه نامعتبر! دوباره انتخاب کن.")

# ===== بنر متنی =====
@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner_text")
async def set_banner_text(message: types.Message):
    text = message.text
    expire_date = None
    amount = None
    unit = None
    
    match = re.search(r'/expire\s+(\d+)\s*(روز|هفته|ماه)', text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        text = text.replace(match.group(0), '').strip()
        
        if unit == "روز":
            expire_date = (datetime.now() + timedelta(days=amount)).isoformat()
        elif unit == "هفته":
            expire_date = (datetime.now() + timedelta(weeks=amount)).isoformat()
        elif unit == "ماه":
            expire_date = (datetime.now() + timedelta(days=amount*30)).isoformat()
    
    banner_id = add_banner("text", None, text, expire_date)
    clear_user_state(message.from_user.id)
    
    if expire_date:
        await message.answer(
            f"✅ **بنر متنی ذخیره شد!** (ID: {banner_id})\n\n"
            f"📝 {text}\n"
            f"⏰ انقضا: {amount} {unit} دیگه\n"
            f"📅 تاریخ انقضا: {expire_date}"
        )
    else:
        await message.answer(
            f"✅ **بنر متنی ذخیره شد!** (ID: {banner_id})\n\n"
            f"📝 {text}\n"
            f"⏰ بدون تاریخ انقضا"
        )

# ===== بنر عکس =====
@router.message(lambda m: m.from_user.id == ADMIN_ID and (m.photo or m.document) and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner_photo")
async def set_banner_photo(message: types.Message):
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image"):
        file_id = message.document.file_id
    else:
        await message.answer("❌ لطفاً یک عکس بفرست!")
        return
    
    caption = message.caption or ""
    expire_date = None
    amount = None
    unit = None
    
    match = re.search(r'/expire\s+(\d+)\s*(روز|هفته|ماه)', caption)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        caption = caption.replace(match.group(0), '').strip()
        
        if unit == "روز":
            expire_date = (datetime.now() + timedelta(days=amount)).isoformat()
        elif unit == "هفته":
            expire_date = (datetime.now() + timedelta(weeks=amount)).isoformat()
        elif unit == "ماه":
            expire_date = (datetime.now() + timedelta(days=amount*30)).isoformat()
    
    banner_id = add_banner("photo", file_id, caption, expire_date)
    clear_user_state(message.from_user.id)
    
    await message.answer(
        f"✅ **بنر عکس ذخیره شد!** (ID: {banner_id})\n\n"
        f"📝 کپشن: {caption if caption else 'ندارد'}\n"
        f"⏰ انقضا: {f'{amount} {unit} دیگه' if expire_date else 'ندارد'}"
    )

# ===== بنر ویدیو =====
@router.message(lambda m: m.from_user.id == ADMIN_ID and (m.video or m.document) and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner_video")
async def set_banner_video(message: types.Message):
    if message.video:
        file_id = message.video.file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("video"):
        file_id = message.document.file_id
    else:
        await message.answer("❌ لطفاً یک ویدیو بفرست!")
        return
    
    caption = message.caption or ""
    expire_date = None
    amount = None
    unit = None
    
    match = re.search(r'/expire\s+(\d+)\s*(روز|هفته|ماه)', caption)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        caption = caption.replace(match.group(0), '').strip()
        
        if unit == "روز":
            expire_date = (datetime.now() + timedelta(days=amount)).isoformat()
        elif unit == "هفته":
            expire_date = (datetime.now() + timedelta(weeks=amount)).isoformat()
        elif unit == "ماه":
            expire_date = (datetime.now() + timedelta(days=amount*30)).isoformat()
    
    banner_id = add_banner("video", file_id, caption, expire_date)
    clear_user_state(message.from_user.id)
    
    await message.answer(
        f"✅ **بنر ویدیو ذخیره شد!** (ID: {banner_id})\n\n"
        f"📝 کپشن: {caption if caption else 'ندارد'}\n"
        f"⏰ انقضا: {f'{amount} {unit} دیگه' if expire_date else 'ندارد'}"
    )

# ========================================
# ===== ⏰ زمان‌بندی بنر =====
# ========================================

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner_schedule")
async def set_banner_schedule(message: types.Message):
    try:
        time_str, date_str = message.text.split()
        hour, minute = time_str.split(":")
        day, month, year = date_str.split("/")
        
        schedule_time = datetime(int(year), int(month), int(day), int(hour), int(minute))
        
        if schedule_time < datetime.now():
            await message.answer("❌ زمان وارد شده گذشته است! زمان آینده را وارد کن.")
            return
        
        user_states[message.from_user.id] = {
            "state": "waiting_banner_schedule_text",
            "schedule_time": schedule_time.isoformat()
        }
        await message.answer(
            f"⏰ **زمان ثبت شد:** {schedule_time.strftime('%H:%M %d/%m/%Y')}\n\n"
            f"📝 حالا **متن بنر** رو بفرست:"
        )
    except Exception as e:
        await message.answer(
            f"❌ **فرمت زمان اشتباه!**\n\n"
            f"فرمت صحیح: `ساعت:دقیقه روز/ماه/سال`\n"
            f"مثال: `12:00 10/08/2026`\n\n"
            f"خطا: {e}"
        )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner_schedule_text")
async def get_banner_schedule_text(message: types.Message):
    text = message.text
    schedule_time = user_states[message.from_user.id].get("schedule_time")
    
    banner_id = add_banner("text", None, text, None, schedule_time)
    clear_user_state(message.from_user.id)
    
    await message.answer(
        f"✅ **بنر زمان‌بندی شد!** (ID: {banner_id})\n\n"
        f"📝 {text}\n"
        f"⏰ ارسال در: {schedule_time}"
    )

# ========================================
# ===== بقیه کدهای قبلی =====
# ========================================

# ===== افزودن چپتر =====
@router.message(lambda m: m.text == "➕ افزودن چپتر" and m.from_user.id == ADMIN_ID)
async def add_file_start(message: types.Message):
    clear_user_state(message.from_user.id)
    user_states[message.from_user.id] = {"state": "waiting_code"}
    await message.answer(
        "📝 **کد چپتر رو بفرست:**\n"
        "مثال: `1_2`"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_code")
async def get_code(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_file", "code": message.text.strip()}
    await message.answer(
        "📄 **حالا فایل رو بفرست**\n\n"
        "می‌تونی اینا رو بفرستی:\n"
        "• PDF 📄\n"
        "• ZIP 📦\n"
        "• عکس 🖼️\n"
        "• ویدیو 🎬\n\n"
        "📝 اگه کپشن هم میخوای، موقع ارسال فایل بنویس!"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document)
async def get_file(message: types.Message):
    state = user_states.get(message.from_user.id, {})
    if state.get("state") != "waiting_file":
        await message.answer("❌ اول از گزینه «➕ افزودن چپتر» استفاده کن! 😅")
        return
    
    code = state.get("code")
    if not code:
        return
    
    caption = message.caption or ""
    file_type = "document"
    
    if message.document.mime_type == "application/pdf":
        file_type = "document"
    elif message.document.mime_type and message.document.mime_type.startswith("image"):
        file_type = "photo"
    elif message.document.mime_type and message.document.mime_type.startswith("video"):
        file_type = "video"
    
    save_file(code, message.document.file_id, file_type, caption)
    clear_user_state(message.from_user.id)
    await message.answer(
        f"✅ **چپتر {code} ذخیره شد!** 🎉\n"
        f"📂 نوع: {file_type}\n"
        f"📝 کپشن: {caption if caption else 'ندارد'}"
    )

# ===== لیست چپترها =====
@router.message(lambda m: m.text == "📋 لیست چپترها" and m.from_user.id == ADMIN_ID)
async def list_files(message: types.Message):
    files = get_all_files()
    if not files:
        await message.answer("❌ هیچ چپتری ذخیره نشده! 😅")
        return
    text = "📋 **لیست چپترها:**\n\n" + "\n".join([f"• `{code}` ({type})" for code, type, _ in files])
    await message.answer(text)

# ===== حذف چپتر =====
@router.message(lambda m: m.text == "🗑 حذف چپتر" and m.from_user.id == ADMIN_ID)
async def delete_file_start(message: types.Message):
    files = get_all_files()
    if not files:
        await message.answer("❌ هیچ چپتری وجود نداره! 😅")
        return
    clear_user_state(message.from_user.id)
    user_states[message.from_user.id] = {"state": "waiting_delete"}
    await message.answer("📝 کد چپتر رو برای حذف بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete")
async def delete_file_confirm(message: types.Message):
    code = message.text.strip()
    if find_file(code):
        delete_file(code)
        await message.answer(f"✅ چپتر {code} حذف شد! 😊")
    else:
        await message.answer(f"❌ چپتر {code} پیدا نشد! 🤔")
    clear_user_state(message.from_user.id)

# ===== افزودن کانال =====
@router.message(lambda m: m.text == "➕ افزودن کانال" and m.from_user.id == ADMIN_ID)
async def add_channel_start(message: types.Message):
    clear_user_state(message.from_user.id)
    user_states[message.from_user.id] = {"state": "waiting_channel"}
    await message.answer(
        "📢 **نام کاربری کانال رو بفرست**\n"
        "مثال: `my_channel`\n\n"
        "⚠️ بدون @ بفرست!"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_channel")
async def get_channel(message: types.Message):
    ch = message.text.strip().replace("@", "")
    add_channel(ch)
    clear_user_state(message.from_user.id)
    await message.answer(f"✅ کانال @{ch} اضافه شد! 🎉")

# ===== حذف کانال =====
@router.message(lambda m: m.text == "🗑 حذف کانال" and m.from_user.id == ADMIN_ID)
async def delete_channel_start(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی وجود نداره! 😅")
        return
    clear_user_state(message.from_user.id)
    user_states[message.from_user.id] = {"state": "waiting_del_channel"}
    await message.answer("📝 نام کاربری کانال رو برای حذف بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_del_channel")
async def delete_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")
    delete_channel(ch)
    clear_user_state(message.from_user.id)
    await message.answer(f"✅ کانال @{ch} حذف شد! 😊")

# ===== لیست کانال‌ها =====
@router.message(lambda m: m.text == "📋 لیست کانال‌ها" and m.from_user.id == ADMIN_ID)
async def list_channels(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی ثبت نشده! 😅")
        return
    text = "📋 **لیست کانال‌ها:**\n\n" + "\n".join([f"• @{ch}" for ch in channels])
    await message.answer(text)

# ===== آمار =====
@router.message(lambda m: m.text == "📊 آمار" and m.from_user.id == ADMIN_ID)
async def stats(message: types.Message):
    files = get_all_files()
    channels = get_channels()
    users = get_user_count()
    await message.answer(
        f"📊 **آمار ربات:**\n\n"
        f"👥 **تعداد کاربران:** {users} نفر\n"
        f"📁 **تعداد چپترها:** {len(files)} تا\n"
        f"📢 **تعداد کانال‌ها:** {len(channels)} تا"
    )

# ===== نظرات =====
@router.message(lambda m: m.text == "💬 نظرات" and m.from_user.id == ADMIN_ID)
async def view_feedback(message: types.Message):
    feedbacks = get_all_feedback()
    if not feedbacks:
        await message.answer("❌ نظری ثبت نشده! 😅")
        return
    text = "💬 **لیست نظرات:**\n\n"
    for id, user_id, msg, date in feedbacks[:10]:
        text += f"#{id} | کاربر {user_id}\n{msg}\n{date}\n---\n"
    if len(feedbacks) > 10:
        text += f"\n... و {len(feedbacks) - 10} نظر دیگه"
    await message.answer(text)

# ===== سوالات =====
@router.message(lambda m: m.text == "❓ سوالات" and m.from_user.id == ADMIN_ID)
async def view_questions(message: types.Message):
    questions = get_pending_questions()
    if not questions:
        await message.answer("❌ سوال بدون پاسخی وجود نداره! 😅")
        return
    for id, user_id, q, date in questions[:5]:
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="✏️ پاسخ", callback_data=f"answer_{id}")]
            ]
        )
        await message.answer(
            f"❓ سوال #{id}\nاز کاربر {user_id}\n{q}\n{date}",
            reply_markup=keyboard
        )
    if len(questions) > 5:
        await message.answer(f"... و {len(questions) - 5} سوال دیگه")

@router.callback_query(lambda c: c.data.startswith("answer_"))
async def answer_question_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    question_id = int(call.data.split("_")[1])
    user_states[call.from_user.id] = {"state": "waiting_answer", "question_id": question_id}
    await call.message.answer("✏️ پاسخ سوال رو بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_answer")
async def get_answer(message: types.Message):
    question_id = user_states[message.from_user.id].get("question_id")
    answer = message.text
    
    question_data = get_question_data(question_id)
    if question_data:
        user_id = question_data[0]
        try:
            await message.bot.send_message(user_id, f"✅ **پاسخ سوال شما:**\n\n{answer}")
        except:
            pass
    
    answer_question(question_id, answer)
    clear_user_state(message.from_user.id)
    await message.answer("✅ پاسخ ذخیره و برای کاربر ارسال شد!")

# ===== ارسال همگانی =====
@router.message(lambda m: m.text == "📢 ارسال همگانی" and m.from_user.id == ADMIN_ID)
async def broadcast_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📤 ارسال فوری")],
            [KeyboardButton(text="⏰ زمان‌بندی شده")],
            [KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    await message.answer("📢 نوع ارسال رو انتخاب کن:", reply_markup=keyboard)

@router.message(lambda m: m.text == "📤 ارسال فوری" and m.from_user.id == ADMIN_ID)
async def broadcast_immediate(message: types.Message):
    clear_user_state(message.from_user.id)
    user_states[message.from_user.id] = {"state": "waiting_broadcast_immediate"}
    await message.answer("📝 پیام رو بفرست تا فوری به همه برسه:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_broadcast_immediate")
async def send_broadcast_immediate(message: types.Message):
    users = get_all_users()
    if not users:
        await message.answer("❌ کاربری وجود نداره!")
        return
    clear_user_state(message.from_user.id)
    await message.answer(f"📤 ارسال به {len(users)} کاربر شروع شد...")
    success = 0
    for user_id in users:
        try:
            await message.bot.send_message(user_id, message.text)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await message.answer(f"✅ پیام به {success} کاربر ارسال شد!")

@router.message(lambda m: m.text == "⏰ زمان‌بندی شده" and m.from_user.id == ADMIN_ID)
async def broadcast_scheduled(message: types.Message):
    clear_user_state(message.from_user.id)
    user_states[message.from_user.id] = {"state": "waiting_scheduled_time"}
    await message.answer("⏰ تاریخ و زمان رو به فرمت زیر بفرست:\n\n`1402-08-15 20:30`")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_scheduled_time")
async def get_scheduled_time(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_scheduled_message", "time": message.text.strip()}
    await message.answer(f"⏰ زمان ثبت شد: {message.text}\n\n📝 حالا پیام رو بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_scheduled_message")
async def send_scheduled_broadcast(message: types.Message):
    add_scheduled_broadcast(message.text, user_states[message.from_user.id].get("time"), "pending")
    clear_user_state(message.from_user.id)
    await message.answer("⏰ پیام در زمان مشخص شده ارسال خواهد شد!")

# ========================================
# ===== 🤖 ساخت ربات جدید (خلاصه) =====
# ========================================

PROJECTS_DIR = "projects"

if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)

def load_projects():
    if os.path.exists(f"{PROJECTS_DIR}/projects.json"):
        with open(f"{PROJECTS_DIR}/projects.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_projects(projects):
    with open(f"{PROJECTS_DIR}/projects.json", "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)

@router.message(lambda m: m.text == "🤖 ساخت ربات جدید" and m.from_user.id == ADMIN_ID)
async def create_bot_start(message: types.Message):
    clear_user_state(message.from_user.id)
    user_states[message.from_user.id] = {"state": "waiting_bot_name"}
    await message.answer(
        "🤖 **ساخت ربات جدید**\n\n"
        "📝 یه اسم برای پروژه انتخاب کن:\n"
        "(مثلاً: `ربات چپتر`, `ربات فروشگاهی` و...)"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_bot_name")
async def get_bot_name(message: types.Message):
    project_name = message.text.strip()
    user_states[message.from_user.id] = {"state": "waiting_bot_token", "name": project_name}
    await message.answer(
        f"📝 **اسم پروژه:** {project_name}\n\n"
        "🔑 حالا **توکن ربات** رو از @BotFather بگیر و بفرست:\n"
        "(مثل: `123456:ABCdef...`)"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_bot_token")
async def get_bot_token(message: types.Message):
    token = message.text.strip()
    user_states[message.from_user.id]["token"] = token
    user_states[message.from_user.id]["state"] = "waiting_bot_admin_id"
    await message.answer(
        "🆔 حالا **آیدی عددی خودت** رو بفرست:\n"
        "(همون ADMIN_ID که داری)"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_bot_admin_id")
async def get_bot_admin_id(message: types.Message):
    try:
        admin_id = int(message.text.strip())
        user_states[message.from_user.id]["admin_id"] = admin_id
        user_states[message.from_user.id]["state"] = "waiting_bot_gemini"
        await message.answer(
            "🤖 **کلید Gemini** (اختیاری)\n\n"
            "اگه میخوای رباتت هوش مصنوعی داشته باشه، کلید رو بفرست.\n"
            "اگه نمیخوای، فقط بفرست `نه`"
        )
    except:
        await message.answer("❌ لطفاً یه عدد معتبر بفرست!")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_bot_gemini")
async def get_bot_gemini(message: types.Message):
    gemini_key = message.text.strip()
    if gemini_key.lower() == "نه":
        gemini_key = ""
    
    data = user_states[message.from_user.id]
    project_name = data["name"]
    token = data["token"]
    admin_id = data["admin_id"]
    
    project_path = f"{PROJECTS_DIR}/{project_name}"
    if os.path.exists(project_path):
        await message.answer(f"❌ پروژه‌ای با اسم `{project_name}` وجود داره! اسم دیگه‌ای انتخاب کن.")
        return
    
    os.makedirs(project_path)
    
    # ساخت فایل‌ها
    config_content = f'''import os

BOT_TOKEN = "{token}"
ADMIN_ID = {admin_id}

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN تنظیم نشده!")
'''
    with open(f"{project_path}/config.py", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    main_content = f'''import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    print("🤖 ربات {project_name} روشن شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
'''
    with open(f"{project_path}/main.py", "w", encoding="utf-8") as f:
        f.write(main_content)
    
    handlers_content = '''from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID

router = Router()

@router.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        f"👋 سلام {message.from_user.first_name}!\\n\\n"
        "به ربات خوش اومدی! 😊\\n"
        "از منو استفاده کن."
    )

@router.message(Command("menu"))
async def menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 راهنما", callback_data="help")],
        [InlineKeyboardButton(text="👤 پروفایل", callback_data="profile")]
    ])
    await message.answer("📋 منوی اصلی:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "help")
async def help_menu(call: types.CallbackQuery):
    await call.message.edit_text("📖 راهنما:\\n\\nبه ربات خوش اومدی! 😊")

@router.callback_query(lambda c: c.data == "profile")
async def profile_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        f"👤 پروفایل:\\n\\n"
        f"آیدی: {call.from_user.id}\\n"
        f"نام: {call.from_user.full_name}"
    )

@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ پنل مدیریت:")
'''
    with open(f"{project_path}/handlers.py", "w", encoding="utf-8") as f:
        f.write(handlers_content)
    
    req_content = '''aiogram==3.13.1
'''
    with open(f"{project_path}/requirements.txt", "w", encoding="utf-8") as f:
        f.write(req_content)
    
    projects = load_projects()
    projects[project_name] = {
        "name": project_name,
        "token": token,
        "admin_id": admin_id,
        "gemini_key": gemini_key,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    save_projects(projects)
    
    clear_user_state(message.from_user.id)
    
    await message.answer(
        f"✅ **ربات {project_name} ساخته شد!** 🎉\n\n"
        f"📂 مسیر: `{project_path}`\n"
        f"🔑 توکن: `{token[:10]}...`\n"
        f"🆔 آیدی ادمین: {admin_id}\n"
        f"🤖 Gemini: {'✅' if gemini_key else '❌'}\n\n"
        f"برای اجرا، از دکمه «📂 پروژه‌های من» استفاده کن."
    )

# ========================================
# ===== 📂 پروژه‌های من =====
# ========================================

@router.message(lambda m: m.text == "📂 پروژه‌های من" and m.from_user.id == ADMIN_ID)
async def my_projects(message: types.Message):
    projects = load_projects()
    if not projects:
        await message.answer("❌ هیچ پروژه‌ای نداری! 😅\n\nاز دکمه «🤖 ساخت ربات جدید» استفاده کن.")
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"📁 {name}") for name in list(projects.keys())[:2]],
            [KeyboardButton(text="➕ ساخت ربات جدید")],
            [KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        f"📂 **پروژه‌های شما:**\n\n"
        + "\n".join([f"• {name}" for name in projects.keys()]),
        reply_markup=keyboard
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and m.text.startswith("📁 "))
async def view_project(message: types.Message):
    project_name = message.text.replace("📁 ", "")
    projects = load_projects()
    
    if project_name not in projects:
        await message.answer("❌ پروژه پیدا نشد!")
        return
    
    project = projects[project_name]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="▶️ اجرا"), KeyboardButton(text="⏹ توقف")],
            [KeyboardButton(text="📝 ویرایش"), KeyboardButton(text="🗑 حذف")],
            [KeyboardButton(text="📤 خروجی"), KeyboardButton(text="🔙 بازگشت به لیست")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"📂 **پروژه:** {project_name}\n\n"
        f"🔑 توکن: `{project['token'][:10]}...`\n"
        f"🆔 ادمین: {project['admin_id']}\n"
        f"🤖 Gemini: {'✅' if project.get('gemini_key') else '❌'}\n"
        f"📅 ساخته شده: {project.get('created_at', 'نامشخص')}\n"
        f"📊 وضعیت: {'🟢 فعال' if project.get('status') == 'active' else '🔴 غیرفعال'}",
        reply_markup=keyboard
    )
    
    user_states[message.from_user.id] = {"current_project": project_name}

# ===== اجرا =====
@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text == "▶️ اجرا" and user_states.get(m.from_user.id, {}).get("current_project"))
async def run_project(message: types.Message):
    project_name = user_states[message.from_user.id]["current_project"]
    project_path = f"{PROJECTS_DIR}/{project_name}"
    
    if not os.path.exists(project_path):
        await message.answer("❌ پروژه پیدا نشد!")
        return
    
    try:
        process = subprocess.Popen(
            ["python3", "main.py"],
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        projects = load_projects()
        projects[project_name]["status"] = "active"
        projects[project_name]["pid"] = process.pid
        save_projects(projects)
        
        await message.answer(f"✅ **ربات {project_name} با موفقیت اجرا شد!** 🚀")
    except Exception as e:
        await message.answer(f"❌ خطا در اجرا: {str(e)}")

# ===== توقف =====
@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text == "⏹ توقف" and user_states.get(m.from_user.id, {}).get("current_project"))
async def stop_project(message: types.Message):
    project_name = user_states[message.from_user.id]["current_project"]
    projects = load_projects()
    
    pid = projects.get(project_name, {}).get("pid")
    if pid:
        try:
            os.kill(pid, 9)
            projects[project_name]["status"] = "stopped"
            save_projects(projects)
            await message.answer(f"✅ ربات {project_name} متوقف شد!")
        except:
            await message.answer(f"⚠️ ربات در حال اجرا نیست!")
    else:
        await message.answer(f"⚠️ ربات در حال اجرا نیست!")

# ===== حذف پروژه =====
@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text == "🗑 حذف" and user_states.get(m.from_user.id, {}).get("current_project"))
async def delete_project(message: types.Message):
    project_name = user_states[message.from_user.id]["current_project"]
    
    shutil.rmtree(f"{PROJECTS_DIR}/{project_name}")
    
    projects = load_projects()
    if project_name in projects:
        del projects[project_name]
    save_projects(projects)
    
    clear_user_state(message.from_user.id)
    await message.answer(f"✅ پروژه {project_name} حذف شد!")

# ===== بازگشت به لیست =====
@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text == "🔙 بازگشت به لیست")
async def back_to_list(message: types.Message):
    await my_projects(message)
