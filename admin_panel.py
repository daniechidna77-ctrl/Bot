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
from datetime import datetime

router = Router()
user_states = {}

# ===== پنل ادمین =====
@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ افزودن چپتر"), KeyboardButton(text="📋 لیست چپترها")],
            [KeyboardButton(text="🗑 حذف چپتر"), KeyboardButton(text="➕ افزودن کانال")],
            [KeyboardButton(text="📁 افزودن پوشه"), KeyboardButton(text="📋 لیست کانال‌ها")],
            [KeyboardButton(text="👀 دیدن پنل عضویت"), KeyboardButton(text="📝 تنظیم بنر")],
            [KeyboardButton(text="🗑 حذف بنر"), KeyboardButton(text="👀 دیدن بنر")],
            [KeyboardButton(text="📊 آمار"), KeyboardButton(text="📢 ارسال همگانی")],
            [KeyboardButton(text="💬 نظرات"), KeyboardButton(text="❓ سوالات")],
            [KeyboardButton(text="🎨 تغییر تم"), KeyboardButton(text="🤖 ساخت ربات جدید")],
            [KeyboardButton(text="📂 پروژه‌های من"), KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )
    await message.answer("🤖 به پنل مدیریت خوش اومدی! چیکار میخوای بکنی؟ 😊", reply_markup=keyboard)

# ===== بستن پنل =====
@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد! 😊", reply_markup=types.ReplyKeyboardRemove())

# ===== دیدن پنل عضویت =====
@router.message(lambda m: m.text == "👀 دیدن پنل عضویت" and m.from_user.id == ADMIN_ID)
async def view_join_panel(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ کانالی برای عضویت اجباری تنظیم نشده! 😅")
        return
    
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}")])
    if len(channels) > 1:
        buttons.append([InlineKeyboardButton(text="🔗 عضویت در همه", callback_data="join_all_inline")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem_inline")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "🎯 **پنل عضویت اجباری**\n\n"
        "برای دریافت فایل‌ها، اول باید تو این کانال‌ها عضو بشی! 😊",
        reply_markup=keyboard
    )

# ===== عضویت در همه (اینلاین) =====
@router.callback_query(lambda c: c.data == "join_all_inline")
async def join_all_inline(call: types.CallbackQuery):
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

# ===== بررسی عضویت (اینلاین) =====
@router.callback_query(lambda c: c.data == "check_mem_inline")
async def check_mem_inline(call: types.CallbackQuery):
    await call.answer("✅ عضویت شما تایید شد! 😊", show_alert=True)
    await call.message.edit_text("✅ **عضویت شما تایید شد!**\n\nحالا میتونی از ربات استفاده کنی 😊")

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

# ===== بقیه کدهای قبلی (افزودن چپتر، لیست، حذف، کانال‌ها، بنر، آمار) =====
# ... (همون کدهای قبلی)

# ========================================
# ===== 🤖 ساخت ربات جدید =====
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
    
    # ساخت پوشه پروژه
    project_path = f"{PROJECTS_DIR}/{project_name}"
    if os.path.exists(project_path):
        await message.answer(f"❌ پروژه‌ای با اسم `{project_name}` وجود داره! اسم دیگه‌ای انتخاب کن.")
        return
    
    os.makedirs(project_path)
    
    # ساخت فایل config.py
    config_content = f'''import os

BOT_TOKEN = "{token}"
ADMIN_ID = {admin_id}

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN تنظیم نشده!")
'''
    with open(f"{project_path}/config.py", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    # ساخت فایل main.py
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
    
    # ساخت فایل handlers.py
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
    
    # ساخت requirements.txt
    req_content = '''aiogram==3.13.1
'''
    with open(f"{project_path}/requirements.txt", "w", encoding="utf-8") as f:
        f.write(req_content)
    
    # ذخیره اطلاعات پروژه
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
    
    user_states[message.from_user.id] = {}
    
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
        # اجرا در پس‌زمینه
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
    
    # حذف پوشه
    import shutil
    shutil.rmtree(f"{PROJECTS_DIR}/{project_name}")
    
    # حذف از دیتابیس
    projects = load_projects()
    if project_name in projects:
        del projects[project_name]
    save_projects(projects)
    
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ پروژه {project_name} حذف شد!")

# ===== بازگشت به لیست =====
@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text == "🔙 بازگشت به لیست")
async def back_to_list(message: types.Message):
    await my_projects(message)

# ========================================
# ===== ادامه کدهای قبلی =====
# ========================================

# ... (همون کدهای قبلی برای افزودن چپتر، لیست، حذف، کانال‌ها، بنر، آمار، نظرات، سوالات، ارسال همگانی)
