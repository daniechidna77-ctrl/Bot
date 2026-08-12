import schedule
import asyncio
import time
from datetime import datetime
from database import get_all_users
from aiogram import Bot

# ========================================
# ===== تابع ارسال خودکار =====
# ========================================
async def send_scheduled_message(bot, message):
    users = get_all_users()
    success = 0
    for user_id, username, full_name in users:
        try:
            await bot.send_message(user_id, message)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    print(f"✅ پیام زمان‌بندی شده به {success} کاربر ارسال شد!")

# ========================================
# ===== زمان‌بندی =====
# ========================================
def start_scheduler(bot):
    schedule.every().day.at("09:00").do(lambda: asyncio.create_task(
        send_scheduled_message(bot, "📢 **صبح بخیر!**\n\nامروز هم همراه ما باش!")
    ))
    
    schedule.every().day.at("21:00").do(lambda: asyncio.create_task(
        send_scheduled_message(bot, "🌙 **شب بخیر!**\n\nامیدوارم روز خوبی داشته باشی!")
    ))
    
    while True:
        schedule.run_pending()
        time.sleep(60)
