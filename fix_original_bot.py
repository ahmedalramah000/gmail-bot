#!/usr/bin/env python3
"""
سكريبت لإصلاح الأخطاء في ملف gmail_bot.py والحصول على نسخة تعمل مثل النسخة الأصلية
"""

import os
import re
import shutil

def main():
    """تطبيق الإصلاحات على ملف gmail_bot.py"""
    print("==== أداة إصلاح بوت Gmail-Telegram (النسخة الأصلية) ====")
    
    # التحقق من وجود الملف الأصلي
    if not os.path.exists("gmail_bot.py"):
        print("خطأ: الملف الأصلي gmail_bot.py غير موجود")
        return
    
    # إنشاء نسخة احتياطية
    backup_file = "gmail_bot.py.original_backup"
    if not os.path.exists(backup_file):
        print(f"إنشاء نسخة احتياطية من الملف الأصلي: {backup_file}")
        shutil.copy("gmail_bot.py", backup_file)
    
    # قراءة الملف الأصلي
    with open("gmail_bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # إصلاح السطر 1074 (خطأ المسافات والصياغة)
    print("إصلاح خطأ الصياغة في دالة button_callback...")
    
    # البحث عن الجزء المعطوب وإصلاحه
    button_callback_start = content.find("async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):")
    if button_callback_start > 0:
        # البحث عن بداية خطأ التنسيق
        error_start = content.find("try:", button_callback_start)
        if error_start > 0:
            # البحث عن نهاية الدالة أو الجزء المعطوب
            next_method = content.find("async def", button_callback_start + 1)
            if next_method < 0:
                next_method = len(content)
            
            # استخراج الكود المعطوب
            broken_code = content[button_callback_start:next_method]
            
            # الإصلاح الأول: خطأ التنسيق في السطر 1074
            fixed_code = re.sub(
                r'try:\s+await query\.edit_message_text\("🔍 جاري البحث عن آخر كود\.\.\. انتظر قليلاً"\)\s+except',
                """try:
            await query.edit_message_text("🔍 جاري البحث عن آخر كود... انتظر قليلاً")
        except""",
                broken_code
            )
            
            # الإصلاح الثاني: إصلاح باقي الأخطاء المحتملة في تنسيق try/except
            fixed_code = re.sub(
                r'if "([^"]+)" in str\(e\) or "([^"]+)" in str\(e\) or "([^"]+)" in str\(e\):\s+# [^\n]+\s+try:',
                r'if "\1" in str(e) or "\2" in str(e) or "\3" in str(e):\n                # تم حذف الرسالة أو غير قابلة للتعديل\n                try:',
                fixed_code
            )
            
            # استبدال التعليمات والمسافات البادئة المعطوبة
            fixed_code = re.sub(
                r'except Exception as e2:(\s+)logger\.error\(f"فشل في إرسال رسالة جديدة: {e2}"\)(\s+)return',
                r'except Exception as e2:\n                    logger.error(f"فشل في إرسال رسالة جديدة: {e2}")\n                    return',
                fixed_code
            )
            
            # إصلاح أي أخطاء متبقية في المسافات البادئة
            fixed_code = re.sub(
                r'else:(\s+)logger\.error\(f"خطأ في API تيليجرام: {e}"\)(\s+)return', 
                r'else:\n                logger.error(f"خطأ في API تيليجرام: {e}")\n                return',
                fixed_code
            )
            
            # تطبيق الإصلاحات
            content = content[:button_callback_start] + fixed_code + content[next_method:]
    
    # إضافة متغيرات عالمية لتتبع الاستجابات والرسائل المعالجة
    if "processed_callbacks = set()" not in content:
        logger_line = content.find("logger = logging.getLogger(__name__)")
        if logger_line > 0:
            insert_pos = content.find("\n", logger_line) + 1
            globals_code = """
# مجموعة لتخزين معرفات الاستجابات المعالجة
processed_callbacks = set()
# تخزين معرف آخر بريد إلكتروني تمت معالجته
last_processed_email_id = None
"""
            content = content[:insert_pos] + globals_code + content[insert_pos:]
            print("تمت إضافة المتغيرات العالمية لمنع المعالجة المكررة")
    
    # إضافة global في دالة get_latest_verification_code
    verification_code_func = content.find("def get_latest_verification_code(self, user_id: str)")
    if verification_code_func > 0:
        function_body_start = content.find(":", verification_code_func) + 1
        function_body_start = content.find("\n", function_body_start) + 1
        
        indent = ""
        for char in content[function_body_start:function_body_start+20]:
            if char.isspace():
                indent += char
            else:
                break
        
        if "global last_processed_email_id" not in content[verification_code_func:verification_code_func+500]:
            global_var = f"{indent}global last_processed_email_id\n"
            content = content[:function_body_start] + global_var + content[function_body_start:]
            print("تمت إضافة المتغير العالمي في دالة get_latest_verification_code")
    
    # إضافة التحقق من الرسائل المكررة
    for_msg_in_messages = content.find("for msg in messages:", verification_code_func)
    if for_msg_in_messages > 0:
        msg_id_line = content.find("msg_id = msg", for_msg_in_messages)
        if msg_id_line > 0:
            end_of_line = content.find("\n", msg_id_line) + 1
            
            loop_indent = indent + "    "  # المسافة البادئة داخل الحلقة
            duplicate_check = f"""
{loop_indent}# التحقق مما إذا كان هذا البريد الإلكتروني قد تمت معالجته بالفعل
{loop_indent}if msg_id == last_processed_email_id:
{loop_indent}    logger.info(f"تمت معالجة هذا البريد الإلكتروني بالفعل: {{msg_id}}")
{loop_indent}    continue
"""
            if "if msg_id == last_processed_email_id" not in content[msg_id_line:msg_id_line+500]:
                content = content[:end_of_line] + duplicate_check + content[end_of_line:]
                print("تمت إضافة التحقق من البريد المكرر")
    
    # إضافة تحديث معرف آخر بريد تمت معالجته
    return_verification = re.search(r'(\s+)return\s+\{\s*["\']code["\']', content[verification_code_func:])
    if return_verification:
        return_indent = return_verification.group(1)
        return_pos = verification_code_func + return_verification.start()
        
        update_last_id = f"""
{return_indent}# تحديث معرف آخر بريد تمت معالجته
{return_indent}last_processed_email_id = msg_id

"""
        if "last_processed_email_id = msg_id" not in content[return_pos-200:return_pos]:
            content = content[:return_pos] + update_last_id + content[return_pos:]
            print("تمت إضافة تحديث معرف آخر بريد")
    
    # إضافة معالج الخطأ العام
    main_func = content.find("def main():")
    if main_func > 0:
        run_polling = content.find("application.run_polling(", main_func)
        if run_polling > 0:
            lines = content[main_func:run_polling].split("\n")
            indent = "    "  # المسافة البادئة الافتراضية
            for line in reversed(lines):
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
            if "application.add_error_handler" not in content[main_func:run_polling+100]:
                content = content[:run_polling] + error_handler + content[run_polling:]
                print("تمت إضافة معالج الخطأ العام")
    
    # كتابة الملف المصحح
    output_file = "fixed_gmail_bot.py"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\nتم إنشاء نسخة مصححة بنجاح: {output_file}")
    print("يمكنك تشغيلها باستخدام الأمر:")
    print(f"python {output_file}")

if __name__ == "__main__":
    main() 