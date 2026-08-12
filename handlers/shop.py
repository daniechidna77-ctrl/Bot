from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
import json

router = Router()

# ========================================
# ===== فروشگاه =====
# ========================================
@router.message(Command("shop"))
async def shop(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 اشتراک یک ماهه", callback_data="buy_1month")],
        [InlineKeyboardButton(text="📦 اشتراک سه ماهه", callback_data="buy_3month")],
        [InlineKeyboardButton(text="📦 اشتراک شش ماهه", callback_data="buy_6month")],
        [InlineKeyboardButton(text="🎫 کد تخفیف", callback_data="coupon")],
        [InlineKeyboardButton(text="📋 وضعیت اشتراک", callback_data="my_subscription")]
    ])
    await message.answer(
        "🛒 **فروشگاه ربات**\n\n"
        "طرح‌های اشتراک رو انتخاب کن:",
        reply_markup=keyboard
    )

# ========================================
# ===== خرید اشتراک =====
# ========================================
@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_subscription(call: types.CallbackQuery):
    plan = call.data.replace("buy_", "")
    
    plans = {
        "1month": {"name": "یک ماهه", "price": 50000, "days": 30},
        "3month": {"name": "سه ماهه", "price": 120000, "days": 90},
        "6month": {"name": "شش ماهه", "price": 200000, "days": 180},
    }
    
    if plan not in plans:
        await call.answer("❌ طرح نامعتبر!", show_alert=True)
        return
    
    plan_info = plans[plan]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 پرداخت", callback_data=f"pay_{plan}")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_shop")]
    ])
    
    await call.message.edit_text(
        f"📦 **{plan_info['name']}**\n\n"
        f"💰 قیمت: {plan_info['price']:,} ریال\n"
        f"⏰ مدت: {plan_info['days']} روز\n\n"
        f"برای خرید روی دکمه پرداخت کلیک کن.",
        reply_markup=keyboard
    )

# ========================================
# ===== پرداخت =====
# ========================================
@router.callback_query(lambda c: c.data.startswith("pay_"))
async def payment(call: types.CallbackQuery):
    plan = call.data.replace("pay_", "")
    
    plans = {
        "1month": {"name": "یک ماهه", "price": 50000, "days": 30},
        "3month": {"name": "سه ماهه", "price": 120000, "days": 90},
        "6month": {"name": "شش ماهه", "price": 200000, "days": 180},
    }
    
    if plan not in plans:
        await call.answer("❌ خطا!", show_alert=True)
        return
    
    plan_info = plans[plan]
    
    # ایجاد تراکنش
    c.execute("""
        INSERT INTO transactions (user_id, amount, description, status)
        VALUES (?, ?, ?, ?)
    """, (call.from_user.id, plan_info["price"], f"خرید اشتراک {plan_info['name']}", "pending"))
    db.commit()
    
    await call.message.edit_text(
        f"💰 **پرداخت اشتراک {plan_info['name']}**\n\n"
        f"مبلغ: {plan_info['price']:,} ریال\n\n"
        f"🔗 لینک پرداخت:\n"
        f"(در حال توسعه...)"
    )

# ========================================
# ===== وضعیت اشتراک =====
# ========================================
@router.callback_query(lambda c: c.data == "my_subscription")
async def my_subscription(call: types.CallbackQuery):
    sub = get_user_subscription(call.from_user.id)
    if sub:
        plan, end_date = sub
        await call.message.edit_text(
            f"✅ **وضعیت اشتراک شما:**\n\n"
            f"📦 طرح: {plan}\n"
            f"⏰ تا تاریخ: {end_date}\n\n"
            f"✅ فعال"
        )
    else:
        await call.message.edit_text(
            "❌ **شما اشتراک فعالی ندارید!**\n\n"
            "از فروشگاه یک طرح تهیه کن."
        )

# ========================================
# ===== برگشت =====
# ========================================
@router.callback_query(lambda c: c.data == "back_shop")
async def back_shop(call: types.CallbackQuery):
    await shop(call.message)
