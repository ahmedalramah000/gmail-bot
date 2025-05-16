#!/usr/bin/env python3
"""
بوت تليجرام بسيط - يقوم بحفظ وعرض أكواد التحقق من OpenAI
"""

import asyncio
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import re
import logging
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# تهيئة التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تحميل متغيرات البيئة
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')  # معرف المدير
TARGET_EMAIL = "ahmedalramah000@gmail.com"  # البريد الإلكتروني الهدف

# ملف تخزين الأكواد
CODES_FILE = "openai_codes.json"

# التأكد من وجود ملف الأكواد
def ensure_codes_file():
    if not os.path.exists(CODES_FILE):
        with open(CODES_FILE, 'w') as f:
            json.dump({"codes": []}, f)

# قراءة الأكواد المحفوظة
def read_codes():
    ensure_codes_file()
    try:
        with open(CODES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"خطأ في قراءة الأكواد: {e}")
        return {"codes": []}

# حفظ كود جديد
def save_code(code, sender_name="غير معروف", manual_input=False):
    data = read_codes()
    data["codes"].append({
        "code": code,
        "timestamp": datetime.now().isoformat(),
        "sender": sender_name,
        "manual_input": manual_input
    })
    
    # الاحتفاظ بآخر 20 كود فقط
    if len(data["codes"]) > 20:
        data["codes"] = data["codes"][-20:]
    
    try:
        with open(CODES_FILE, 'w') as f:
            json.dump(data, f, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"خطأ في حفظ الكود: {e}")
        return False

# استخراج الأكواد من النص
def extract_code(text):
    # البحث عن أرقام مكونة من 6 أرقام (كود التحقق النموذجي)
    code_match = re.search(r'\b(\d{6})\b', text)
    if code_match:
        return code_match.group(1)
    return None

# التحقق ما إذا كان النص يحتوي على بريد إلكتروني OpenAI
def is_openai_email(text):
    if TARGET_EMAIL.lower() in text.lower():
        return True
    
    # كلمات دالة على أن الرسالة من OpenAI
    openai_keywords = ["openai", "code", "verification", "login", "sign in", "تحقق", "رمز", "كود", "تسجيل الدخول"]
    
    for keyword in openai_keywords:
        if keyword.lower() in text.lower():
            return True
    
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الرد عند بدء استخدام البوت"""
    keyboard = [
        [InlineKeyboardButton("🔑 عرض آخر كود", callback_data="get_last_code")],
        [InlineKeyboardButton("📋 عرض آخر 5 أكواد", callback_data="get_recent_codes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f'مرحبًا! أنا بوت أكواد OpenAI.\n\n'
        f'- أرسل لي نص البريد الإلكتروني الذي يحتوي على كود OpenAI\n'
        f'- أو أرسل الكود مباشرة (6 أرقام)\n'
        f'- استخدم الأزرار أدناه لعرض آخر كود',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة المساعدة"""
    keyboard = [
        [InlineKeyboardButton("🔑 عرض آخر كود", callback_data="get_last_code")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'استخدم هذا البوت لإدارة أكواد OpenAI.\n\n'
        '- أرسل نص البريد الإلكتروني كاملاً لاستخراج الكود\n'
        '- أو أرسل الكود مباشرة (6 أرقام)\n'
        '- اضغط على الزر أدناه لعرض آخر كود تم استلامه',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع نقرات الأزرار"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_last_code":
        # عرض آخر كود
        data = read_codes()
        if data["codes"]:
            last_code = data["codes"][-1]
            timestamp = datetime.fromisoformat(last_code["timestamp"])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            message = (
                f"📬 <b>آخر كود OpenAI</b>\n\n"
                f"🔑 <code>{last_code['code']}</code>\n\n"
                f"⏰ الوقت: {time_str}"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="get_last_code")],
                [InlineKeyboardButton("📋 عرض آخر 5 أكواد", callback_data="get_recent_codes")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await query.edit_message_text("لا توجد أكواد محفوظة حتى الآن.")
    
    elif query.data == "get_recent_codes":
        # عرض آخر 5 أكواد
        data = read_codes()
        if data["codes"]:
            recent_codes = data["codes"][-5:]
            recent_codes.reverse()  # عرض الأحدث أولاً
            
            message = "<b>📋 آخر 5 أكواد OpenAI:</b>\n\n"
            
            for i, code_data in enumerate(recent_codes):
                timestamp = datetime.fromisoformat(code_data["timestamp"])
                time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                message += f"{i+1}. <code>{code_data['code']}</code> - ⏰ {time_str}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="get_recent_codes")],
                [InlineKeyboardButton("🔑 عرض آخر كود فقط", callback_data="get_last_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await query.edit_message_text("لا توجد أكواد محفوظة حتى الآن.")

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل الواردة واستخراج الأكواد"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text
    
    # محاولة استخراج الكود
    code = extract_code(text)
    
    # التحقق مما إذا كانت الرسالة تبدو كبريد من OpenAI
    is_email = is_openai_email(text)
    
    keyboard = [
        [InlineKeyboardButton("🔑 عرض آخر كود", callback_data="get_last_code")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if code:
        # حفظ الكود
        manual_input = not is_email  # إذا لم يكن بريد إلكتروني، فهو إدخال يدوي
        save_code(code, user_name, manual_input)
        
        # تأكيد استلام الكود للمستخدم
        await update.message.reply_text(
            f"✅ تم استلام وحفظ الكود: <code>{code}</code>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # إعادة توجيه الكود إلى المدير إذا لزم الأمر
        if ADMIN_CHAT_ID and str(user_id) != ADMIN_CHAT_ID:
            admin_message = (
                f"📬 <b>تم استلام كود جديد</b>\n\n"
                f"🔑 <code>{code}</code>\n\n"
                f"📨 من المستخدم: {user_name} (ID: {user_id})"
            )
            
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=admin_message,
                    parse_mode='HTML'
                )
                logger.info(f"تم إرسال الكود {code} إلى المدير")
            except Exception as e:
                logger.error(f"خطأ في إرسال الرسالة إلى المدير: {e}")
    else:
        await update.message.reply_text(
            "لم يتم العثور على أي كود في رسالتك. الرجاء إرسال رسالة تحتوي على كود مكون من 6 أرقام.",
            reply_markup=reply_markup
        )

def main() -> None:
    """تشغيل البوت"""
    # التحقق من وجود توكن البوت
    if not TELEGRAM_BOT_TOKEN:
        logger.error("لم يتم تعيين TELEGRAM_BOT_TOKEN. قم بإضافته إلى ملف .env")
        return
    
    # التأكد من وجود ملف الأكواد
    ensure_codes_file()

    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    # بدء البوت
    logger.info("بدء تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 