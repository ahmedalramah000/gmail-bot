@echo off
echo ===================================
echo = تشغيل بوت Gmail-Telegram المصحح =
echo ===================================
echo.

if not exist simple_fixed_bot.py (
    echo تطبيق الإصلاحات على البوت...
    python simple_bot.py
    echo.
)

echo تشغيل البوت المصحح...
echo.
python simple_fixed_bot.py

pause 