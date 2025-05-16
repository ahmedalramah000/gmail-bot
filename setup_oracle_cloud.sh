#!/bin/bash

# سكريبت لإعداد بيئة التشغيل على Oracle Cloud
echo "بدء إعداد بيئة التشغيل لبوت التليجرام على Oracle Cloud..."

# تحديث النظام
echo "تحديث النظام..."
sudo dnf update -y || sudo apt update -y

# تثبيت Python وأدوات التطوير
echo "تثبيت Python والمكتبات الأساسية..."
sudo dnf install -y python3 python3-pip git screen || sudo apt install -y python3 python3-pip git screen

# تثبيت المكتبات المطلوبة
echo "تثبيت المكتبات المطلوبة للبوت..."
pip3 install --upgrade pip
pip3 install python-telegram-bot google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv Flask

# إنشاء مجلد للبوت
echo "إنشاء مجلد للبوت..."
mkdir -p ~/telegram_bot

echo "اكتمل الإعداد. الآن انقل ملفات البوت إلى المجلد: ~/telegram_bot"
echo "ثم قم بتشغيل: bash run_bot.sh" 