@echo off
echo ========================================
echo        تشغيل بوت أكواد ChatGPT
echo ========================================
echo.

REM التحقق من وجود ملف .env
echo جاري التحقق من ملف .env...
if exist .env (
    echo تم العثور على ملف .env
) else (
    echo لم يتم العثور على ملف .env! سيتم إنشاؤه...
    copy env_config.txt .env
)

echo.
echo جاري تشغيل البوت...
python gmail_bot.py

REM في حال توقف البوت سيتم عرض هذه الرسالة
echo.
echo تم إيقاف البوت.
echo.
pause 