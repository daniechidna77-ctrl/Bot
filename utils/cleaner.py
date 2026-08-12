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
        print(f"❌ خطا در کلینر PDF: {e}")
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
        print(f"❌ خطا در کلینر عکس: {e}")
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
        return "❌ کلید جیمینای تنظیم نشده!"
    
    try:
        # استخراج متن از PDF
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        if len(text) < 50:
            return "📝 متن کافی برای خلاصه‌سازی وجود ندارد!"
        
        # ارسال به جیمینای
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"خلاصه زیر رو به فارسی بنویس (حداکثر ۵ خط):\n\n{text[:5000]}"
                }]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return result if result else "❌ خلاصه‌ای پیدا نشد!"
                else:
                    return f"❌ خطا از جیمینای: {response.status}"
    except Exception as e:
        return f"❌ خطا: {str(e)[:100]}"

# ========================================
# ===== چت با جیمینای =====
# ========================================
async def gemini_chat(text):
    if not GEMINI_API_KEY:
        return "❌ کلید جیمینای تنظیم نشده!"
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""تو یه دستیار هوشمند هستی با شخصیت شوخ و بازیگوش.
به فارسی پاسخ بده.
پاسخ‌هات کوتاه و جذاب باشه.

سوال: {text}
"""
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return reply if reply else "❌ جوابی پیدا نشد!"
                else:
                    return f"❌ خطا از جیمینای: {response.status}"
    except Exception as e:
        return f"❌ خطا: {str(e)[:100]}"
