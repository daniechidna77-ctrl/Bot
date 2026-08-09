from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
import asyncio
from datetime import datetime

router = Router()
user_states = {}

# ===== پنل ادمین (با دکمه افزودن پوشه) =====
@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ افزودن چپتر"), KeyboardButton(text="📋 لیست چپترها")],
            [KeyboardButton(text="🗑 حذف چپتر"), KeyboardButton(text="➕ افزودن کانال")],
            [KeyboardButton(text="📁 افزودن پوشه"), KeyboardButton(text="📋 لیست کانال‌ها")],
            [KeyboardButton(text="📝 تنظیم بنر"), KeyboardButton(text="🗑 حذف بنر")],
            [KeyboardButton(text="👀 دیدن بنر"), KeyboardButton(text="📊 آمار")],
            [KeyboardButton(text="📢 ارسال همگانی"), KeyboardButton(text="💬 نظرات")],
            [KeyboardButton(text="❓ سوالات"), KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    await message.answer("🤖 به پنل مدیریت خوش اومدی! چیکار میخوای بکنی؟ 😊", reply_markup=keyboard)

# ===== بستن پنل =====
@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد! 😊", reply_markup=types.ReplyKeyboardRemove())

# ===== دیدن پنل عضویت (با پیام شاد) =====
@router.message(lambda m: m.text == "👀 دیدن پنل عضویت" and m.from_user.id == ADMIN_ID)
async def view_join_panel(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی برای عضویت اجباری تنظیم نشده! 😅")
        return
    
    # ساخت دکمه‌های عضویت
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}")])
    if len(channels) > 1:
        buttons.append([InlineKeyboardButton(text="🔗 عضویت در همه", callback_data="join_all")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "🎯 **پنل عضویت اجباری**\n\n"
        "برای دریافت فایل‌ها، اول باید تو این کانال‌ها عضو بشی! 😊\n"
        "اگه عضو شدی، بزن **عضو شدم** تا بریم سراغ فایل‌ها 🚀",
        reply_markup=keyboard
    )

# ===== دیدن بنر =====
@router.message(lambda m: m.text == "👀 دیدن بنر" and m.from_user.id == ADMIN_ID)
async def view_banner(message: types.Message):
    banner = get_banner()
    await message.answer(
        f"📝 **بنر فعلی ربات:**\n\n"
        f"「 {banner} 」\n\n"
        f"اگه خوشت نمیاد، با «📝 تنظیم بنر» عوضش کن 😉"
    )

# ===== افزودن پوشه (چند کانال با هم) =====
@router.message(lambda m: m.text == "📁 افزودن پوشه" and m.from_user.id == ADMIN_ID)
async def add_folder_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_folder_channels"}
    await message.answer(
        "📁 **افزودن چند کانال با هم**\n\n"
        "اسم کانال‌ها رو با کاما (,) از هم جدا کن:\n"
        "مثال: `channel1,channel2,channel3`\n\n"
        "⚠️ بدون @ بفرست!"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_folder_channels")
async def get_folder_channels(message: types.Message):
    channels = [ch.strip().replace("@", "") for ch in message.text.split(",")]
    added = 0
    for ch in channels:
        if ch:
            add_channel(ch)
            added += 1
    user_states[message.from_user.id] = {}
    await message.answer(
        f"✅ **{added} تا کانال با موفقیت اضافه شدن!** 🎉\n\n"
        f"کانال‌ها:\n" + "\n".join([f"• @{ch}" for ch in channels if ch])
    )

# ===== افزودن چپتر با کپشن =====
@router.message(lambda m: m.text == "➕ افزودن چپتر" and m.from_user.id == ADMIN_ID)
async def add_file_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_code"}
    await message.answer(
        "📝 **کد چپتر رو بفرست:**\n"
        "مثال: `1_2`\n\n"
        "اگه میخوای یه کد خاص بذاری، بفرستش 😊"
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
    user_states[message.from_user.id] = {}
    await message.answer(
        f"✅ **چپتر {code} ذخیره شد!** 🎉\n"
        f"📂 نوع: {file_type}\n"
        f"📝 کپشن: {caption if caption else 'ندارد'}\n\n"
        f"اگه خوشت میاد، یه چپتر دیگه هم اضافه کن 😉"
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
    user_states[message.from_user.id] = {}

# ===== افزودن کانال =====
@router.message(lambda m: m.text == "➕ افزودن کانال" and m.from_user.id == ADMIN_ID)
async def add_channel_start(message: types.Message):
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
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ کانال @{ch} اضافه شد! 🎉")

# ===== حذف کانال =====
@router.message(lambda m: m.text == "🗑 حذف کانال" and m.from_user.id == ADMIN_ID)
async def delete_channel_start(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی وجود نداره! 😅")
        return
    user_states[message.from_user.id] = {"state": "waiting_del_channel"}
    await message.answer("📝 نام کاربری کانال رو برای حذف بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_del_channel")
async def delete_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")
    delete_channel(ch)
    user_states[message.from_user.id] = {}
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

# ===== تنظیم بنر =====
@router.message(lambda m: m.text == "📝 تنظیم بنر" and m.from_user.id == ADMIN_ID)
async def set_banner_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_banner"}
    await message.answer("📝 **متن بنر جدید رو بفرست:**\n\n(همون پیام خوش‌آمدگویی که کاربرا می‌بینن)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner")
async def get_banner_text(message: types.Message):
    set_banner(message.text)
    user_states[message.from_user.id] = {}
    await message.answer("✅ **بنر ذخیره شد!** 🎉\n\nاگه میخوای ببینی چطوریه، از دکمه «👀 دیدن بنر» استفاده کن.")

# ===== حذف بنر =====
@router.message(lambda m: m.text == "🗑 حذف بنر" and m.from_user.id == ADMIN_ID)
async def delete_banner_cmd(message: types.Message):
    delete_banner()
    await message.answer("✅ **بنر حذف شد!**\n\nدیگه پیام خوش‌آمدگویی پیش‌فرض میاد 😊")

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
        f"📢 **تعداد کانال‌ها:** {len(channels)} تا\n\n"
        f"😊 داری خوب پیش میری! ادامه بده..."
    )

# ===== بقیه کدها (نظرات، سوالات، ارسال همگانی) =====
# ... (همون کدهای قبلی)
