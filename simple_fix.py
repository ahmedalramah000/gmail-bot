#!/usr/bin/env python3
"""
سكربت بسيط لتطبيق إصلاحات أساسية على بوت Gmail-Telegram
"""

import os
import shutil
import re

def main():
    """تطبيق الإصلاحات الأساسية على البوت"""
    print("===== أداة إصلاح البوت =====")
    
    # التحقق من وجود الملف الأصلي
    if not os.path.exists("gmail_bot.py"):
        print("خطأ: ملف gmail_bot.py غير موجود")
        return False
    
    # إنشاء نسخة احتياطية
    backup_file = "gmail_bot.py.simple_backup"
    if not os.path.exists(backup_file):
        print(f"إنشاء نسخة احتياطية: {backup_file}")
        shutil.copy("gmail_bot.py", backup_file)
    
    # قراءة محتوى الملف
    with open("gmail_bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # تطبيق الإصلاحات
    content = apply_fixes(content)
    
    # كتابة الملف المصحح
    output_file = "simple_fixed_bot.py"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\nتم إنشاء البوت المصحح: {output_file}")
    print("يمكنك تشغيله باستخدام الأمر:")
    print(f"python {output_file}")

def apply_fixes(content):
    """تطبيق الإصلاحات الأساسية على محتوى الملف"""
    
    # 1. إضافة المتغيرات العالمية
    logger_line = content.find("logger = logging.getLogger(__name__)")
    if logger_line > 0:
        insert_pos = content.find("\n", logger_line) + 1
        
        global_vars = """
# مجموعة لتخزين معرفات الاستجابات المعالجة
processed_callbacks = set()
# تخزين معرف آخر بريد إلكتروني تمت معالجته
last_processed_email_id = None
"""
        content = content[:insert_pos] + global_vars + content[insert_pos:]
        print("✓ تمت إضافة المتغيرات العالمية")
    
    # 2. تحديث دالة button_callback
    button_callback_start = content.find("async def button_callback(self, update: Update, context:")
    if button_callback_start > 0:
        # البحث عن نهاية التعريف الأولي للدالة
        function_start_end = content.find(")", button_callback_start) + 1
        
        # البحث عن بداية جسم الدالة
        function_body_start = content.find("\n", function_start_end) + 1
        indent = "    "  # المسافة البادئة الافتراضية
        
        # العثور على المسافة البادئة الفعلية
        for char in content[function_body_start:function_body_start+20]:
            if char.isspace():
                indent += char
            else:
                break
        
        # إضافة التحقق من الاستجابات المكررة
        duplicate_check = f"""
{indent}global TUTORIAL_VIDEO_FILE_ID, processed_callbacks, last_processed_email_id
{indent}query = update.callback_query
{indent}user_id = str(update.effective_user.id)
    
{indent}# تجنب معالجة نفس الاستجابة عدة مرات
{indent}callback_id = f"{{query.message.message_id}}_{{query.data}}"
{indent}if callback_id in processed_callbacks:
{indent}    await query.answer("جاري المعالجة...")
{indent}    return
        
{indent}# إضافة إلى الاستجابات المعالجة
{indent}processed_callbacks.add(callback_id)
"""
        # البحث عن الكود الحالي
        old_code_start = content.find("query = update.callback_query", button_callback_start)
        old_code_end = content.find("await query.answer()", button_callback_start) + len("await query.answer()")
        
        if old_code_start > 0 and old_code_end > old_code_start:
            content = content[:old_code_start] + duplicate_check + content[old_code_end:]
            print("✓ تم تحديث دالة button_callback")
    
    # 3. تحديث دالة get_latest_verification_code
    verification_code_func = content.find("def get_latest_verification_code(self, user_id:")
    if verification_code_func > 0:
        # البحث عن بداية جسم الدالة
        function_body_start = content.find(":", verification_code_func) + 1
        function_body_start = content.find("\n", function_body_start) + 1
        
        # تحديد المسافة البادئة
        indent = ""
        for char in content[function_body_start:function_body_start+20]:
            if char.isspace():
                indent += char
            else:
                break
        
        # إضافة المتغير العالمي
        global_var = f"{indent}global last_processed_email_id\n"
        content = content[:function_body_start] + global_var + content[function_body_start:]
        
        # البحث عن حلقة معالجة الرسائل
        for_loop = content.find("for msg in messages:", verification_code_func)
        if for_loop > 0:
            # البحث عن استخراج معرف الرسالة
            msg_id_line = content.find("msg_id = msg", for_loop)
            if msg_id_line > 0:
                # العثور على نهاية سطر استخراج المعرف
                end_of_line = content.find("\n", msg_id_line) + 1
                
                # إضافة التحقق من البريد المكرر
                duplicate_check = f"""
{indent}    # التحقق مما إذا كان هذا البريد الإلكتروني قد تمت معالجته بالفعل
{indent}    if msg_id == last_processed_email_id:
{indent}        logger.info(f"تمت معالجة هذا البريد الإلكتروني بالفعل: {{msg_id}}")
{indent}        continue
"""
                content = content[:end_of_line] + duplicate_check + content[end_of_line:]
            
            # البحث عن مكان إرجاع كود التحقق
            return_verification = re.search(r'(\s+)return\s+\{\s*["\']code["\']', content[for_loop:])
            if return_verification:
                return_indent = return_verification.group(1)
                return_pos = for_loop + return_verification.start()
                
                # إضافة تحديث معرف آخر بريد تمت معالجته
                update_last_id = f"""
{return_indent}# تحديث معرف آخر بريد تمت معالجته
{return_indent}last_processed_email_id = msg_id

"""
                content = content[:return_pos] + update_last_id + content[return_pos:]
                print("✓ تم تحديث دالة get_latest_verification_code")
    
    # 4. إضافة معالج الخطأ العام
    main_function = content.find("def main():")
    if main_function > 0:
        # البحث عن سطر بدء تشغيل البوت
        run_polling = content.find("application.run_polling(", main_function)
        if run_polling > 0:
            # تحديد المسافة البادئة
            lines = content[main_function:run_polling].split("\n")
            indent = "    "  # المسافة البادئة الافتراضية
            for line in reversed(lines):
                if line.strip().startswith("application."):
                    indent = line[:line.find("application")]
                    break
            
            # إضافة معالج الخطأ
            error_handler = f"""
{indent}# إضافة معالج الأخطاء
{indent}async def error_handler(update, context):
{indent}    \"\"\"تسجيل الأخطاء التي تسببها التحديثات.\"\"\"
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
            content = content[:run_polling] + error_handler + content[run_polling:]
            print("✓ تمت إضافة معالج الخطأ العام")
    
    # 5. إضافة try/except لعمليات تعديل الرسائل
    edit_message_pattern = re.compile(r'(\s+)(await query\.edit_message_text\([^)]+\))(\s*(?!except))')
    
    # العثور على جميع التطابقات
    matches = list(edit_message_pattern.finditer(content))
    offset = 0
    
    # معالجة كل تطابق
    for match in matches:
        indent = match.group(1)
        edit_call = match.group(2)
        match_start = match.start() + offset
        match_end = match.end() + offset
        
        # استبدال بنسخة مع try/except
        safe_version = f"""
{indent}try:
{indent}    {edit_call}
{indent}except telegram.error.BadRequest as e:
{indent}    logger.error(f"فشل في تعديل الرسالة: {{e}}")
{indent}    try:
{indent}        await context.bot.send_message(
{indent}            chat_id=query.message.chat_id,
{indent}            text="لم يتم العثور على الرسالة أو لا يمكن تعديلها. إليك رسالة جديدة."
{indent}        )
{indent}    except Exception as e2:
{indent}        logger.error(f"فشل في إرسال رسالة جديدة: {{e2}}")"""
        
        content = content[:match_start] + safe_version + content[match_end:]
        offset += len(safe_version) - (match_end - match_start)
    
    if len(matches) > 0:
        print(f"✓ تمت إضافة معالجة الأخطاء لـ {len(matches)} استدعاءات edit_message_text")
    
    return content

if __name__ == "__main__":
    main() 