#!/usr/bin/env python3
"""
Script to set up Gmail App Password authentication for the Telegram ChatGPT codes bot.
This is an alternative to OAuth authentication that avoids token expiration issues.
"""

import os
import sys
import re
import getpass
from dotenv import load_dotenv

# Load existing environment variables
load_dotenv()

def setup_app_password():
    """Set up the App Password for Gmail authentication"""
    print("\n=== إعداد المصادقة باستخدام App Password لبريد Gmail ===\n")
    print("هذه الطريقة تساعد على تجنب مشاكل انتهاء صلاحية التوكن (invalid_grant).")
    print("سيتم إنشاء ملف .env جديد مع إعدادات App Password.\n")
    
    # Get existing values from .env file or use defaults
    telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    target_email = os.environ.get('TARGET_EMAIL', 'ahmedalramah000@gmail.com')
    password = os.environ.get('PASSWORD', '0001A@hmEd_Ram4h!')
    email_senders = os.environ.get('EMAIL_SENDERS', 'no-reply@openai.com,login-code@openai.com,noreply@tm.openai.com')
    code_search_minutes = os.environ.get('CODE_SEARCH_MINUTES', '60')
    rate_limit_per_user = os.environ.get('RATE_LIMIT_PER_USER', '10')
    
    # Get App Password from user
    print("خطوات الحصول على App Password من Google:")
    print("1. قم بتفعيل المصادقة الثنائية على حساب Google الخاص بك من الرابط:")
    print("   https://myaccount.google.com/security")
    print("2. انتقل إلى صفحة كلمات مرور التطبيقات من الرابط:")
    print("   https://myaccount.google.com/apppasswords")
    print("3. اختر 'تطبيق آخر' واكتب اسمًا مثل 'بوت تلجرام'")
    print("4. انسخ كلمة المرور المكونة من 16 حرفًا\n")
    
    app_password = getpass.getpass("أدخل كلمة مرور التطبيق المكونة من 16 حرفًا (App Password): ")
    
    # Validate App Password format (16 characters, no spaces)
    app_password = app_password.replace(" ", "")
    if len(app_password) != 16:
        print(f"\n⚠️ تنبيه: طول كلمة المرور هو {len(app_password)} حرفًا، ولكن يجب أن تكون 16 حرفًا.")
        confirm = input("هل تريد المتابعة على أي حال؟ (نعم/لا): ").strip().lower()
        if confirm != "نعم" and confirm != "yes" and confirm != "y":
            print("تم إلغاء الإعداد.")
            sys.exit(1)
    
    # Ask for Telegram bot token if not already set
    if not telegram_bot_token:
        telegram_bot_token = input("\nأدخل توكن بوت التلجرام (TELEGRAM_BOT_TOKEN): ")
    
    # Ask for Telegram chat ID if not already set
    if not telegram_chat_id:
        telegram_chat_id = input("\nأدخل معرف محادثة التلجرام (TELEGRAM_CHAT_ID): ")
    
    # Ask for target email if different from default
    email_input = input(f"\nأدخل البريد الإلكتروني المستهدف (اترك فارغًا للإبقاء على {target_email}): ")
    if email_input:
        target_email = email_input
    
    # Create new .env file
    with open(".env", "w", encoding="utf-8") as env_file:
        env_file.write(f"# إعدادات التليجرام\n")
        env_file.write(f"TELEGRAM_BOT_TOKEN={telegram_bot_token}\n")
        env_file.write(f"TELEGRAM_CHAT_ID={telegram_chat_id}\n\n")
        
        env_file.write(f"# البريد الإلكتروني المستخدم\n")
        env_file.write(f"TARGET_EMAIL={target_email}\n")
        env_file.write(f"PASSWORD={password}\n\n")
        
        env_file.write(f"# إعدادات طريقة المصادقة - تم ضبطها لاستخدام App Password\n")
        env_file.write(f"USE_APP_PASSWORD=true\n")
        env_file.write(f"APP_PASSWORD={app_password}\n\n")
        
        env_file.write(f"# قائمة مرسلي البريد الإلكتروني المسموح بهم\n")
        env_file.write(f"EMAIL_SENDERS={email_senders}\n\n")
        
        env_file.write(f"# المدة الزمنية للبحث عن الأكواد (بالدقائق)\n")
        env_file.write(f"CODE_SEARCH_MINUTES={code_search_minutes}\n\n")
        
        env_file.write(f"# الحد الأقصى للاستعلامات لكل مستخدم\n")
        env_file.write(f"RATE_LIMIT_PER_USER={rate_limit_per_user}\n\n")
        
        env_file.write(f"# ملفات Gmail API (غير مستخدمة مع App Password)\n")
        env_file.write(f"GMAIL_CREDENTIALS_FILE=credentials.json.json\n")
        env_file.write(f"GMAIL_TOKEN_FILE=token.json\n")
    
    print("\n✅ تم إنشاء ملف .env بنجاح مع إعدادات App Password!")
    print("\nالآن يمكنك تشغيل البوت باستخدام الأمر:")
    print("python gmail_bot.py")
    print("\nسيستخدم البوت App Password بدلاً من OAuth، مما يمنع مشاكل انتهاء صلاحية التوكن.")
    
    # Attempt to remove token.json if it exists
    if os.path.exists("token.json"):
        try:
            os.remove("token.json")
            print("\nتم حذف ملف token.json القديم لتجنب أي تداخل مع الطريقة الجديدة.")
        except Exception as e:
            print(f"\nملاحظة: لم نتمكن من حذف ملف token.json: {e}")
            print("يمكنك حذفه يدويًا إذا واجهتك مشاكل.")

if __name__ == "__main__":
    setup_app_password() 