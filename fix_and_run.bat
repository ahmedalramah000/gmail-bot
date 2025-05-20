@echo off
echo =========================================
echo = إصلاح وتشغيل بوت Gmail-Telegram الأصلي =
echo =========================================
echo.

echo 1. إنشاء نسخة للإصلاح...
copy /Y gmail_bot.py fixed_original_bot.py >nul

echo 2. إصلاح المسافات البادئة...
powershell -Command "(Get-Content fixed_original_bot.py) -replace 'try:\s+await query\.edit_message_text\(', 'try:\n            await query.edit_message_text(' | Set-Content fixed_original_bot.py"

echo 3. إضافة المتغيرات العالمية (processed_callbacks, last_processed_email_id)...
powershell -Command "$content = Get-Content fixed_original_bot.py -Raw; $logger_index = $content.IndexOf('logger = logging.getLogger'); $nl_index = $content.IndexOf([char]10, $logger_index) + 1; $globals = '# مجموعة لتخزين معرفات الاستجابات المعالجة' + [char]10 + 'processed_callbacks = set()' + [char]10 + '# تخزين معرف آخر بريد إلكتروني تمت معالجته' + [char]10 + 'last_processed_email_id = None' + [char]10; $content.Substring(0, $nl_index) + $globals + $content.Substring($nl_index) | Set-Content fixed_original_bot.py"

echo 4. تشغيل البوت المصحح...
echo.
python fixed_original_bot.py

echo.
echo إذا استمرت المشكلة، جرب تشغيل simple_bot.py بدلاً منه:
echo python simple_bot.py
echo.

pause 