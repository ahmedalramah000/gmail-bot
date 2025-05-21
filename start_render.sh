#!/bin/bash

echo "=== بدء تشغيل البوت على منصة Render ==="

# تثبيت المتطلبات
echo "تثبيت المتطلبات..."
pip install -r requirements.txt

# تنفيذ سكريبت الإصلاح
echo "تنفيذ سكريبت إصلاح Render..."
python render_fix.py

# تشغيل البوت
echo "بدء تشغيل البوت..."
python gmail_bot.py 