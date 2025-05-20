#!/usr/bin/env python3
"""
سكريبت بسيط لإصلاح أخطاء المسافات البادئة في ملف gmail_bot.py
"""

import re
import os

def main():
    # التحقق من وجود الملف
    if not os.path.exists("gmail_bot.py"):
        print("خطأ: ملف gmail_bot.py غير موجود")
        return
    
    # قراءة المحتوى
    with open("gmail_bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # إضافة المتغيرات العالمية إذا لم تكن موجودة
    if "processed_callbacks = set()" not in content:
        logger_pos = content.find("logger = logging.getLogger(__name__)")
        if logger_pos > 0:
            new_line_pos = content.find("\n", logger_pos) + 1
            global_vars = "\n# مجموعة لتخزين معرفات الاستجابات المعالجة\nprocessed_callbacks = set()\n# تخزين معرف آخر بريد إلكتروني تمت معالجته\nlast_processed_email_id = None\n"
            content = content[:new_line_pos] + global_vars + content[new_line_pos:]
            print("تمت إضافة المتغيرات العالمية")
    
    # إصلاح خطأ المسافات البادئة في دالة button_callback
    # نمط البحث عن سطر الخطأ
    error_pattern = r'try:\s+await query\.edit_message_text\("🔍 جاري البحث عن آخر كود\.\.\. انتظر قليلاً"\)\s+except'
    
    # استبدال النمط بالتنسيق الصحيح
    fixed_code = re.sub(error_pattern, 
                        'try:\n            await query.edit_message_text("🔍 جاري البحث عن آخر كود... انتظر قليلاً")\n        except',
                        content)
    
    # كتابة المحتوى المصحح
    with open("fixed_gmail_bot.py", "w", encoding="utf-8") as f:
        f.write(fixed_code)
    
    print("تم إصلاح أخطاء المسافات البادئة وحفظ الملف كـ fixed_gmail_bot.py")
    print("يمكنك تشغيل البوت المصحح بالأمر:")
    print("python fixed_gmail_bot.py")

if __name__ == "__main__":
    main() 