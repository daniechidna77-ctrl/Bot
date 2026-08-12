import os
import fitz
from PIL import Image
import aiohttp
import json
from config import GEMINI_API_KEY

# ========================================
# ===== کلینر PDF =====
# ========================================
async def clean_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        output_path = file_path.replace(".pdf", "_cleaned.pdf")
        new_doc = fitz.open()
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_text((50, 50), text, fontsize=11)
        
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        return output_path
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

# ========================================
# ===== کلینر عکس =====
# ========================================
async def clean_image(file_path):
    try:
        image = Image.open(file_path)
        if image.width > 2000:
            ratio = 2000 / image.width
            new_size = (2000, int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        output_path = file_path.replace(".jpg", "_cleaned.jpg").replace(".png", "_cleaned.png")
        image.save(output_path, quality=95, optimize=True)
        return output_path
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

# ========================================
# ===== تشخیص نوع فایل =====
# ========================================
def get_file_type(file_path):
    if file_path.endswith(".pdf"):
        return "pdf"
    elif file_path.endswith((".jpg", ".jpeg", ".png", ".gif")):
        return "image"
    else:
        return "other"

# ========================================
# ===== خلاصه‌سازی با جیمینای =====
# ========================================
async def summarize_with_gemini(file_path):
    if not GEMINI_API_KEY:
        return None
    
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"خلاصه زیر رو به فارسی بنویس (حداکثر ۵ خط):\n\n{text[:5000]}"
                }]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return None
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

# ========================================
# ===== چت با جیمینای (شوخ و بازیگوش) =====
# ========================================
async def gemini_chat(text):
    if not GEMINI_API_KEY:
        return "😅 جیمینای در دسترس نیست! کلید API رو تنظیم کن."
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""تو یه دستیار هوشمند هستی با شخصیت شوخ، بازیگوش و صمیمی.
به فارسی پاسخ بده.
پاسخ‌هات کوتاه، جذاب و بدون تکرار باشه.
اگه سوالی خارج از حوزت بود، با شوخی جواب بده.

سوال: {text}
"""
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return reply
                return "😅 یه مشکلی پیش اومده! بعداً دوباره امتحان کن."
    except Exception as e:
        print(f"❌ خطا: {e}")
        return "😅 نتونستم جواب بدم! شاید نت یا کلید جیمینای مشکل داره."
