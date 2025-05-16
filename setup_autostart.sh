#!/bin/bash

# سكريبت لإعداد البوت للعمل تلقائيًا عند إعادة تشغيل الخادم
echo "إعداد تشغيل البوت تلقائيًا عند إعادة تشغيل الخادم..."

# الحصول على المسار الكامل للبوت
BOT_DIR="$HOME/telegram_bot"
RUN_SCRIPT="$BOT_DIR/run_at_startup.sh"

# إنشاء سكريبت التشغيل عند بدء التشغيل
echo "إنشاء سكريبت التشغيل التلقائي..."
cat > "$RUN_SCRIPT" << 'EOL'
#!/bin/bash
cd $HOME/telegram_bot
python3 gmail_bot.py >> bot.log 2>&1
EOL

# جعل السكريبت قابل للتنفيذ
chmod +x "$RUN_SCRIPT"

# إضافة السكريبت إلى crontab
echo "إضافة السكريبت إلى جدول المهام (crontab)..."
(crontab -l 2>/dev/null || echo "") | grep -v "telegram_bot/run_at_startup.sh" | { cat; echo "@reboot $RUN_SCRIPT"; } | crontab -

echo "تم الإعداد بنجاح! البوت سيعمل تلقائيًا عند إعادة تشغيل الخادم."
echo "لاختبار الإعداد، أعد تشغيل الخادم باستخدام الأمر: sudo reboot" 