import aiohttp
import json
from config import ZARINPAL_MERCHANT

# ========================================
# ===== اتصال به زرین‌پال =====
# ========================================
async def create_payment(amount, description, user_id):
    if not ZARINPAL_MERCHANT:
        return None
    
    try:
        url = "https://api.zarinpal.com/pg/v4/payment/request.json"
        payload = {
            "merchant_id": ZARINPAL_MERCHANT,
            "amount": amount,
            "description": description,
            "callback_url": f"https://your-bot-url.com/callback",
            "metadata": {
                "user_id": str(user_id)
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("authority")
                else:
                    return None
    except Exception as e:
        print(f"❌ خطا در زرین‌پال: {e}")
        return None

# ========================================
# ===== تایید پرداخت =====
# ========================================
async def verify_payment(authority, amount):
    if not ZARINPAL_MERCHANT:
        return None
    
    try:
        url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
        payload = {
            "merchant_id": ZARINPAL_MERCHANT,
            "authority": authority,
            "amount": amount
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("ref_id")
                else:
                    return None
    except Exception as e:
        print(f"❌ خطا در تایید پرداخت: {e}")
        return None
