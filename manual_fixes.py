#!/usr/bin/env python3
"""
سكربت لتطبيق الإصلاحات بشكل مباشر على نسخة من البوت
"""

import os
import shutil

def main():
    # التحقق من وجود الملف الأصلي
    if not os.path.exists("gmail_bot.py"):
        print("خطأ: الملف الأصلي gmail_bot.py غير موجود")
        return
    
    # إنشاء نسخة احتياطية
    backup_file = "gmail_bot.py.manual_backup"
    if not os.path.exists(backup_file):
        print(f"إنشاء نسخة احتياطية: {backup_file}")
        shutil.copy("gmail_bot.py", backup_file)
    
    # إنشاء ملف المخرجات
    output_file = "manual_fixed_bot.py"
    print(f"إنشاء ملف: {output_file}")
    
    # فتح ملف الإدخال وقراءته
    with open("gmail_bot.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # إضافة المتغيرات العالمية بعد تعريف logger
    logger_found = False
    processed_callbacks_added = False
    modified_lines = []
    
    for line in lines:
        modified_lines.append(line)
        
        # إضافة المتغيرات العالمية
        if not processed_callbacks_added and "logger = logging.getLogger" in line:
            logger_found = True
            modified_lines.append("\n# مجموعة لتخزين معرفات الاستجابات المعالجة\n")
            modified_lines.append("processed_callbacks = set()\n")
            modified_lines.append("# تخزين معرف آخر بريد إلكتروني تمت معالجته\n")
            modified_lines.append("last_processed_email_id = None\n")
            processed_callbacks_added = True
            print("✓ تمت إضافة المتغيرات العالمية")
    
    # إضافة معالج الخطأ العام في دالة main() قبل تشغيل البوت
    error_handler_inserted = False
    app_run_polling_found = False
    
    for i in range(len(modified_lines)):
        if not error_handler_inserted and "application.run_polling" in modified_lines[i]:
            app_run_polling_found = True
            
            # تحديد المسافة البادئة من السطر الحالي
            indent = ""
            for char in modified_lines[i]:
                if char.isspace():
                    indent += char
                else:
                    break
            
            # إنشاء معالج الخطأ
            error_handler = [
                f"\n{indent}# إضافة معالج الأخطاء\n",
                f"{indent}async def error_handler(update, context):\n",
                f"{indent}    \"\"\"تسجيل الأخطاء التي تسببها التحديثات.\"\"\"\n",
                f"{indent}    logger.error(f\"حدث استثناء أثناء معالجة تحديث: {{context.error}}\")\n",
                f"{indent}    \n",
                f"{indent}    # إخطار المستخدم بالخطأ إذا كان ذلك مناسبًا\n",
                f"{indent}    if update and update.effective_chat:\n",
                f"{indent}        try:\n",
                f"{indent}            await context.bot.send_message(\n",
                f"{indent}                chat_id=update.effective_chat.id,\n",
                f"{indent}                text=\"حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى.\"\n",
                f"{indent}            )\n",
                f"{indent}        except Exception as e:\n",
                f"{indent}            logger.error(f\"فشل في إرسال رسالة الخطأ: {{e}}\")\n",
                f"{indent}            \n",
                f"{indent}application.add_error_handler(error_handler)\n"
            ]
            
            # إدراج معالج الخطأ قبل سطر application.run_polling
            for line in error_handler:
                modified_lines.insert(i, line)
                i += 1
            
            error_handler_inserted = True
            print("✓ تمت إضافة معالج الخطأ العام")
    
    # كتابة محتوى الملف المعدل
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(modified_lines)
    
    print("\nتم إنشاء البوت المصحح بنجاح!")
    print("يجب عليك الآن تعديل دالتي button_callback و get_latest_verification_code يدوياً")
    print("باتباع التعليمات في ملف fix_all_errors.txt")
    print("\nيمكنك تشغيل البوت المصحح باستخدام الأمر:")
    print(f"python {output_file}")

if __name__ == "__main__":
    main() 