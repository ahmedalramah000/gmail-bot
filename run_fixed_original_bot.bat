@echo off
echo ========================================
echo = تشغيل بوت Gmail-Telegram الأصلي المصحح =
echo ========================================
echo.

echo سيتم نسخ "fixed_gmail_bot.py" من الملف الأصلي وإصلاح الأخطاء...
copy /Y gmail_bot.py fixed_gmail_bot.py >nul

echo.
echo تعديل الملف وإصلاح أخطاء التنسيق...

powershell -Command "(Get-Content fixed_gmail_bot.py) -replace 'try:\s+await query\.edit_message_text\(', 'try:^n            await query.edit_message_text(' -replace '\^n', [Environment]::NewLine | Set-Content fixed_gmail_bot.py"

echo.
echo إضافة المتغيرات العالمية...

powershell -Command "$content = Get-Content fixed_gmail_bot.py -Raw; $varText = '# مجموعة لتخزين معرفات الاستجابات المعالجة^nprocessed_callbacks = set()^n# تخزين معرف آخر بريد إلكتروني تمت معالجته^nlast_processed_email_id = None^n'; $pos = $content.IndexOf('logger = logging.getLogger(__name__)'); $pos = $content.IndexOf([Environment]::NewLine, $pos) + [Environment]::NewLine.Length; $content.Substring(0, $pos) + $varText + $content.Substring($pos) | Set-Content fixed_gmail_bot.py" -replace '\^n', [Environment]::NewLine

echo.
echo تشغيل البوت المصحح...
echo.
python fixed_gmail_bot.py

pause 