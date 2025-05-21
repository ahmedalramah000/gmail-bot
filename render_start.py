#!/usr/bin/env python3
"""
ملف تشغيل البوت على منصة Render
"""

import os
import sys
import logging
import subprocess
import time

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_env_file():
    """التحقق من وجود ملف .env وإنشائه إذا لم يكن موجودًا"""
    if not os.path.exists('.env'):
        logger.info("ملف .env غير موجود، سيتم إنشاؤه...")
        
        # استخراج القيم من متغيرات البيئة
        telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        target_email = os.environ.get('TARGET_EMAIL', 'ahmedalramah000@gmail.com')
        password = os.environ.get('PASSWORD', '0001A@hmEd_Ram4h!')
        app_password = os.environ.get('APP_PASSWORD', '')
        telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        
        # إنشاء محتوى الملف
        env_content = f"""TELEGRAM_BOT_TOKEN={telegram_token}
TARGET_EMAIL={target_email}
PASSWORD={password}
EMAIL_SENDERS=no-reply@openai.com,login-code@openai.com,noreply@tm.openai.com
CODE_SEARCH_MINUTES=60
RATE_LIMIT_PER_USER=20
USE_APP_PASSWORD=true
APP_PASSWORD={app_password}
TELEGRAM_CHAT_ID={telegram_chat_id}
"""
        
        try:
            with open('.env', 'w', encoding='utf-8') as env_file:
                env_file.write(env_content)
            logger.info("تم إنشاء ملف .env بنجاح!")
        except Exception as e:
            logger.error(f"فشل في إنشاء ملف .env: {e}")
            return False
    
    return True

def check_token_files():
    """التحقق من وجود ملفات المصادقة وإنشائها إذا لم تكن موجودة"""
    from render_fix import create_dummy_token, create_dummy_credentials
    
    if not os.path.exists('token.json'):
        logger.info("ملف token.json غير موجود، سيتم إنشاؤه...")
        create_dummy_token()
    
    if not os.path.exists('credentials.json.json'):
        logger.info("ملف credentials.json.json غير موجود، سيتم إنشاؤه...")
        create_dummy_credentials()
    
    return True

def setup_render_environment():
    """إعداد بيئة Render"""
    try:
        # تنفيذ سكريبت الإصلاح
        logger.info("جاري تنفيذ سكريبت إصلاح Render...")
        subprocess.run([sys.executable, "render_fix.py"], check=True)
        logger.info("تم تنفيذ سكريبت الإصلاح بنجاح!")
        return True
    except Exception as e:
        logger.error(f"فشل في إعداد بيئة Render: {e}")
        return False

def main():
    """الوظيفة الرئيسية لتشغيل البوت"""
    logger.info("بدء تشغيل البوت على منصة Render...")
    
    # التحقق من وجود ملف .env
    if not check_env_file():
        logger.error("فشل في إعداد ملف .env")
        return
    
    # إعداد بيئة Render
    if not setup_render_environment():
        logger.error("فشل في إعداد بيئة Render")
        return
    
    # التحقق من وجود ملفات المصادقة
    if not check_token_files():
        logger.error("فشل في إعداد ملفات المصادقة")
        return
    
    # تشغيل البوت
    logger.info("جاري تشغيل البوت...")
    try:
        subprocess.run([sys.executable, "gmail_bot.py"], check=True)
    except Exception as e:
        logger.error(f"فشل في تشغيل البوت: {e}")

if __name__ == "__main__":
    main() 