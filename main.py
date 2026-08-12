import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN, ADMIN_ID
from handlers import user, admin, shop, ai, channels
from utils import scheduler

# ===== لاگینگ =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ===== ربات =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== ثبت روت‌ها =====
dp.include_router(user.router)
dp.include_router(admin.router)
dp.include_router(shop.router)
dp.include_router(ai.router)
dp.include_router(channels.router)

# ===== دستورات ربات =====
async def set_commands():
    commands = [
        BotCommand(command="start", description="🚀 شروع ربات"),
        BotCommand(command="panel", description="⚙️ پنل مدیریت"),
        BotCommand(command="menu", description="📋 منوی کاربر"),
        BotCommand(command="shop", description="🛒 فروشگاه"),
        BotCommand(command="help", description="📖 راهنما"),
    ]
    await bot.set_my_commands(commands)

# ===== اجرا =====
async def main():
    await set_commands()
    logger.info("🤖 ربات روشن شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
