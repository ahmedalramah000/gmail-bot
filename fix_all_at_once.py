#!/usr/bin/env python3
"""
سكريبت شامل لإصلاح جميع الأخطاء في بوت Gmail-Telegram ونسخ ملف صحيح من الصفر
"""

import os
import re
import shutil

def main():
    print("=== أداة الإصلاح الشامل لبوت Gmail-Telegram ===")
    
    # إنشاء نسخة جديدة من الملف الأصلي
    if not os.path.exists("gmail_bot.py"):
        print("خطأ: الملف الأصلي gmail_bot.py غير موجود!")
        return
    
    # نسخ الملف الأصلي
    input_file = "gmail_bot.py"
    output_file = "complete_fixed_bot.py"
    
    # إنشاء نسخة احتياطية أولاً
    backup_file = "gmail_bot.py.backup_before_fix"
    if not os.path.exists(backup_file):
        shutil.copy(input_file, backup_file)
        print(f"تم إنشاء نسخة احتياطية: {backup_file}")
    
    # قراءة محتوى الملف
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"خطأ في قراءة الملف: {e}")
        return
    
    # 1. إضافة المتغيرات العالمية
    print("1. إضافة المتغيرات العالمية...")
    if "processed_callbacks = set()" not in content:
        logger_index = content.find("logger = logging.getLogger(__name__)")
        if logger_index > 0:
            newline_index = content.find("\n", logger_index) + 1
            global_vars = """
# مجموعة لتخزين معرفات الاستجابات المعالجة
processed_callbacks = set()
# تخزين معرف آخر بريد إلكتروني تمت معالجته
last_processed_email_id = None
"""
            content = content[:newline_index] + global_vars + content[newline_index:]
    
    # 2. إصلاح خطأ المسافات البادئة في دالة button_callback
    print("2. إصلاح خطأ المسافات البادئة في دالة button_callback...")
    
    pattern = r'try:\s+await query\.edit_message_text\("🔍 جاري البحث عن آخر كود\.\.\. انتظر قليلاً"\)\s+except'
    replacement = 'try:\n            await query.edit_message_text("🔍 جاري البحث عن آخر كود... انتظر قليلاً")\n        except'
    content = re.sub(pattern, replacement, content)
    
    # 3. إصلاح المزيد من أخطاء التنسيق في نفس الدالة
    print("3. إصلاح أخطاء التنسيق الإضافية...")
    
    # أ. إصلاح تنسيق شرط if وما بعده
    pattern2 = r'if "([^"]+)" in str\(e\) or "([^"]+)" in str\(e\) or "([^"]+)" in str\(e\):\s+# [^\n]+\s+try:'
    replacement2 = r'if "\1" in str(e) or "\2" in str(e) or "\3" in str(e):\n                # تم حذف الرسالة أو غير قابلة للتعديل\n                try:'
    content = re.sub(pattern2, replacement2, content)
    
    # ب. إصلاح تنسيق except Exception
    pattern3 = r'except Exception as e2:(\s+)logger\.error\([^)]+\)(\s+)return'
    replacement3 = r'except Exception as e2:\n                    logger.error(f"فشل في إرسال رسالة جديدة: {e2}")\n                    return'
    content = re.sub(pattern3, replacement3, content)
    
    # ج. إصلاح تنسيق else:
    pattern4 = r'else:(\s+)logger\.error\([^)]+\)(\s+)return'
    replacement4 = r'else:\n                logger.error(f"خطأ في API تيليجرام: {e}")\n                return'
    content = re.sub(pattern4, replacement4, content)
    
    # 4. إضافة استخدام global في دالة get_latest_verification_code
    print("4. إضافة متغير global في دالة get_latest_verification_code...")
    
    verification_func = content.find("def get_latest_verification_code(self, user_id: str)")
    if verification_func > 0:
        func_body_start = content.find(":", verification_func) + 1
        func_body_start = content.find("\n", func_body_start) + 1
        
        # تحديد المسافة البادئة
        indent = ""
        for char in content[func_body_start:func_body_start+20]:
            if char.isspace():
                indent += char
            else:
                break
                
        # إضافة global إذا لم تكن موجودة
        if "global last_processed_email_id" not in content[verification_func:verification_func+200]:
            global_var = f"{indent}global last_processed_email_id\n"
            content = content[:func_body_start] + global_var + content[func_body_start:]
    
    # 5. إضافة التحقق من الرسائل المكررة
    print("5. إضافة التحقق من الرسائل المكررة...")
    
    msg_loop = content.find("for msg in messages:", verification_func)
    if msg_loop > 0:
        msg_id_line = content.find("msg_id = msg", msg_loop)
        if msg_id_line > 0:
            line_end = content.find("\n", msg_id_line) + 1
            
            loop_indent = indent + "    "  # مستوى تداخل واحد أعمق
            dup_check = f"""
{loop_indent}# التحقق مما إذا كان هذا البريد الإلكتروني قد تمت معالجته بالفعل
{loop_indent}if msg_id == last_processed_email_id:
{loop_indent}    logger.info(f"تمت معالجة هذا البريد الإلكتروني بالفعل: {{msg_id}}")
{loop_indent}    continue
"""
            if "if msg_id == last_processed_email_id" not in content[msg_id_line:msg_id_line+300]:
                content = content[:line_end] + dup_check + content[line_end:]
    
    # 6. إضافة تحديث معرف آخر بريد تمت معالجته
    print("6. إضافة تحديث معرف آخر بريد تمت معالجته...")
    
    return_pattern = re.search(r'(\s+)return\s+\{\s*["\']code["\']', content[verification_func:])
    if return_pattern:
        return_indent = return_pattern.group(1)
        return_pos = verification_func + return_pattern.start()
        
        update_id = f"""
{return_indent}# تحديث معرف آخر بريد تمت معالجته
{return_indent}last_processed_email_id = msg_id

"""
        if "last_processed_email_id = msg_id" not in content[return_pos-200:return_pos]:
            content = content[:return_pos] + update_id + content[return_pos:]
    
    # 7. إضافة معالج الأخطاء العام في دالة main
    print("7. إضافة معالج الأخطاء العام...")
    
    main_func = content.find("def main():")
    if main_func > 0:
        run_polling = content.find("application.run_polling(", main_func)
        if run_polling > 0:
            # تحديد المسافة البادئة
            indent = "    "
            main_lines = content[main_func:run_polling].splitlines()
            for line in main_lines:
                if line.strip().startswith("application."):
                    indent = line[:line.find("application")]
                    break
            
            error_handler = f"""
{indent}# إضافة معالج الأخطاء
{indent}async def error_handler(update, context):
{indent}    """تسجيل الأخطاء التي تسببها التحديثات."""
{indent}    logger.error(f"حدث استثناء أثناء معالجة تحديث: {{context.error}}")
{indent}    
{indent}    # إخطار المستخدم بالخطأ إذا كان ذلك مناسبًا
{indent}    if update and update.effective_chat:
{indent}        try:
{indent}            await context.bot.send_message(
{indent}                chat_id=update.effective_chat.id,
{indent}                text="حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى."
{indent}            )
{indent}        except Exception as e:
{indent}            logger.error(f"فشل في إرسال رسالة الخطأ: {{e}}")
{indent}            
{indent}application.add_error_handler(error_handler)
"""
            if "application.add_error_handler" not in content[main_func:run_polling+300]:
                content = content[:run_polling] + error_handler + content[run_polling:]
    
    # كتابة الملف المصحح
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"تم إنشاء الملف المصحح بنجاح: {output_file}")
        print("يمكنك تشغيل البوت المصحح بالأمر:")
        print(f"python {output_file}")
    except Exception as e:
        print(f"خطأ في كتابة الملف المصحح: {e}")

if __name__ == "__main__":
    main() 