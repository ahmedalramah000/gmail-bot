#!/bin/bash

# سكريبت لتشغيل البوت في الخلفية
echo "بدء تشغيل بوت التليجرام..."

# الانتقال إلى مجلد البوت
cd ~/telegram_bot

# تشغيل البوت في الخلفية باستخدام screen
# يمكنك الاتصال بجلسة screen باستخدام: screen -r telegram_bot
screen -dmS telegram_bot bash -c "python3 gmail_bot.py; exec bash"

# التحقق من حالة التشغيل
echo "تم تشغيل البوت في الخلفية"
echo "للاتصال بجلسة البوت استخدم الأمر: screen -r telegram_bot"
echo "للانفصال من الجلسة بدون إيقاف البوت اضغط: Ctrl+A ثم D" 