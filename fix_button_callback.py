"""
This file contains the fixed button_callback method for the Gmail-Telegram Bot.
It includes fixes for:
1. Preventing duplicate button processing
2. Adding error handling for message editing operations
3. Better user feedback when errors occur
"""

import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import CallbackContext
import telegram

# تعريف الدالة المعدلة
async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة نقرات الأزرار مع منع المعالجة المكررة واستخدام معالجة الأخطاء المحسنة."""
    global TUTORIAL_VIDEO_FILE_ID, processed_callbacks, last_processed_email_id
    query = update.callback_query
    user_id = str(update.effective_user.id)
    
    # تجنب معالجة نفس الاستجابة عدة مرات
    callback_id = f"{query.message.message_id}_{query.data}"
    if callback_id in processed_callbacks:
        await query.answer("جاري المعالجة...")
        return
        
    # إضافة إلى الاستجابات المعالجة
    processed_callbacks.add(callback_id)
    
    # إذا وصل عدد الاستجابات المعالجة لأكثر من 1000، احذف القديمة
    if len(processed_callbacks) > 1000:
        # حذف أقدم 500 استجابة
        processed_callbacks = set(list(processed_callbacks)[-500:])
    
    await query.answer()
    
    if query.data == "get_chatgpt_code":
        # عرض رسالة انتظار
        try:
            await query.edit_message_text("🔍 جاري البحث عن آخر كود... انتظر قليلاً")
        except telegram.error.BadRequest as e:
            logger.error(f"فشل في تعديل رسالة الانتظار: {e}")
            try:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="🔍 جاري البحث عن آخر كود... انتظر قليلاً"
                )
            except Exception as e2:
                logger.error(f"فشل في إرسال رسالة انتظار جديدة: {e2}")
                return
        
        # البحث عن الكود
        code_info = self.get_latest_verification_code(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="get_chatgpt_code")],
            [InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="show_tutorial")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if code_info:
            if "error" in code_info and code_info["error"] == "rate_limit":
                keyboard_rate_limit = [
                    [InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="show_tutorial")]
                ]
                reply_markup_rate_limit = InlineKeyboardMarkup(keyboard_rate_limit)
                
                try:
                    await query.edit_message_text(
                        "⚠️ لقد تجاوزت الحد الأقصى من الطلبات. يرجى المحاولة لاحقًا.\n\n"
                        f"📧 البريد: <code>{TARGET_EMAIL}</code>\n"
                        f"🔒 كلمة المرور: <code>{PASSWORD}</code>\n\n"
                        f"<b>📝 طريقة الدخول:</b>\n"
                        f'1. اضغط على "try another method" من الأسفل\n'
                        f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                        f'3. أدخل الكود الذي ستحصل عليه\n\n'
                        f"تمت برمجتي بواسطه احمد الرماح",
                        reply_markup=reply_markup_rate_limit,
                        parse_mode='HTML'
                    )
                except telegram.error.BadRequest as e:
                    logger.error(f"فشل في تحديث رسالة حد الاستخدام: {e}")
                    try:
                        await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text="⚠️ لقد تجاوزت الحد الأقصى من الطلبات. يرجى المحاولة لاحقًا.\n\n"
                            f"📧 البريد: <code>{TARGET_EMAIL}</code>\n"
                            f"🔒 كلمة المرور: <code>{PASSWORD}</code>\n\n"
                            f"<b>📝 طريقة الدخول:</b>\n"
                            f'1. اضغط على "try another method" من الأسفل\n'
                            f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                            f'3. أدخل الكود الذي ستحصل عليه\n\n'
                            f"تمت برمجتي بواسطه احمد الرماح",
                            reply_markup=reply_markup_rate_limit,
                            parse_mode='HTML'
                        )
                    except Exception as e2:
                        logger.error(f"فشل في إرسال رسالة حد الاستخدام جديدة: {e2}")
                return
            
            # عرض الكود فقط بطريقة بسيطة مع بيانات تسجيل الدخول
            message = (
                f"🔑 <b>كود التحقق الخاص بك:</b>\n\n"
                f"<code>{code_info['code']}</code>\n\n"
                f"📧 <b>بيانات تسجيل الدخول:</b>\n"
                f"البريد: <code>{TARGET_EMAIL}</code>\n"
                f"الباسورد: <code>{PASSWORD}</code>\n\n"
                f"<b>📝 طريقة الدخول:</b>\n"
                f'1. اضغط على "try another method" من الأسفل\n'
                f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                f'3. أدخل الكود المعروض أعلاه\n\n'
                f"تمت برمجتي بواسطه احمد الرماح"
            )
            
            try:
                await query.edit_message_text(
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except telegram.error.BadRequest as e:
                logger.error(f"فشل في تعديل رسالة الكود: {e}")
                try:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=message,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                except Exception as e2:
                    logger.error(f"فشل في إرسال رسالة الكود جديدة: {e2}")
        else:
            # رسالة محسنة عند عدم وجود كود
            keyboard_no_code = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="get_chatgpt_code")],
                [InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="show_tutorial")]
            ]
            reply_markup_no_code = InlineKeyboardMarkup(keyboard_no_code)
            
            try:
                await query.edit_message_text(
                    f"❌ لم يتم العثور على كود تحقق\nحاول مره اخري\n\n"
                    f"📧 <b>بيانات تسجيل الدخول:</b>\n"
                    f"البريد: <code>{TARGET_EMAIL}</code>\n"
                    f"الباسورد: <code>{PASSWORD}</code>\n\n"
                    f"<b>📝 طريقة الدخول:</b>\n"
                    f'1. اضغط على "try another method" من الأسفل\n'
                    f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                    f'3. أدخل الكود الذي ستحصل عليه\n\n'
                    f"تمت برمجتي بواسطه احمد الرماح",
                    reply_markup=reply_markup_no_code,
                    parse_mode='HTML'
                )
            except telegram.error.BadRequest as e:
                logger.error(f"فشل في تعديل رسالة عدم وجود كود: {e}")
                try:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"❌ لم يتم العثور على كود تحقق\nحاول مره اخري\n\n"
                        f"📧 <b>بيانات تسجيل الدخول:</b>\n"
                        f"البريد: <code>{TARGET_EMAIL}</code>\n"
                        f"الباسورد: <code>{PASSWORD}</code>\n\n"
                        f"<b>📝 طريقة الدخول:</b>\n"
                        f'1. اضغط على "try another method" من الأسفل\n'
                        f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                        f'3. أدخل الكود الذي ستحصل عليه\n\n'
                        f"تمت برمجتي بواسطه احمد الرماح",
                        reply_markup=reply_markup_no_code,
                        parse_mode='HTML'
                    )
                except Exception as e2:
                    logger.error(f"فشل في إرسال رسالة عدم وجود كود جديدة: {e2}")
                
    elif query.data == "show_tutorial":
        try:
            # إرسال فيديو الشرح
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=TUTORIAL_VIDEO_FILE_ID,
                caption="🎬 <b>شرح طريقة الحصول على كود التحقق</b>\n\n"
                "اتبع الخطوات كما في الفيديو للحصول على كود التحقق من OpenAI",
                parse_mode='HTML'
            )
            await query.edit_message_reply_markup(reply_markup=None)
        except telegram.error.BadRequest as e:
            logger.error(f"فشل في إرسال فيديو الشرح: {e}")
            try:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="⚠️ حدث خطأ أثناء إرسال فيديو الشرح. يرجى المحاولة مرة أخرى."
                )
            except Exception as e2:
                logger.error(f"فشل في إرسال رسالة خطأ فيديو الشرح: {e2}")

# تعديلات في get_latest_verification_code للتعامل مع البريد المكرر

def get_latest_verification_code(self, user_id: str) -> Optional[dict]:
    """استرجاع آخر كود تحقق من Gmail مع تجاهل أكواد إعادة تعيين كلمة المرور."""
    global last_processed_email_id
    
    # باقي الشيفرة
    
    # بعد استرجاع رسائل البريد الإلكتروني
    for msg in messages:
        msg_id = msg.get("id")
        
        # التحقق مما إذا كان هذا البريد الإلكتروني قد تمت معالجته بالفعل
        if msg_id == last_processed_email_id:
            logger.info(f"تمت معالجة هذا البريد الإلكتروني بالفعل: {msg_id}")
            continue
            
        # باقي الشيفرة
        
        # عند تحديد كود صالح
        # تحديث معرف آخر بريد تمت معالجته
        last_processed_email_id = msg_id
        
        return {
            "code": verification_code,
            "sender": sender,
            "subject": subject,
            "time": received_time
        }
        
# إضافة معالج للأخطاء العامة
async def error_handler(update, context):
    """تسجيل الأخطاء التي تسببها التحديثات."""
    logger.error(f"حدث استثناء أثناء معالجة تحديث: {context.error}")
    
    # إخطار المستخدم بالخطأ إذا كان ذلك مناسبًا
    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى."
            )
        except Exception as e:
            logger.error(f"فشل في إرسال رسالة الخطأ: {e}")

# كيفية تسجيل معالج الخطأ في دالة main
# application.add_error_handler(error_handler) 