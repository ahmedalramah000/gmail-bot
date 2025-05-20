#!/usr/bin/env python3
"""
Script to fix the Gmail-Telegram bot issues.
This script creates a fixed version of the bot with proper error handling and duplicate prevention.
"""

import os
import shutil
import re
import sys

def main():
    print("Gmail-Telegram Bot Fix Tool")
    print("==========================")
    
    # Check if source file exists
    if not os.path.exists("gmail_bot.py"):
        print("Error: Source file gmail_bot.py not found.")
        return False
        
    # Create backup if needed
    backup_file = "gmail_bot.py.fix-backup"
    if not os.path.exists(backup_file):
        print(f"Creating backup of original file as {backup_file}...")
        shutil.copy("gmail_bot.py", backup_file)
    
    # Create fixed_gmail_bot.py
    output_file = "fixed_gmail_bot.py"
    print(f"Creating fixed version as {output_file}...")
    
    try:
        # Read source file
        with open("gmail_bot.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # Apply fixes
        fixed_content = apply_fixes(content)
        
        # Write fixed file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(fixed_content)
            
        print(f"Successfully created {output_file}")
        print("\nYou can now run the fixed bot with:")
        print(f"python {output_file}")
        return True
    except Exception as e:
        print(f"Error during fix process: {e}")
        return False

def apply_fixes(content):
    """Apply all fixes to the bot code"""
    
    # 1. Fix indentation issues in button_callback
    print("- Fixing button_callback indentation issues...")
    pattern = r'try:\s+await query\.edit_message_text\("🔍 جاري البحث عن آخر كود\.\.\. انتظر قليلاً"\)\s+except telegram\.error\.BadRequest as e:'
    replacement = '''try:
            await query.edit_message_text("🔍 جاري البحث عن آخر كود... انتظر قليلاً")
        except telegram.error.BadRequest as e:'''
    content = re.sub(pattern, replacement, content)
    
    # 2. Add global variables for tracking processed items
    print("- Adding global tracking variables...")
    if "processed_callbacks = set()" not in content:
        logger_section = content.find("logger = logging.getLogger(__name__)")
        if logger_section > 0:
            insert_pos = content.find("\n", logger_section) + 1
            globals_code = '''
# مجموعة لتخزين معرفات الاستجابات المعالجة
processed_callbacks = set()
# تخزين معرف آخر بريد إلكتروني تمت معالجته
last_processed_email_id = None
'''
            content = content[:insert_pos] + globals_code + content[insert_pos:]
    
    # 3. Update button_callback method for duplicate prevention
    print("- Enhancing button_callback to prevent duplicate processing...")
    button_callback_start = content.find("async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):")
    if button_callback_start > 0:
        # Find the beginning of function body
        function_body_start = content.find(":", button_callback_start) + 1
        function_body_start = content.find("\n", function_body_start) + 1
        
        # Get the indentation of the function body
        indentation = ""
        for char in content[function_body_start:]:
            if char.isspace():
                indentation += char
            else:
                break
        
        # Add code for duplicate prevention
        duplicate_check_code = f'''
{indentation}global TUTORIAL_VIDEO_FILE_ID, processed_callbacks, last_processed_email_id
{indentation}query = update.callback_query
{indentation}user_id = str(update.effective_user.id)
{indentation}
{indentation}# تجنب معالجة نفس الاستجابة عدة مرات
{indentation}callback_id = f"{{query.message.message_id}}_{{query.data}}"
{indentation}if callback_id in processed_callbacks:
{indentation}    await query.answer("جاري المعالجة...")
{indentation}    return
{indentation}    
{indentation}# إضافة إلى الاستجابات المعالجة
{indentation}processed_callbacks.add(callback_id)
'''
        # Remove the old function body start and replace with our enhanced version
        old_body_start = content[function_body_start:content.find("await query.answer()", function_body_start) + len("await query.answer()")]
        content = content.replace(old_body_start, duplicate_check_code)
    
    # 4. Update get_latest_verification_code to avoid duplicate emails
    print("- Updating get_latest_verification_code to prevent duplicate email processing...")
    verification_code_start = content.find("def get_latest_verification_code(self, user_id: str)")
    if verification_code_start > 0:
        # Add global variable reference
        function_body_start = content.find(":", verification_code_start) + 1
        function_body_start = content.find("\n", function_body_start) + 1
        
        # Get indentation
        indentation = ""
        for char in content[function_body_start:]:
            if char.isspace():
                indentation += char
            else:
                break
                
        # Add global reference
        global_ref = f"{indentation}global last_processed_email_id\n"
        content = content[:function_body_start] + global_ref + content[function_body_start:]
        
        # Find the message processing loop
        for_msg_in_messages = content.find("for msg in messages:", verification_code_start)
        if for_msg_in_messages > 0:
            # Get the indentation for the loop body
            loop_body_start = content.find("\n", for_msg_in_messages) + 1
            loop_indentation = ""
            for char in content[loop_body_start:]:
                if char.isspace():
                    loop_indentation += char
                else:
                    break
            
            # Find message ID extraction
            msg_id_pattern = re.search(r"(\s+)(msg_id = msg.*?\n)", content[for_msg_in_messages:])
            if msg_id_pattern:
                msg_id_line_end = for_msg_in_messages + msg_id_pattern.end()
                
                # Add check for already processed emails
                duplicate_check = f'''
{loop_indentation}# التحقق مما إذا كان هذا البريد الإلكتروني قد تمت معالجته بالفعل
{loop_indentation}if msg_id == last_processed_email_id:
{loop_indentation}    logger.info(f"تمت معالجة هذا البريد الإلكتروني بالفعل: {{msg_id}}")
{loop_indentation}    continue
'''
                content = content[:msg_id_line_end] + duplicate_check + content[msg_id_line_end:]
                
                # Find return statement with verification code
                return_pattern = re.search(r'(\s+)return\s+\{\s*["\']code["\']\s*:\s*verification_code', content[for_msg_in_messages:])
                if return_pattern:
                    return_pos = for_msg_in_messages + return_pattern.start()
                    return_indentation = return_pattern.group(1)
                    
                    # Add update to last_processed_email_id
                    update_last_id = f'''
{return_indentation}# حفظ معرف الرسالة كمعالجة لتجنب معالجتها مرة أخرى
{return_indentation}last_processed_email_id = msg_id

'''
                    content = content[:return_pos] + update_last_id + content[return_pos:]
    
    # 5. Add error handler in main function
    print("- Adding global error handler...")
    main_func = content.find("def main():")
    if main_func > 0:
        # Find the application.run_polling line
        run_polling = content.find("application.run_polling(", main_func)
        if run_polling > 0:
            # Get correct indentation
            indentation = "    "  # Default indentation
            main_lines = content[main_func:run_polling].splitlines()
            for line in main_lines:
                if "application." in line:
                    indentation = line[:line.find("application")]
                    break
            
            # Add error handler
            error_handler = f'''
{indentation}# Add error handler
{indentation}async def error_handler(update, context):
{indentation}    """تسجيل الأخطاء التي تسببها التحديثات."""
{indentation}    logger.error(f"حدث استثناء أثناء معالجة تحديث: {{context.error}}")
{indentation}    
{indentation}    # إخطار المستخدم بالخطأ إذا كان ذلك مناسبًا
{indentation}    if update and update.effective_chat:
{indentation}        try:
{indentation}            await context.bot.send_message(
{indentation}                chat_id=update.effective_chat.id,
{indentation}                text="حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى."
{indentation}            )
{indentation}        except Exception as e:
{indentation}            logger.error(f"فشل في إرسال رسالة الخطأ: {{e}}")
{indentation}            
{indentation}application.add_error_handler(error_handler)
'''
            content = content[:run_polling] + error_handler + content[run_polling:]
    
    # 6. Fix all remaining try/except blocks for message editing
    print("- Adding error handling for all message editing operations...")
    content = fix_message_editing(content)
    
    return content

def fix_message_editing(content):
    """Add proper error handling to all message editing operations"""
    # Pattern for edit_message_text without try/except
    unsafe_edit_pattern = re.compile(r'(\s+)await query\.edit_message_text\(((?!try).)*?\)\s*(?!except)', re.DOTALL)
    
    # Find all instances
    matches = list(unsafe_edit_pattern.finditer(content))
    offset = 0
    
    # Process each match
    for match in matches:
        indentation = match.group(1)
        full_match = match.group(0)
        match_start = match.start() + offset
        match_end = match.end() + offset
        
        # Replace with try/except version
        safe_version = f'''
{indentation}try:
{full_match}
{indentation}except telegram.error.BadRequest as e:
{indentation}    logger.error(f"فشل في تعديل الرسالة: {{e}}")
{indentation}    try:
{indentation}        await context.bot.send_message(
{indentation}            chat_id=query.message.chat_id,
{indentation}            text=text,  # Use the same text parameter
{indentation}            reply_markup=reply_markup,  # Use the same reply_markup
{indentation}            parse_mode='HTML'
{indentation}        )
{indentation}    except Exception as e2:
{indentation}        logger.error(f"فشل في إرسال رسالة جديدة: {{e2}}")'''
        
        # Special case handling
        if "text=" not in full_match:
            # Simplify for cases where we can't automatically add parameters
            safe_version = f'''
{indentation}try:
{full_match}
{indentation}except telegram.error.BadRequest as e:
{indentation}    logger.error(f"فشل في تعديل الرسالة: {{e}}")
{indentation}    # إذا فشل التعديل، نحاول إرسال رسالة جديدة
{indentation}    # تم تجاهل هذا الاستبدال التلقائي لأنه يتطلب معالجة خاصة'''
        
        # Apply the replacement
        content = content[:match_start] + safe_version + content[match_end:]
        offset += len(safe_version) - len(full_match)
    
    return content

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 