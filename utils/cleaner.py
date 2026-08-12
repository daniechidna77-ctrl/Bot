import os
import fitz
from PIL import Image
import io
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
    elif file_path.endswith((".mp4", ".avi", ".mkv")):
        return "video"
    elif file_path.endswith((".zip", ".rar")):
        return "archive"
    else:
        return "other"

# ========================================
# ===== خلاصه‌سازی با Gemini =====
# ========================================
async def summarize_with_gemini(file_path):
    if not GEMINI_API_KEY:
        return None
    
    try:
        # خواندن متن فایل
        if file_path.endswith(".pdf"):
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        else:
            return None
        
        # ارسال به Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"خلاصه زیر را به فارسی بنویس:\n\n{text[:10000]}"
                }]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "خلاصه‌ای پیدا نشد!")
                else:
                    return None
    except Exception as e:
        print(f"❌ خطا در Gemini: {e}")
        return None

# ========================================
# ===== ترجمه با Gemini =====
# ========================================
async def translate_with_gemini(text, target_lang="fa"):
    if not GEMINI_API_KEY:
        return None
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"متن زیر را به {target_lang} ترجمه کن:\n\n{text}"
                }]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "ترجمه‌ای پیدا نشد!")
                else:
                    return None
    except Exception as e:
        print(f"❌ خطا در Gemini: {e}")
        return None
