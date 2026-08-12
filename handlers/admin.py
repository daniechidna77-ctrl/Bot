from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
from utils.cleaner import clean_pdf, clean_image, get_file_type, summarize_with_gemini, translate_with_gemini
import os
import asyncio

router = Router()
user_states = {}

# ========================================
# ===== پنل ادمین =====
# ========================================
def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="📚 مدیریت چپترها")],
        [KeyboardButton(text="📢 مدیریت کانال‌ها")],
        [KeyboardButton(text="🎨 مدیریت بنر")],
        [KeyboardButton(text="🛒 مدیریت فروشگاه")],
        [KeyboardButton(text="📊 آمار")],
        [KeyboardButton(text="📤 ارسال همگانی")],
        [KeyboardButton(text="🤖 کلینر فایل")],
        [KeyboardButton(text="🎯 تبلیغات")],
        [KeyboardButton(text="❓ سوالات کاربران")],
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
        "از دکمه‌های زیر استفاده کن:",
        reply_markup=get_admin_keyboard()
    )

# ========================================
# ===== بستن پنل =====
# ========================================
@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())

# ========================================
# ===== مدیریت چپترها =====
# ========================================
@router.message(lambda m: m.text == "📚 مدیریت چپترها" and m.from_user.id == ADMIN_ID)
async def manage_chapters(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن چپتر", callback_data="add_chapter")],
        [InlineKeyboardButton(text="📋 لیست چپترها", callback_data="list_chapters")],
        [InlineKeyboardButton(text="🗑 حذف چپتر", callback_data="delete_chapter")],
        [InlineKeyboardButton(text="🔍 جستجو", callback_data="search_chapter")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("📚 **مدیریت چپترها**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_chapter")
async def add_chapter_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_states[call.from_user.id] = {"state": "waiting_code"}
    await call.message.edit_text("📝 **کد چپتر رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_code")
async def get_chapter_code(message: types.Message):
    user_states[message.from_user.id]["code"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_file"
    await message.answer("📄 **حالا فایل رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_file")
async def save_chapter_file(message: types.Message):
    code = user_states[message.from_user.id].get("code")
    if not code:
        return
    
    file_type = "document"
    if message.document.mime_type and message.document.mime_type.startswith("image"):
        file_type = "photo"
    elif message.document.mime_type and message.document.mime_type.startswith("video"):
        file_type = "video"
    
    save_file(code, message.document.file_id, file_type, message.caption or "")
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **چپتر {code} ذخیره شد!**")

@router.callback_query(lambda c: c.data == "list_chapters")
async def list_chapters(call: types.CallbackQuery):
    files = get_all_files()
    if not files:
        await call.message.edit_text("❌ هیچ چپتری ذخیره نشده!")
        return
    text = "📋 **لیست چپترها:**\n\n"
    for code, file_type, caption, downloads in files:
        text += f"• `{code}` ({file_type}) - {downloads} دانلود\n"
    await call.message.edit_text(text)

@router.callback_query(lambda c: c.data == "delete_chapter")
async def delete_chapter_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_delete"}
    await call.message.edit_text("📝 **کد چپتر رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete")
async def delete_chapter_confirm(message: types.Message):
    code = message.text
    if find_file(code):
        delete_file(code)
        await message.answer(f"✅ چپتر {code} حذف شد!")
    else:
        await message.answer(f"❌ چپتر {code} پیدا نشد!")
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "search_chapter")
async def search_chapter_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_search"}
    await call.message.edit_text("🔍 **کد یا کپشن چپتر رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_search")
async def search_chapter_confirm(message: types.Message):
    query = message.text
    results = search_files(query)
    if results:
        text = f"🔍 **نتایج جستجو برای '{query}':**\n\n"
        for code, file_type, caption in results:
            text += f"• `{code}` ({file_type}) - {caption or 'بدون کپشن'}\n"
        await message.answer(text)
    else:
        await message.answer(f"❌ نتیجه‌ای برای '{query}' پیدا نشد!")
    user_states[message.from_user.id] = {}

# ========================================
# ===== مدیریت کانال‌ها =====
# ========================================
@router.message(lambda m: m.text == "📢 مدیریت کانال‌ها" and m.from_user.id == ADMIN_ID)
async def manage_channels(message: types.Message):
    channels = get_channels()
    text = "📢 **لیست کانال‌ها:**\n\n"
    text += "\n".join([f"• @{ch}" for ch in channels]) if channels else "❌ هیچ کانالی وجود نداره!"
    await message.answer(text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن کانال", callback_data="add_channel")],
        [InlineKeyboardButton(text="➖ حذف کانال", callback_data="remove_channel")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("یک گزینه رو انتخاب کن:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_channel")
async def add_channel_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_channel"}
    await call.message.edit_text("📢 **نام کانال رو بفرست (بدون @):**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_channel")
async def add_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")
    add_channel(ch)
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ کانال @{ch} اضافه شد!")

@router.callback_query(lambda c: c.data == "remove_channel")
async def remove_channel_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_remove_channel"}
    await call.message.edit_text("📢 **نام کانال رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_remove_channel")
async def remove_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")
    delete_channel(ch)
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ کانال @{ch} حذف شد!")

# ========================================
# ===== مدیریت بنر =====
# ========================================
@router.message(lambda m: m.text == "🎨 مدیریت بنر" and m.from_user.id == ADMIN_ID)
async def manage_banner(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 تنظیم بنر", callback_data="set_banner")],
        [InlineKeyboardButton(text="🗑 حذف بنر", callback_data="delete_banner")],
        [InlineKeyboardButton(text="👀 دیدن بنر", callback_data="view_banner")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("🎨 **مدیریت بنر**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "set_banner")
async def set_banner_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_banner"}
    await call.message.edit_text(
        "📝 **بنر رو بفرست**\n\n"
        "می‌تونی اینا رو بفرستی:\n"
        "• متن\n"
        "• عکس\n"
        "• ویدیو\n"
        "• فایل"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner")
async def set_banner_confirm(message: types.Message):
    if message.text:
        set_banner("text", None, message.text)
        await message.answer(f"✅ بنر متنی ذخیره شد!")
    elif message.photo:
        set_banner("photo", message.photo[-1].file_id, message.caption or "")
        await message.answer("✅ بنر عکس ذخیره شد!")
    elif message.video:
        set_banner("video", message.video.file_id, message.caption or "")
        await message.answer("✅ بنر ویدیو ذخیره شد!")
    elif message.document:
        set_banner("document", message.document.file_id, message.caption or "")
        await message.answer("✅ بنر فایل ذخیره شد!")
    else:
        await message.answer("❌ نوع فایل پشتیبانی نمیشه!")
        return
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "delete_banner")
async def delete_banner_confirm(call: types.CallbackQuery):
    delete_banner()
    await call.message.edit_text("✅ بنر حذف شد!")

@router.callback_query(lambda c: c.data == "view_banner")
async def view_banner(call: types.CallbackQuery):
    banner = get_banner()
    if banner["type"] == "photo" and banner["file_id"]:
        await call.message.answer_photo(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "video" and banner["file_id"]:
        await call.message.answer_video(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "document" and banner["file_id"]:
        await call.message.answer_document(banner["file_id"], caption=banner["text"])
    else:
        await call.message.edit_text(f"📝 **بنر فعلی:**\n\n{banner['text']}")

# ========================================
# ===== کلینر فایل =====
# ========================================
@router.message(lambda m: m.text == "🤖 کلینر فایل" and m.from_user.id == ADMIN_ID)
async def cleaner_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_cleaner"}
    await message.answer(
        "🤖 **کلینر هوشمند فایل**\n\n"
        "فایل (PDF یا عکس) رو بفرست تا:\n"
        "✅ پاک‌سازی و بهینه‌سازی کنم\n"
        "✅ کیفیت رو بالا ببرم\n"
        "✅ حجم رو کم کنم\n"
        "✅ خلاصه‌سازی با Gemini"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_cleaner")
async def cleaner_process(message: types.Message):
    file = await message.bot.get_file(message.document.file_id)
    file_path = f"temp_{message.from_user.id}_{message.document.file_name}"
    await message.bot.download_file(file.file_path, file_path)
    
    file_type = get_file_type(file_path)
    cleaned_path = None
    
    if file_type == "pdf":
        await message.answer("🔄 در حال پاک‌سازی PDF...")
        cleaned_path = await clean_pdf(file_path)
        # خلاصه‌سازی با Gemini
        summary = await summarize_with_gemini(file_path)
        if summary:
            await message.answer(f"📝 **خلاصه فایل:**\n\n{summary}")
    elif file_type == "image":
        await message.answer("🔄 در حال پاک‌سازی عکس...")
        cleaned_path = await clean_image(file_path)
    else:
        await message.answer("❌ این نوع فایل پشتیبانی نمیشه!")
        os.remove(file_path)
        return
    
    if cleaned_path:
        with open(cleaned_path, "rb") as f:
            await message.answer_document(
                f,
                caption=f"✅ **فایل پاک‌سازی شد!**\n\n📁 {os.path.basename(cleaned_path)}"
            )
        os.remove(file_path)
        os.remove(cleaned_path)
    else:
        await message.answer("❌ خطا در پاک‌سازی فایل!")

    user_states[message.from_user.id] = {}

# ========================================
# ===== آمار =====
# ========================================
@router.message(lambda m: m.text == "📊 آمار" and m.from_user.id == ADMIN_ID)
async def stats(message: types.Message):
    files = get_all_files()
    channels = get_channels()
    users = get_user_count()
    
    await message.answer(
        f"📊 **آمار ربات:**\n\n"
        f"👥 **تعداد کاربران:** {users} نفر\n"
        f"📁 **تعداد چپترها:** {len(files)} تا\n"
        f"📢 **تعداد کانال‌ها:** {len(channels)} تا\n"
        f"📥 **کل دانلودها:** {sum(f[3] for f in files)} بار"
    )

# ========================================
# ===== ارسال همگانی =====
# ========================================
@router.message(lambda m: m.text == "📤 ارسال همگانی" and m.from_user.id == ADMIN_ID)
async def broadcast_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_broadcast"}
    await message.answer("📝 **پیام رو بفرست تا به همه کاربرا ارسال بشه:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_broadcast")
async def broadcast_confirm(message: types.Message):
    users = get_all_users()
    if not users:
        await message.answer("❌ هیچ کاربری وجود نداره!")
        return
    
    await message.answer(f"📤 ارسال به {len(users)} کاربر شروع شد...")
    
    success = 0
    for user_id, username, full_name in users:
        try:
            await message.bot.send_message(user_id, message.text)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    await message.answer(f"✅ پیام به {success} کاربر ارسال شد!")
    user_states[message.from_user.id] = {}

# ========================================
# ===== سوالات کاربران =====
# ========================================
@router.message(lambda m: m.text == "❓ سوالات کاربران" and m.from_user.id == ADMIN_ID)
async def view_questions(message: types.Message):
    questions = get_pending_questions()
    if not questions:
        await message.answer("❌ هیچ سوال بدون پاسخی وجود نداره!")
        return
    
    for q_id, user_id, q, date in questions:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ پاسخ", callback_data=f"answer_q_{q_id}")]
        ])
        await message.answer(
            f"❓ **سوال #{q_id}**\n"
            f"👤 کاربر: `{user_id}`\n"
            f"📅 {date}\n\n"
            f"{q}",
            reply_markup=keyboard
        )

@router.callback_query(lambda c: c.data.startswith("answer_q_"))
async def answer_question_start(call: types.CallbackQuery):
    q_id = int(call.data.replace("answer_q_", ""))
    user_states[call.from_user.id] = {"state": "waiting_answer", "q_id": q_id}
    await call.message.answer("✏️ **پاسخ سوال رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_answer")
async def answer_question_confirm(message: types.Message):
    q_id = user_states[message.from_user.id].get("q_id")
    answer = message.text
    answer_question(q_id, answer)
    user_states[message.from_user.id] = {}
    await message.answer("✅ پاسخ ذخیره شد!")

# ========================================
# ===== تبلیغات =====
# ========================================
@router.message(lambda m: m.text == "🎯 تبلیغات" and m.from_user.id == ADMIN_ID)
async def ads_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن تبلیغ", callback_data="add_ad")],
        [InlineKeyboardButton(text="📋 لیست تبلیغات", callback_data="list_ads")],
        [InlineKeyboardButton(text="🗑 حذف تبلیغ", callback_data="delete_ad")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("🎯 **مدیریت تبلیغات**", reply_markup=keyboard)

# ========================================
# ===== برگشت =====
# ========================================
@router.callback_query(lambda c: c.data == "back_to_panel")
async def back_to_panel(call: types.CallbackQuery):
    await call.message.edit_text(
        "⚙️ **پنل مدیریت**\n\n"
        "از دکمه‌های زیر استفاده کن:",
        reply_markup=get_admin_keyboard()
)
