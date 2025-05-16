#!/bin/bash

# سكريبت لإعداد البوت كخدمة نظام
echo "إعداد البوت كخدمة نظام..."

# تحديد المسارات
BOT_DIR="$HOME/telegram_bot"
SERVICE_NAME="telegram-bot"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# إنشاء ملف الخدمة
echo "إنشاء ملف خدمة النظام..."

sudo tee "$SERVICE_FILE" > /dev/null << EOL
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
ExecStart=/usr/bin/python3 $BOT_DIR/gmail_bot.py
Restart=always
RestartSec=10
StandardOutput=append:$BOT_DIR/bot.log
StandardError=append:$BOT_DIR/bot.log

[Install]
WantedBy=multi-user.target
EOL

# تحديث systemd
echo "تحديث خدمات النظام..."
sudo systemctl daemon-reload

# تفعيل وتشغيل الخدمة
echo "تمكين وتشغيل الخدمة..."
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# التحقق من حالة الخدمة
echo "التحقق من حالة الخدمة..."
sudo systemctl status "$SERVICE_NAME"

echo "تم إعداد الخدمة بنجاح! البوت سيعمل تلقائيًا عند تشغيل النظام."
echo "أوامر مفيدة:"
echo "  - عرض حالة البوت: sudo systemctl status $SERVICE_NAME"
echo "  - إعادة تشغيل البوت: sudo systemctl restart $SERVICE_NAME"
echo "  - إيقاف البوت: sudo systemctl stop $SERVICE_NAME"
echo "  - عرض سجلات البوت: journalctl -u $SERVICE_NAME" 