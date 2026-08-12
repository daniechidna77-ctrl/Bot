# ========================================
# ===== کلینر فایل با جیمینای =====
# ========================================
@router.message(lambda m: m.text == "🤖 کلینر فایل" and m.from_user.id == ADMIN_ID)
async def cleaner_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_cleaner"}
    await message.answer(
        "🤖 **کلینر هوشمند فایل**\n\n"
        "فایل (PDF یا عکس) رو بفرست تا:\n"
        "✅ پاک‌سازی کنم\n"
        "✅ کیفیت رو بالا ببرم\n"
        "✅ خلاصه‌سازی با جیمینای"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_cleaner")
async def cleaner_process(message: types.Message):
    file = await message.bot.get_file(message.document.file_id)
    file_path = f"temp_{message.from_user.id}_{message.document.file_name}"
    await message.bot.download_file(file.file_path, file_path)
    
    file_type = get_file_type(file_path)
    cleaned_path = None
    
    if file_type == "pdf":
        await message.answer("🔄 پاک‌سازی PDF...")
        cleaned_path = await clean_pdf(file_path)
        # خلاصه‌سازی با جیمینای
        summary = await summarize_with_gemini(file_path)
        if summary and "خطا" not in summary:
            await message.answer(f"📝 **خلاصه:**\n\n{summary}")
        elif summary:
            await message.answer(f"⚠️ {summary}")
    elif file_type == "image":
        await message.answer("🔄 پاک‌سازی عکس...")
        cleaned_path = await clean_image(file_path)
    else:
        await message.answer("❌ این نوع فایل پشتیبانی نمیشه!")
        os.remove(file_path)
        return
    
    if cleaned_path:
        with open(cleaned_path, "rb") as f:
            await message.answer_document(
                f,
                caption=f"✅ **فایل پاک‌سازی شد!**"
            )
        os.remove(file_path)
        os.remove(cleaned_path)
    else:
        await message.answer("❌ خطا در پاک‌سازی!")

    user_states[message.from_user.id] = {}

# ========================================
# ===== چت با جیمینای (شوخ و بازیگوش) =====
# ========================================
@router.message(lambda m: m.text == "💬 چت با جیمینای" and m.from_user.id == ADMIN_ID)
async def gemini_chat_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_gemini_chat"}
    await message.answer(
        "💬 **با جیمینای حرف بزن!**\n\n"
        "هر چی دوست داری بپرس، جواب میده 😊\n"
        "(برای بستن /cancel بفرست)"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_gemini_chat")
async def gemini_chat_response(message: types.Message):
    if message.text == "/cancel":
        user_states[message.from_user.id] = {}
        await message.answer("✅ چت بسته شد!")
        return
    
    await message.answer("🤔 دارم فکر میکنم...")
    
    response = await gemini_chat(message.text)
    if response and "خطا" not in response:
        await message.answer(response)
    else:
        await message.answer(response or "❌ جیمینای در دسترس نیست!")
