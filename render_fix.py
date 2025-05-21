#!/usr/bin/env python3
"""
أداة لإصلاح مشاكل تشغيل البوت على منصة Render
"""

import os
import json
import requests
import base64
from dotenv import load_dotenv
import logging

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_env_variables():
    """إنشاء ملف .env مناسب لبيئة Render"""
    logger.info("إنشاء ملف .env للاستخدام مع Render...")
    
    env_content = """TELEGRAM_BOT_TOKEN=7698638945:AAG9v9FgDUbe4gpN4IBFc1LlBjkaX9-K0xw
TARGET_EMAIL=ahmedalramah000@gmail.com
PASSWORD=0001A@hmEd_Ram4h!
EMAIL_SENDERS=no-reply@openai.com,login-code@openai.com,noreply@tm.openai.com
CODE_SEARCH_MINUTES=60
RATE_LIMIT_PER_USER=20
USE_APP_PASSWORD=true
APP_PASSWORD="""
    
    # تخمين كلمة مرور التطبيق من القيم المتاحة في متغيرات البيئة
    app_password = os.environ.get('APP_PASSWORD', '')
    
    if app_password:
        env_content += app_password
    else:
        logger.warning("APP_PASSWORD غير متوفر في متغيرات البيئة!")
    
    env_content += "\nTELEGRAM_CHAT_ID="
    admin_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    if admin_chat_id:
        env_content += admin_chat_id
    
    with open('.env', 'w', encoding='utf-8') as env_file:
        env_file.write(env_content)
    
    logger.info("تم إنشاء ملف .env بنجاح!")
    
    # تحميل المتغيرات البيئية مباشرة
    load_dotenv()

def create_dummy_token():
    """إنشاء ملف token.json وهمي لتجنب أخطاء التحقق"""
    logger.info("إنشاء ملف token.json وهمي...")
    
    dummy_token = {
        "token": "dummy_token",
        "refresh_token": "dummy_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "dummy_client_id",
        "client_secret": "dummy_secret",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expiry": "2099-12-31T23:59:59Z"
    }
    
    with open('token.json', 'w', encoding='utf-8') as token_file:
        json.dump(dummy_token, token_file)
    
    logger.info("تم إنشاء ملف token.json بنجاح!")

def create_dummy_credentials():
    """إنشاء ملف credentials.json.json وهمي"""
    logger.info("إنشاء ملف credentials.json.json وهمي...")
    
    dummy_credentials = {
        "installed": {
            "client_id": "dummy_client_id.apps.googleusercontent.com",
            "project_id": "dummy-project",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "dummy_secret",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open('credentials.json.json', 'w', encoding='utf-8') as creds_file:
        json.dump(dummy_credentials, creds_file)
    
    logger.info("تم إنشاء ملف credentials.json.json بنجاح!")

def modify_py_files():
    """تعديل ملفات Python للتوافق مع بيئة Render"""
    logger.info("تعديل keep_alive.py لتشغيله على Render...")
    
    keep_alive_content = """
from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "بوت تلجرام للحصول على أكواد ChatGPT قيد التشغيل!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
"""
    
    with open('keep_alive.py', 'w', encoding='utf-8') as keep_alive_file:
        keep_alive_file.write(keep_alive_content)
    
    logger.info("تم تعديل keep_alive.py بنجاح!")

def main():
    """الوظيفة الرئيسية لإعداد البوت على Render"""
    logger.info("بدء إعداد البيئة لـ Render...")
    
    # إنشاء ملف .env
    setup_env_variables()
    
    # إنشاء ملفات وهمية للمصادقة
    create_dummy_token()
    create_dummy_credentials()
    
    # تعديل ملفات لتتوافق مع Render
    modify_py_files()
    
    logger.info("تم إعداد البيئة بنجاح! البوت جاهز للتشغيل على Render.")

if __name__ == "__main__":
    main() 