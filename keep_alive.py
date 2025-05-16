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
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

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

def keep_alive():
    """الحفاظ على تشغيل البوت وتحميل ملفات الاعتماد"""
    # تحميل ملفات الاعتماد أولاً
    download_credentials()
    
    # بدء خادم الويب
    t = Thread(target=run)
    t.start() 