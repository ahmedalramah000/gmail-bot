# 这是正确格式的start函数，请将此代码复制到gmail_bot.py中
async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الرد عند بدء استخدام البوت."""
    user_id = str(update.effective_user.id)
    
    # القائمة الأساسية للجميع
    keyboard = [
        [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")],
        [InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="show_tutorial")]
    ]
    
    # إضافة زر لوحة المسؤول إذا كان المستخدم هو المسؤول
    if ADMIN_CHAT_ID and user_id == ADMIN_CHAT_ID:
        keyboard.append([InlineKeyboardButton("👑 لوحة تحكم المسؤول", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # إزالة التحذير المتعلق بملف بيانات الاعتماد
    message_text = (
        f'مرحبًا! أنا بوت كود ChatGPT\n\n'
        f'اضغط على الزر أدناه للحصول على آخر كود تحقق.\n'
        f'البريد المستخدم: <code>{TARGET_EMAIL}</code>\n'
        f'كلمة المرور: <code>{PASSWORD}</code>\n\n'
        f'<b>📝 طريقة الدخول:</b>\n'
        f'1. اضغط على "try another method" من الأسفل\n'
        f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
        f'3. أدخل الكود الذي ستحصل عليه\n\n'
        f'تمت برمجتي بواسطه احمد الرماح'
    )
    
    await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='HTML') 