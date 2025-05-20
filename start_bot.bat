@echo off
echo ==============================================
echo      تشغيل بوت أكواد ChatGPT في الخلفية
echo ==============================================
echo.

echo جاري التحقق من ملف الإعدادات .env...
if exist .env (
    echo تم العثور على ملف .env
) else (
    echo لم يتم العثور على ملف .env! سيتم إنشاؤه...
    copy env_config.txt .env
)

echo.
echo جاري تشغيل البوت في الخلفية...
start /B cmd /c "python gmail_bot.py > bot.log 2>&1"

echo.
echo تم تشغيل البوت بنجاح!
echo جميع رسائل البوت سيتم تسجيلها في ملف bot.log
echo.
echo للتفاعل مع البوت، افتح تطبيق Telegram وأرسل /start
echo للمستخدم المسؤول، سيظهر زر "لوحة تحكم المسؤول" في القائمة الرئيسية
echo.
echo ملاحظة: لإيقاف البوت، افتح مدير المهام واحذف عملية Python
echo. 