import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router as user_router
from admin_panel import router as admin_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ثبت روت‌ها
dp.include_router(user_router)
dp.include_router(admin_router)

async def main():
    print("🤖 ربات روشن شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
