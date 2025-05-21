from flask import Flask
from threading import Thread
import os
import logging
import requests

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask('')

@app.route('/')
def home():
    return "بوت تلجرام للحصول على أكواد ChatGPT قيد التشغيل!"

def run():
    # قراءة PORT من متغيرات البيئة التي توفرها منصة Render
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"تشغيل خادم الويب على المنفذ {port}")
    app.run(host='0.0.0.0', port=port)

def download_credentials():
    """وظيفة لتحميل ملفات الاعتماد من روابط مباشرة"""
    # استخراج الروابط من متغيرات البيئة
    creds_url = os.environ.get('CREDENTIALS_URL')
    token_url = os.environ.get('TOKEN_URL')
    
    # تحميل ملف credentials.json.json إذا لم يكن موجودًا وتم تحديد الرابط
    if creds_url and not os.path.exists("credentials.json.json"):
        try:
            logger.info("تحميل ملف credentials.json.json...")
            r = requests.get(creds_url)
            if r.status_code == 200:
                with open("credentials.json.json", "wb") as f:
                    f.write(r.content)
                logger.info("تم تحميل ملف credentials.json.json بنجاح")
            else:
                logger.error(f"فشل تحميل credentials.json.json. رمز الحالة: {r.status_code}")
        except Exception as e:
            logger.error(f"خطأ أثناء تحميل credentials.json.json: {e}")
    
    # تحميل ملف token.json إذا لم يكن موجودًا وتم تحديد الرابط
    if token_url and not os.path.exists("token.json"):
        try:
            logger.info("تحميل ملف token.json...")
            r = requests.get(token_url)
            if r.status_code == 200:
                with open("token.json", "wb") as f:
                    f.write(r.content)
                logger.info("تم تحميل ملف token.json بنجاح")
            else:
                logger.error(f"فشل تحميل token.json. رمز الحالة: {r.status_code}")
        except Exception as e:
            logger.error(f"خطأ أثناء تحميل token.json: {e}")
    
    # إنشاء ملفات وهمية إذا لم تكن موجودة ولم يتم تحديد روابط التحميل
    if not os.path.exists("credentials.json.json") and not creds_url:
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
            import json
            json.dump(dummy_credentials, creds_file)
        
        logger.info("تم إنشاء ملف credentials.json.json وهمي بنجاح!")
    
    if not os.path.exists("token.json") and not token_url:
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
            import json
            json.dump(dummy_token, token_file)
        
        logger.info("تم إنشاء ملف token.json وهمي بنجاح!")

def keep_alive():
    """الحفاظ على تشغيل البوت وتحميل ملفات الاعتماد"""
    # تحميل ملفات الاعتماد أولاً
    download_credentials()
    
    # بدء خادم الويب
    t = Thread(target=run)
    t.start() 