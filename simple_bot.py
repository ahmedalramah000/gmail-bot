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
PASSWORD = "0001A@hmEd_Ram4h!"  # كلمة المرور للمسؤول

# نص تعليمات الدخول
LOGIN_INSTRUCTIONS = (
    "🔹 عند تسجيل الدخول إلى ChatGPT استخدم 'Try another method' ثم اختر 'Email' "
    "لإرسال كود التحقق عبر البريد الإلكتروني بدلاً من المصادقة الثنائية"
)

# ملف تخزين الأكواد
CODES_FILE = "openai_codes.json"
# ملف تخزين معلومات الفيديو التعليمي
TUTORIAL_VIDEO_INFO = "tutorial_video_info.json"

# التأكد من وجود ملف معلومات الفيديو
def ensure_tutorial_video_file():
    if not os.path.exists(TUTORIAL_VIDEO_INFO):
        with open(TUTORIAL_VIDEO_INFO, 'w') as f:
            json.dump({"file_id": None}, f)

# قراءة معلومات الفيديو التعليمي
def read_tutorial_video_info():
    ensure_tutorial_video_file()
    try:
        with open(TUTORIAL_VIDEO_INFO, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"خطأ في قراءة معلومات الفيديو: {e}")
        return {"file_id": None}

# حفظ معلومات الفيديو التعليمي
def save_tutorial_video_info(file_id):
    data = {"file_id": file_id}
    try:
        with open(TUTORIAL_VIDEO_INFO, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"خطأ في حفظ معلومات الفيديو: {e}")
        return False

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

# التحقق من صلاحيات المسؤول
def is_admin(user_id):
    return ADMIN_CHAT_ID and str(user_id) == ADMIN_CHAT_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الرد عند بدء استخدام البوت"""
    user_id = update.effective_user.id
    
    # إضافة أزرار إضافية للمسؤول
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("🔑 عرض آخر كود", callback_data="get_last_code")],
            [InlineKeyboardButton("📋 عرض آخر 5 أكواد", callback_data="get_recent_codes")],
            [InlineKeyboardButton("👨‍💼 لوحة المسؤول", callback_data="admin_panel")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🔑 عرض آخر كود", callback_data="get_last_code")],
            [InlineKeyboardButton("📋 عرض آخر 5 أكواد", callback_data="get_recent_codes")]
        ]
        
        # إضافة زر الفيديو التعليمي إذا كان متاحًا
        video_info = read_tutorial_video_info()
        if video_info["file_id"]:
            keyboard.append([InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="view_tutorial")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f'مرحبًا! أنا بوت أكواد OpenAI.\n\n'
        f'- أرسل لي نص البريد الإلكتروني الذي يحتوي على كود OpenAI\n'
        f'- أو أرسل الكود مباشرة (6 أرقام)\n'
        f'- استخدم الأزرار أدناه لعرض آخر كود\n\n'
        f'{LOGIN_INSTRUCTIONS}\n\n'
        f'تمت برمجتي بواسطه احمد الرماح',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة المساعدة"""
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("🔑 عرض آخر كود", callback_data="get_last_code")],
            [InlineKeyboardButton("👨‍💼 لوحة المسؤول", callback_data="admin_panel")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🔑 عرض آخر كود", callback_data="get_last_code")]
        ]
        
        # إضافة زر الفيديو التعليمي إذا كان متاحًا
        video_info = read_tutorial_video_info()
        if video_info["file_id"]:
            keyboard.append([InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="view_tutorial")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'استخدم هذا البوت لإدارة أكواد OpenAI.\n\n'
        '- أرسل نص البريد الإلكتروني كاملاً لاستخراج الكود\n'
        '- أو أرسل الكود مباشرة (6 أرقام)\n'
        '- اضغط على الزر أدناه لعرض آخر كود تم استلامه\n\n'
        f'{LOGIN_INSTRUCTIONS}\n\n'
        'تمت برمجتي بواسطه احمد الرماح',
        reply_markup=reply_markup
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض لوحة تحكم المسؤول"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.answer("غير مصرح لك بالوصول إلى لوحة المسؤول", show_alert=True)
        return
    
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📤 رفع فيديو تعليمي", callback_data="upload_tutorial")],
        [InlineKeyboardButton("👁 عرض الفيديو التعليمي", callback_data="view_tutorial_admin")],
        [InlineKeyboardButton("🗑 حذف الفيديو التعليمي", callback_data="delete_tutorial")],
        [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👨‍💼 <b>لوحة تحكم المسؤول</b>\n\n"
        "اختر إحدى العمليات أدناه:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أوامر المسؤول"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    if not is_admin(user_id):
        await query.answer("غير مصرح لك بالوصول إلى هذه الوظيفة", show_alert=True)
        return
    
    await query.answer()
    
    if data == "upload_tutorial":
        # طلب تحميل فيديو تعليمي
        context.user_data["waiting_for_tutorial"] = True
        
        await query.edit_message_text(
            "📤 <b>رفع فيديو تعليمي</b>\n\n"
            "يرجى إرسال الفيديو التعليمي الآن.\n"
            "يجب أن يكون الفيديو بتنسيق .mp4 أو .mov\n\n"
            "اضغط على زر العودة للإلغاء.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="admin_panel")]])
        )
    
    elif data == "view_tutorial_admin":
        # عرض الفيديو التعليمي (للمسؤول)
        video_info = read_tutorial_video_info()
        if video_info["file_id"]:
            await context.bot.send_video(
                chat_id=user_id,
                video=video_info["file_id"],
                caption="🎬 الفيديو التعليمي الحالي"
            )
            
            await query.edit_message_text(
                "✅ تم إرسال الفيديو التعليمي.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="admin_panel")]])
            )
        else:
            await query.edit_message_text(
                "❌ لم يتم العثور على فيديو تعليمي. يرجى رفع فيديو أولاً.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="admin_panel")]])
            )
    
    elif data == "delete_tutorial":
        # حذف الفيديو التعليمي
        save_tutorial_video_info(None)
        
        await query.edit_message_text(
            "✅ تم حذف الفيديو التعليمي بنجاح.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="admin_panel")]])
        )
    
    elif data == "back_to_main":
        # العودة إلى القائمة الرئيسية
        await start(update, context)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع نقرات الأزرار"""
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # معالجة أوامر المسؤول
    if data in ["admin_panel", "upload_tutorial", "view_tutorial_admin", "delete_tutorial", "back_to_main"]:
        await handle_admin_commands(update, context)
        return
    
    await query.answer()
    
    if data == "get_last_code":
        # عرض آخر كود
        data = read_codes()
        if data["codes"]:
            last_code = data["codes"][-1]
            timestamp = datetime.fromisoformat(last_code["timestamp"])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            message = (
                f"📬 <b>آخر كود OpenAI</b>\n\n"
                f"🔑 <code>{last_code['code']}</code>\n\n"
                f"⏰ الوقت: {time_str}\n\n"
                f"{LOGIN_INSTRUCTIONS}\n\n"
                f"تمت برمجتي بواسطه احمد الرماح"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="get_last_code")],
                [InlineKeyboardButton("📋 عرض آخر 5 أكواد", callback_data="get_recent_codes")]
            ]
            
            # إضافة زر الفيديو التعليمي إذا كان متاحًا
            video_info = read_tutorial_video_info()
            if video_info["file_id"]:
                keyboard.append([InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="view_tutorial")])
            
            if is_admin(user_id):
                keyboard.append([InlineKeyboardButton("👨‍💼 لوحة المسؤول", callback_data="admin_panel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await query.edit_message_text("لا توجد أكواد محفوظة حتى الآن.")
    
    elif data == "get_recent_codes":
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
            
            message += f"{LOGIN_INSTRUCTIONS}\n\n"
            message += "تمت برمجتي بواسطه احمد الرماح"
            
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="get_recent_codes")],
                [InlineKeyboardButton("🔑 عرض آخر كود فقط", callback_data="get_last_code")]
            ]
            
            # إضافة زر الفيديو التعليمي إذا كان متاحًا
            video_info = read_tutorial_video_info()
            if video_info["file_id"]:
                keyboard.append([InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="view_tutorial")])
            
            if is_admin(user_id):
                keyboard.append([InlineKeyboardButton("👨‍💼 لوحة المسؤول", callback_data="admin_panel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await query.edit_message_text("لا توجد أكواد محفوظة حتى الآن.")
    
    elif data == "view_tutorial":
        # عرض الفيديو التعليمي للمستخدم
        video_info = read_tutorial_video_info()
        if video_info["file_id"]:
            await context.bot.send_video(
                chat_id=user_id,
                video=video_info["file_id"],
                caption=f"🎬 شرح طريقة تسجيل الدخول إلى ChatGPT\n\n"
                        f"📧 البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
                        f"🔒 كلمة المرور: <code>{PASSWORD}</code>\n\n"
                        f"<b>طريقة الدخول:</b>\n"
                        f"1. اضغط على 'Try another method' من الأسفل\n"
                        f"2. اختر البريد الإلكتروني (الخيار الثالث)\n"
                        f"3. أدخل الكود الذي تحصل عليه من البوت\n\n"
                        f"تمت برمجتي بواسطه احمد الرماح",
                parse_mode='HTML'
            )
            
            # إرسال رسالة تأكيد
            keyboard = [
                [InlineKeyboardButton("🔑 الحصول على كود جديد", callback_data="get_last_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ تم إرسال الفيديو التعليمي. شاهده بالأعلى.",
                reply_markup=reply_markup
            )
        else:
            # إذا لم يكن هناك فيديو، أرسل تعليمات نصية فقط
            keyboard = [
                [InlineKeyboardButton("🔑 الحصول على كود", callback_data="get_last_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"<b>📝 طريقة تسجيل الدخول إلى ChatGPT:</b>\n\n"
                f"📧 البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
                f"🔒 كلمة المرور: <code>{PASSWORD}</code>\n\n"
                f"<b>الخطوات:</b>\n"
                f"1. اضغط على 'Try another method' من الأسفل\n"
                f"2. اختر البريد الإلكتروني (الخيار الثالث)\n"
                f"3. أدخل الكود الذي تحصل عليه من البوت\n\n"
                f"ملاحظة: لم يتم العثور على الفيديو التعليمي حالياً.\n\n"
                f"تمت برمجتي بواسطه احمد الرماح",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل الواردة واستخراج الأكواد"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # التحقق من انتظار فيديو تعليمي من المسؤول
    if context.user_data.get("waiting_for_tutorial") and is_admin(user_id):
        if update.message.video:
            # حفظ الفيديو التعليمي
            video_file_id = update.message.video.file_id
            save_tutorial_video_info(video_file_id)
            context.user_data["waiting_for_tutorial"] = False
            
            await update.message.reply_text(
                "✅ تم حفظ الفيديو التعليمي بنجاح.\n"
                "سيتم عرضه للمستخدمين من خلال زر 'شاهد شرح طريقة الدخول'."
            )
            return
        else:
            # رسالة غير مناسبة
            await update.message.reply_text(
                "❌ يرجى إرسال ملف فيديو.\n"
                "استخدم الأمر /start للعودة إلى القائمة الرئيسية."
            )
            return
    
    # معالجة الرسائل العادية
    text = update.message.text
    
    # محاولة استخراج الكود
    code = extract_code(text)
    
    # التحقق مما إذا كانت الرسالة تبدو كبريد من OpenAI
    is_email = is_openai_email(text)
    
    # تحضير أزرار الرد
    keyboard = [
        [InlineKeyboardButton("🔑 عرض آخر كود", callback_data="get_last_code")],
    ]
    
    # إضافة زر الفيديو التعليمي إذا كان متاحًا
    video_info = read_tutorial_video_info()
    if video_info["file_id"]:
        keyboard.append([InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="view_tutorial")])
    
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👨‍💼 لوحة المسؤول", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if code:
        # حفظ الكود
        manual_input = not is_email  # إذا لم يكن بريد إلكتروني، فهو إدخال يدوي
        save_code(code, user_name, manual_input)
        
        # تأكيد استلام الكود للمستخدم
        await update.message.reply_text(
            f"✅ تم استلام وحفظ الكود: <code>{code}</code>\n\n"
            f"{LOGIN_INSTRUCTIONS}\n\n"
            f"تمت برمجتي بواسطه احمد الرماح",
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
            "لم يتم العثور على أي كود في رسالتك. الرجاء إرسال رسالة تحتوي على كود مكون من 6 أرقام.\n\n"
            f"{LOGIN_INSTRUCTIONS}\n\n"
            "تمت برمجتي بواسطه احمد الرماح",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر خاص بالمسؤول للوصول إلى لوحة التحكم"""
    user_id = update.effective_user.id
    args = context.args
    
    # التحقق من كلمة المرور
    if len(args) != 1 or args[0] != PASSWORD:
        await update.message.reply_text("❌ كلمة مرور غير صحيحة.")
        return
    
    # تحديث معرف المسؤول إذا لم يكن موجوداً
    if not ADMIN_CHAT_ID:
        # هذا ليس الحل الأمثل، لكنه يمكن أن يعمل كحل مؤقت
        os.environ['TELEGRAM_CHAT_ID'] = str(user_id)
        logger.info(f"تم تعيين المستخدم {user_id} كمسؤول")
    
    keyboard = [
        [InlineKeyboardButton("📤 رفع فيديو تعليمي", callback_data="upload_tutorial")],
        [InlineKeyboardButton("👁 عرض الفيديو التعليمي", callback_data="view_tutorial_admin")],
        [InlineKeyboardButton("🗑 حذف الفيديو التعليمي", callback_data="delete_tutorial")],
        [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👨‍💼 <b>لوحة تحكم المسؤول</b>\n\n"
        "مرحباً بك في لوحة التحكم. اختر إحدى العمليات أدناه:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

def main() -> None:
    """تشغيل البوت"""
    # التحقق من وجود توكن البوت
    if not TELEGRAM_BOT_TOKEN:
        logger.error("لم يتم تعيين TELEGRAM_BOT_TOKEN. قم بإضافته إلى ملف .env")
        return
    
    # التأكد من وجود الملفات اللازمة
    ensure_codes_file()
    ensure_tutorial_video_file()

    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))
    application.add_handler(MessageHandler(filters.VIDEO, process_message))  # معالجة الفيديو
    application.add_handler(CallbackQueryHandler(button_callback))

    # بدء البوت
    logger.info("بدء تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 