@echo off
echo =============================
echo = تطبيق إصلاحات البوت يدوياً =
echo =============================
echo.

echo إنشاء ملف البوت المصحح...

echo. > manual_fixed_bot.py
echo :: إضافة محتوى البوت الأصلي
type gmail_bot.py > manual_fixed_bot.py

echo.
echo تم إنشاء البوت المصحح بنجاح!
echo.
echo لتشغيل البوت:
echo.
echo 1. قم بتعديل ملف manual_fixed_bot.py باستخدام محرر النصوص
echo 2. أضف المتغيرات العالمية التالية بعد سطر logger = logging.getLogger(__name__):
echo.
echo # مجموعة لتخزين معرفات الاستجابات المعالجة
echo processed_callbacks = set()
echo # تخزين معرف آخر بريد إلكتروني تمت معالجته
echo last_processed_email_id = None
echo.
echo 3. أضف "global last_processed_email_id" في بداية دالة get_latest_verification_code
echo 4. أضف الشرط التالي في حلقة معالجة رسائل البريد:
echo.
echo if msg_id == last_processed_email_id:
echo     logger.info(f"تمت معالجة هذا البريد الإلكتروني بالفعل: {msg_id}")
echo     continue
echo.
echo 5. أضف التالي قبل إرجاع كود التحقق:
echo.
echo last_processed_email_id = msg_id
echo.
echo 6. أضف معالج الخطأ قبل application.run_polling() في دالة main():
echo.
echo # إضافة معالج الأخطاء
echo async def error_handler(update, context):
echo     logger.error(f"حدث استثناء أثناء معالجة تحديث: {context.error}")
echo     if update and update.effective_chat:
echo         try:
echo             await context.bot.send_message(
echo                 chat_id=update.effective_chat.id,
echo                 text="حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى."
echo             )
echo         except Exception as e:
echo             logger.error(f"فشل في إرسال رسالة الخطأ: {e}")
echo application.add_error_handler(error_handler)
echo.
echo 7. تأكد من أن جميع استدعاءات edit_message_text محاطة بـ try/except
echo.
echo 8. ثم قم بتشغيل البوت:
echo python manual_fixed_bot.py
echo.

echo هل تريد فتح الملف للتعديل الآن؟ (Y/N)
choice /c YN /m "اختر:"

if %ERRORLEVEL% EQU 1 (
    notepad manual_fixed_bot.py
)

pause 