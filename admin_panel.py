from aiogram import Router, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import *
import asyncio

router = Router()
user_states = {}

# ===== پنل ادمین =====
@router.message(lambda m: m.text == "⚙️ پنل مدیریت" or m.text == "/panel")
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ افزودن چپتر"), KeyboardButton(text="📋 لیست چپترها")],
            [KeyboardButton(text="🗑 حذف چپتر"), KeyboardButton(text="➕ افزودن کانال")],
            [KeyboardButton(text="➖ حذف کانال"), KeyboardButton(text="📋 لیست کانال‌ها")],
            [KeyboardButton(text="📝 تنظیم بنر"), KeyboardButton(text="🗑 حذف بنر")],
            [KeyboardButton(text="📊 آمار"), KeyboardButton(text="📢 ارسال همگانی")],
            [KeyboardButton(text="💬 نظرات"), KeyboardButton(text="❓ سوالات")],
            [KeyboardButton(text="🎨 تغییر تم پیش‌فرض"), KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    await message.answer("⚙️ پنل مدیریت:", reply_markup=keyboard)

# ===== بستن پنل =====
@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())

# ===== افزودن چپتر =====
@router.message(lambda m: m.text == "➕ افزودن چپتر" and m.from_user.id == ADMIN_ID)
async def add_file_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_code"}
    await message.answer("📝 کد چپتر رو بفرست:\nمثال: 1_2")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_code")
async def get_code(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_file", "code": message.text.strip()}
    await message.answer("📄 حالا فایل رو ارسال کن (PDF, ZIP, عکس, ویدیو):")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document)
async def get_file(message: types.Message):
    state = user_states.get(message.from_user.id, {})
    if state.get("state") != "waiting_file":
        return
    code = state.get("code")
    if not code:
        return
    
    # تشخیص نوع فایل
    file_type = "document"
    if message.document.mime_type == "application/pdf":
        file_type = "document"
    elif message.document.mime_type and message.document.mime_type.startswith("image"):
        file_type = "photo"
    elif message.document.mime_type and message.document.mime_type.startswith("video"):
        file_type = "video"
    
    save_file(code, message.document.file_id, file_type)
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ چپتر {code} ذخیره شد! (نوع: {file_type})")

# ===== لیست چپترها =====
@router.message(lambda m: m.text == "📋 لیست چپترها" and m.from_user.id == ADMIN_ID)
async def list_files(message: types.Message):
    files = get_all_files()
    if not files:
        await message.answer("❌ هیچ چپتری ذخیره نشده!")
        return
    text = "📋 لیست چپترها:\n" + "\n".join([f"• {code} ({type})" for code, type in files])
    await message.answer(text)

# ===== حذف چپتر =====
@router.message(lambda m: m.text == "🗑 حذف چپتر" and m.from_user.id == ADMIN_ID)
async def delete_file_start(message: types.Message):
    files = get_all_files()
    if not files:
        await message.answer("❌ هیچ چپتری وجود نداره!")
        return
    user_states[message.from_user.id] = {"state": "waiting_delete"}
    await message.answer("📝 کد چپتر رو برای حذف بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete")
async def delete_file_confirm(message: types.Message):
    code = message.text.strip()
    if find_file(code):
        delete_file(code)
        await message.answer(f"✅ چپتر {code} حذف شد!")
    else:
        await message.answer(f"❌ چپتر {code} پیدا نشد!")
    user_states[message.from_user.id] = {}

# ===== افزودن کانال =====
@router.message(lambda m: m.text == "➕ افزودن کانال" and m.from_user.id == ADMIN_ID)
async def add_channel_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_channel"}
    await message.answer("📢 نام کاربری کانال رو بفرست (بدون @):")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_channel")
async def get_channel(message: types.Message):
    ch = message.text.strip().replace("@", "")
    add_channel(ch)
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ کانال @{ch} اضافه شد!")

# ===== حذف کانال =====
@router.message(lambda m: m.text == "➖ حذف کانال" and m.from_user.id == ADMIN_ID)
async def delete_channel_start(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی وجود نداره!")
        return
    user_states[message.from_user.id] = {"state": "waiting_del_channel"}
    await message.answer("📝 نام کاربری کانال رو برای حذف بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_del_channel")
async def delete_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")
    delete_channel(ch)
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ کانال @{ch} حذف شد!")

# ===== لیست کانال‌ها =====
@router.message(lambda m: m.text == "📋 لیست کانال‌ها" and m.from_user.id == ADMIN_ID)
async def list_channels(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی ثبت نشده!")
        return
    await message.answer("📋 لیست کانال‌ها:\n" + "\n".join([f"• @{ch}" for ch in channels]))

# ===== تنظیم بنر =====
@router.message(lambda m: m.text == "📝 تنظیم بنر" and m.from_user.id == ADMIN_ID)
async def set_banner_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_banner"}
    await message.answer("📝 متن بنر جدید رو بفرست:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner")
async def get_banner_text(message: types.Message):
    set_banner(message.text)
    user_states[message.from_user.id] = {}
    await message.answer("✅ بنر ذخیره شد!")

# ===== حذف بنر =====
@router.message(lambda m: m.text == "🗑 حذف بنر" and m.from_user.id == ADMIN_ID)
async def delete_banner_cmd(message: types.Message):
    delete_banner()
    await message.answer("✅ بنر حذف شد! بنر پیش‌فرض فعال شد.")

# ===== آمار =====
@router.message(lambda m: m.text == "📊 آمار" and m.from_user.id == ADMIN_ID)
async def stats(message: types.Message):
    files = get_all_files()
    channels = get_channels()
    users = get_user_count()
    await message.answer(
        f"📊 آمار ربات:\n\n"
        f"👥 تعداد کاربران: {users}\n"
        f"📁 تعداد چپترها: {len(files)}\n"
        f"📢 تعداد کانال‌ها: {len(channels)}"
    )

# ===== نظرات =====
@router.message(lambda m: m.text == "💬 نظرات" and m.from_user.id == ADMIN_ID)
async def view_feedback(message: types.Message):
    feedbacks = get_all_feedback()
    if not feedbacks:
        await message.answer("❌ نظری ثبت نشده!")
        return
    
    text = "💬 لیست نظرات:\n\n"
    for id, user_id, msg, date in feedbacks[:10]:  # 10 تا آخرین
        text += f"#{id} | کاربر {user_id}\n{msg}\n{date}\n---\n"
    
    if len(feedbacks) > 10:
        text += f"\n... و {len(feedbacks) - 10} نظر دیگه"
    
    await message.answer(text)

# ===== سوالات =====
@router.message(lambda m: m.text == "❓ سوالات" and m.from_user.id == ADMIN_ID)
async def view_questions(message: types.Message):
    questions = get_pending_questions()
    if not questions:
        await message.answer("❌ سوال بدون پاسخی وجود نداره!")
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
    answer_question(question_id, answer)
    user_states[message.from_user.id] = {}
    await message.answer("✅ پاسخ ذخیره شد!")

# ===== ارسال همگانی =====
@router.message(lambda m: m.text == "📢 ارسال همگانی" and m.from_user.id == ADMIN_ID)
async def broadcast_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_broadcast"}
    await message.answer("📝 پیام رو بفرست تا به همه کاربرا برسه:")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_broadcast")
async def send_broadcast(message: types.Message):
    users = get_all_users()
    if not users:
        await message.answer("❌ کاربری وجود نداره!")
        return
    
    user_states[message.from_user.id] = {}
    await message.answer(f"📤 ارسال به {len(users)} کاربر شروع شد...")
    
    success = 0
    for user_id in users:
        try:
            await message.bot.send_message(user_id, message.text)
            success += 1
            await asyncio.sleep(0.05)  # جلوگیری از محدودیت
        except:
            pass
    
    await message.answer(f"✅ پیام به {success} کاربر ارسال شد!")

# ===== تغییر تم پیش‌فرض =====
@router.message(lambda m: m.text == "🎨 تغییر تم پیش‌فرض" and m.from_user.id == ADMIN_ID)
async def change_default_theme(message: types.Message):
    # اینجا می‌تونی تم پیش‌فرض رو تغییر بدی
    await message.answer("🎨 تم پیش‌فرض برای کاربران جدید:\nلطفاً انتخاب کن:\n☀️ روز\n🌙 شب", 
                        reply_markup=types.ReplyKeyboardMarkup(
                            keyboard=[
                                [KeyboardButton(text="☀️ روز"), KeyboardButton(text="🌙 شب")],
                                [KeyboardButton(text="🔙 بستن پنل")]
                            ],
                            resize_keyboard=True
                        ))
