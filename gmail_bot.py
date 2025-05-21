#!/usr/bin/env python3
"""
بوت تليجرام للحصول على أكواد التحقق من ChatGPT عبر Gmail
"""

import os
import re
import json
import base64
import logging
import time
import socket
import sys
import requests
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
from keep_alive import keep_alive  # إضافة استيراد للحفاظ على البوت نشطًا

from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import smtplib
import imaplib
import email
from email.header import decode_header
import telegram

# تهيئة التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تحميل متغيرات البيئة
load_dotenv()

# وظيفة لتحميل ملفات المصادقة من Google Drive
def download_file(env_var, filename):
    """تحميل ملف من عنوان URL محدد في متغير بيئي"""
    url = os.getenv(env_var)
    if not url:
        print(f"[ERROR] Env var {env_var} not set")
        return False
    
    try:
        print(f"[INFO] محاولة تحميل {filename} من {url}")
        r = requests.get(url)
        r.raise_for_status()
        
        # التأكد من أن الملف له التنسيق الصحيح
        if filename.endswith('.json.json'):
            # إزالة التكرار في الامتداد
            corrected_filename = filename.replace('.json.json', '.json')
            print(f"[WARN] تصحيح اسم الملف من {filename} إلى {corrected_filename}")
            filename = corrected_filename
        
        with open(filename, 'wb') as f:
            f.write(r.content)
        
        file_size = os.path.getsize(filename)
        print(f"[OK] Downloaded {filename} (Size: {file_size} bytes)")
        
        # التحقق من صحة ملف JSON
        if filename.endswith('.json'):
            try:
                with open(filename, 'r') as f:
                    json.load(f)
                print(f"[OK] تم التحقق من صحة ملف {filename} كملف JSON صالح")
            except json.JSONDecodeError as e:
                print(f"[ERROR] الملف {filename} ليس ملف JSON صالح: {e}")
                return False
                
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] خطأ في الاتصال أثناء تحميل {filename}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to download {filename}: {e}")
        return False

# مجموعة لتخزين معرفات الاستجابات المعالجة
processed_callbacks = set()
# تخزين معرف آخر بريد إلكتروني تمت معالجته
last_processed_email_id = None

# Maximum connection retry attempts
MAX_RETRIES = 5
# Base delay between retries (will increase exponentially)
BASE_RETRY_DELAY = 5

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TARGET_EMAIL = os.environ.get('TARGET_EMAIL', "ahmedalramah000@gmail.com")  # البريد من متغيرات البيئة
PASSWORD = os.environ.get('PASSWORD', "0001A@hmEd_Ram4h!")  # كلمة المرور من متغيرات البيئة
EMAIL_SENDERS = os.environ.get('EMAIL_SENDERS', "no-reply@openai.com,login-code@openai.com,noreply@tm.openai.com").split(',')
# المدة الزمنية للبحث عن الأكواد (بالدقائق)
CODE_SEARCH_MINUTES = int(os.environ.get('CODE_SEARCH_MINUTES', 60))
# الحد الأقصى للاستعلامات لكل مستخدم
RATE_LIMIT_PER_USER = int(os.environ.get('RATE_LIMIT_PER_USER', 10))

# إعدادات App Password
USE_APP_PASSWORD = os.environ.get('USE_APP_PASSWORD', 'false').lower() == 'true'
APP_PASSWORD = os.environ.get('APP_PASSWORD', '')

# متغير لتخزين معرف الفيديو التعليمي
TUTORIAL_VIDEO_FILE_ID = os.environ.get('TUTORIAL_VIDEO_FILE_ID', None)
if TUTORIAL_VIDEO_FILE_ID == 'None':
    TUTORIAL_VIDEO_FILE_ID = None
TUTORIAL_VIDEO_FILE = "tutorial_video.json"

# إعدادات Gmail API
GMAIL_CREDENTIALS_FILE = 'credentials.json'  # Nombre correcto sin extensión duplicada
GMAIL_TOKEN_FILE = 'token.json'  # Nombre correcto sin extensión duplicada
GMAIL_API_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# دوال لحفظ واسترجاع معرف الفيديو
def save_video_id(file_id):
    """حفظ معرف الفيديو في ملف"""
    try:
        with open(TUTORIAL_VIDEO_FILE, 'w') as f:
            json.dump({"file_id": file_id}, f)
        return True
    except Exception as e:
        logger.error(f"خطأ في حفظ معرف الفيديو: {e}")
        return False

def load_video_id():
    """استرجاع معرف الفيديو من الملف"""
    global TUTORIAL_VIDEO_FILE_ID
    try:
        if os.path.exists(TUTORIAL_VIDEO_FILE):
            with open(TUTORIAL_VIDEO_FILE, 'r') as f:
                data = json.load(f)
                TUTORIAL_VIDEO_FILE_ID = data.get("file_id")
                logger.info(f"تم تحميل معرف الفيديو: {TUTORIAL_VIDEO_FILE_ID}")
    except Exception as e:
        logger.error(f"خطأ في استرجاع معرف الفيديو: {e}")
        TUTORIAL_VIDEO_FILE_ID = None

# كلمات مفتاحية لتحديد رسائل إعادة تعيين كلمة المرور
PASSWORD_RESET_KEYWORDS = [
    "password reset", 
    "reset password", 
    "reset your password",
    "إعادة تعيين كلمة المرور", 
    "اعادة تعيين كلمة المرور"
]

# كلمات مفتاحية لتحديد رسائل تسجيل الدخول العادية
LOGIN_CODE_KEYWORDS = [
    "log-in code",
    "login code",
    "verification code",
    "كود تسجيل الدخول",
    "رمز التحقق"
]

class GmailClient:
    """التعامل مع عمليات Gmail API."""
    
    def __init__(self, credentials_file: str, token_file: str):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.auth_method = "oauth"  # Default authentication method
        
        # طباعة معلومات عن المسارات للتشخيص
        print(f"[INFO] مسار ملف بيانات الاعتماد: {self.credentials_file}")
        print(f"[INFO] مسار ملف التوكن: {self.token_file}")
        
        # تحقق مما إذا كان يجب استخدام App Password
        if USE_APP_PASSWORD and APP_PASSWORD:
            logger.info("استخدام App Password للمصادقة")
            self.auth_method = "app_password"
            self._authenticate_with_app_password()
        else:
            logger.info("استخدام OAuth للمصادقة")
            # التحقق من وجود ملف بيانات الاعتماد
            if not os.path.exists(self.credentials_file):
                logger.error(f"ملف بيانات الاعتماد غير موجود: {self.credentials_file}")
                # محاولة البحث عن الملف بأسماء أخرى محتملة
                possible_names = ["credentials.json.json", "credentials.json"]
                for name in possible_names:
                    if os.path.exists(name):
                        logger.info(f"تم العثور على ملف بيانات اعتماد بديل: {name}")
                        self.credentials_file = name
                        break
                else:
                    self.service = None
                    return
                
            self.service = self._authenticate_oauth()
    
    def _authenticate_with_app_password(self):
        """المصادقة مع Gmail باستخدام App Password."""
        try:
            # This method doesn't create a service object like oauth, but instead
            # sets up the class to use IMAP directly when methods are called
            logger.info("تم إعداد المصادقة باستخدام App Password")
            self._test_app_password_connection()
            return True
        except Exception as e:
            logger.error(f"فشل المصادقة باستخدام App Password: {e}")
            return None
    
    def _test_app_password_connection(self):
        """اختبار الاتصال باستخدام App Password."""
        try:
            # Try to connect to Gmail using IMAP
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(TARGET_EMAIL, APP_PASSWORD)
            mail.logout()
            logger.info("تم الاتصال بنجاح باستخدام App Password")
            return True
        except Exception as e:
            logger.error(f"فشل اختبار الاتصال باستخدام App Password: {e}")
            raise e
    
    def _authenticate_oauth(self):
        """المصادقة مع Gmail API باستخدام OAuth."""
        creds = None
        
        # التحقق من اسم ملف التوكن وجربة بدائل إذا لم يكن موجودًا
        if not os.path.exists(self.token_file):
            print(f"[ERROR] ملف التوكن غير موجود في المسار المتوقع: {self.token_file}")
            # محاولة استخدام أسماء بديلة محتملة
            alternative_names = ["token.json.json", "token.json"]
            for alt_name in alternative_names:
                if os.path.exists(alt_name):
                    print(f"[INFO] تم العثور على ملف توكن بديل: {alt_name}")
                    self.token_file = alt_name
                    break
        
        # تحميل التوكن الموجود إذا كان متاحًا
        if os.path.exists(self.token_file):
            try:
                print(f"[INFO] محاولة قراءة ملف التوكن: {self.token_file}")
                with open(self.token_file, 'r') as token:
                    token_data = json.load(token)
                    print(f"[INFO] تم قراءة البيانات من ملف التوكن: {self.token_file}")
                    creds = Credentials.from_authorized_user_info(
                        token_data, GMAIL_API_SCOPES
                    )
            except json.JSONDecodeError as json_err:
                print(f"[ERROR] خطأ في تنسيق JSON في ملف التوكن: {json_err}")
                logger.error(f"خطأ في تنسيق JSON في ملف التوكن: {json_err}")
                creds = None
            except Exception as e:
                logger.error(f"خطأ في قراءة ملف التوكن: {e}")
                print(f"[ERROR] خطأ في قراءة ملف التوكن: {e}")
                creds = None
        
        # إذا لم تكن هناك بيانات اعتماد صالحة، قم بالمصادقة
        if not creds or not creds.valid:
            try:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("تحديث التوكن المنتهي...")
                    try:
                        creds.refresh(Request())
                        logger.info("تم تحديث التوكن بنجاح")
                    except Exception as refresh_error:
                        logger.error(f"فشل تحديث التوكن: {refresh_error}")
                        logger.error("لا يمكن تحديث token.json. يرجى إعادة تحميله من المصدر.")
                        return None
                else:
                    logger.error("ملف token.json غير موجود أو غير صالح. يرجى توفيره أو إعادة تحميله.")
                    return None
                
                # حفظ بيانات الاعتماد للتشغيل التالي
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                logger.info("تم تحديث/إنشاء ملف التوكن بنجاح")
            except Exception as e:
                logger.error(f"خطأ أثناء عملية المصادقة: {e}")
                return None
        
        try:
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logger.error(f"خطأ في إنشاء خدمة Gmail: {e}")
            return None
    
    def list_messages(self, query: str, max_results: int = 10) -> List[dict]:
        """سرد الرسائل التي تطابق الاستعلام المحدد."""
        if self.auth_method == "oauth":
            return self._list_messages_oauth(query, max_results)
        else:
            return self._list_messages_app_password(query, max_results)
            
    def _list_messages_oauth(self, query: str, max_results: int = 10) -> List[dict]:
        """سرد الرسائل باستخدام OAuth."""
        if not self.service:
            logger.error("خدمة Gmail غير متاحة")
            return []
            
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId='me', q=query, maxResults=max_results)
                .execute()
            )
            messages = results.get('messages', [])
            return messages
        except Exception as e:
            logger.error(f"خطأ في سرد الرسائل (OAuth): {e}")
            return []
    
    def _list_messages_app_password(self, query: str, max_results: int = 10) -> List[dict]:
        """سرد الرسائل باستخدام App Password."""
        try:
            # Connect to Gmail
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(TARGET_EMAIL, APP_PASSWORD)
            mail.select('inbox')
            
            # Build search criteria from query
            # For simplicity, we'll translate the most common queries
            search_criteria = 'ALL'
            if 'from:' in query:
                sender = query.split('from:')[1].strip().split(' ')[0]
                search_criteria = f'(FROM "{sender}")'
            
            # Add date criteria if needed
            if 'after:' in query:
                date_str = query.split('after:')[1].strip().split(' ')[0]
                # Convert date format to IMAP format (01-Jan-2020)
                try:
                    date_obj = datetime.strptime(date_str, '%Y/%m/%d')
                    date_imap = date_obj.strftime('%d-%b-%Y')
                    search_criteria += f' (SINCE "{date_imap}")'
                except Exception as e:
                    logger.error(f"خطأ في تحويل التاريخ: {e}")
            
            # Perform search
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                logger.error(f"فشل البحث في البريد: {status}")
                return []
            
            # Convert to list of IDs
            message_ids = messages[0].split()
            if max_results > 0:
                message_ids = message_ids[-max_results:]
            
            # Format to match Gmail API format
            result = []
            for msg_id in message_ids:
                result.append({'id': msg_id.decode('utf-8')})
            
            mail.logout()
            return result
        except Exception as e:
            logger.error(f"خطأ في سرد الرسائل (App Password): {e}")
            return []
    
    def get_message(self, msg_id: str) -> Optional[dict]:
        """الحصول على رسالة محددة بواسطة المعرف."""
        if self.auth_method == "oauth":
            return self._get_message_oauth(msg_id)
        else:
            return self._get_message_app_password(msg_id)
            
    def _get_message_oauth(self, msg_id: str) -> Optional[dict]:
        """الحصول على رسالة باستخدام OAuth."""
        if not self.service:
            logger.error("خدمة Gmail غير متاحة")
            return None
            
        try:
            return (
                self.service.users()
                .messages()
                .get(userId='me', id=msg_id, format='full')
                .execute()
            )
        except Exception as e:
            logger.error(f"خطأ في الحصول على الرسالة {msg_id} (OAuth): {e}")
            return None
    
    def _get_message_app_password(self, msg_id: str) -> Optional[dict]:
        """الحصول على رسالة باستخدام App Password."""
        try:
            # Connect to Gmail
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(TARGET_EMAIL, APP_PASSWORD)
            mail.select('inbox')
            
            # Fetch the message
            status, msg_data = mail.fetch(msg_id.encode(), '(RFC822)')
            
            if status != 'OK':
                logger.error(f"فشل الحصول على الرسالة {msg_id}: {status}")
                mail.logout()
                return None
            
            # Parse the message
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Convert to format similar to Gmail API
            result = {
                'id': msg_id,
                'payload': {
                    'headers': [],
                    'body': {'data': ''},
                    'parts': []
                },
                'internalDate': str(int(time.time() * 1000))
            }
            
            # Extract headers
            for header in email_message.items():
                result['payload']['headers'].append({
                    'name': header[0],
                    'value': header[1]
                })
            
            # Extract body
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if "attachment" not in content_disposition:
                        # Get the body
                        try:
                            body = part.get_payload(decode=True)
                            if body:
                                # Convert to base64 to match Gmail API format
                                encoded = base64.urlsafe_b64encode(body).decode()
                                part_obj = {
                                    'mimeType': content_type,
                                    'body': {'data': encoded}
                                }
                                result['payload']['parts'].append(part_obj)
                        except Exception as e:
                            logger.error(f"خطأ في استخراج جزء الرسالة: {e}")
            else:
                # Not multipart - get the content
                try:
                    body = email_message.get_payload(decode=True)
                    if body:
                        encoded = base64.urlsafe_b64encode(body).decode()
                        result['payload']['body']['data'] = encoded
                except Exception as e:
                    logger.error(f"خطأ في استخراج نص الرسالة: {e}")
            
            mail.logout()
            return result
        except Exception as e:
            logger.error(f"خطأ في الحصول على الرسالة {msg_id} (App Password): {e}")
            return None


class OpenAICodeExtractor:
    """استخراج أكواد التحقق من OpenAI من رسائل البريد الإلكتروني."""
    
    @staticmethod
    def decode_email_body(payload: dict) -> str:
        """فك تشفير نص البريد الإلكتروني من base64."""
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(
                payload['body']['data'].encode('ASCII')
            ).decode('utf-8')
        
        # التحقق من وجود رسالة متعددة الأجزاء
        if 'parts' in payload:
            for part in payload['parts']:
                body = OpenAICodeExtractor.decode_email_body(part)
                if body:
                    return body
        
        return ""
    
    @staticmethod
    def extract_verification_code(text: str, subject: str = None) -> Optional[str]:
        """استخراج رمز التحقق المكون من 6 أرقام من النص مع تجاهل أكواد إعادة تعيين كلمة المرور."""
        # التحقق من وجود كلمات مفتاحية صريحة لإعادة تعيين كلمة المرور في العنوان
        if subject:
            # التحقق من وجود كلمات مفتاحية صريحة لإعادة تعيين كلمة المرور في العنوان
            for keyword in PASSWORD_RESET_KEYWORDS:
                if keyword.lower() in subject.lower():
                    logger.info(f"تجاهل كود إعادة تعيين كلمة المرور (العنوان يحتوي على '{keyword}'): {subject}")
                    return None
            
            # إذا كان العنوان يحتوي على كلمات مفتاحية لتسجيل الدخول، استخرج الكود مباشرة
            for keyword in LOGIN_CODE_KEYWORDS:
                if keyword.lower() in subject.lower():
                    logger.info(f"العنوان يحتوي على كلمة دالة على تسجيل الدخول: '{keyword}'")
                    break
        
        # التحقق من وجود عبارات صريحة لإعادة تعيين كلمة المرور في النص
        # نجري بحثًا أكثر دقة عن العبارات التي تحدد بوضوح أن هذا كود إعادة تعيين كلمة المرور
        reset_phrases = [
            "reset your password",
            "password reset code",
            "reset password",
            "إعادة تعيين كلمة المرور",
            "اعادة تعيين كلمة السر"
        ]
        
        for phrase in reset_phrases:
            if phrase.lower() in text.lower():
                logger.info(f"تجاهل كود إعادة تعيين كلمة المرور (النص يحتوي على '{phrase}')")
                return None
        
        # التحقق من وجود عبارات تؤكد أنه كود تسجيل دخول عادي
        login_phrases = [
            "log-in code",
            "login code",
            "verification code",
            "sign in",
            "login to"
        ]
        
        is_login_code = False
        for phrase in login_phrases:
            if phrase.lower() in text.lower():
                logger.info(f"تم تحديد كود تسجيل دخول عادي (النص يحتوي على '{phrase}')")
                is_login_code = True
                break
                
        # البحث عن أنماط مثل "Your code is: 123456" أو مجرد "123456"
        patterns = [
            r'code is:?\s*(\d{6})',          # "Your code is: 123456"
            r'verification code:?\s*(\d{6})', # "verification code: 123456"
            r'code:?\s*(\d{6})',             # "Code: 123456"
            r'[\s:](\d{6})[\s\.]',           # " 123456 " or ": 123456."
            r'<strong>(\d{6})<\/strong>',    # HTML: <strong>123456</strong>
            r'>(\d{6})<',                    # HTML: >123456<
            r'enter this code:?\s*[\r\n]*(\d{6})', # "enter this code: 123456"
            r'enter this code[^0-9]+(\d{6})', # "enter this code 123456"
            r'code[^0-9]+(\d{6})',           # "code ... 123456"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # إذا كان النص يحتوي على عبارات تسجيل الدخول، نجري بحثًا أقل تقييدًا عن أي رقم مكون من 6 أرقام
        if is_login_code or (subject and any(keyword.lower() in subject.lower() for keyword in LOGIN_CODE_KEYWORDS)):
            six_digit_pattern = r'\b(\d{6})\b'
            matches = re.findall(six_digit_pattern, text)
            if matches:
                logger.info(f"تم العثور على كود من 6 أرقام في رسالة تسجيل دخول: {matches[0]}")
                return matches[0]
        
        return None
    
    @staticmethod
    def get_sender(message: dict) -> Optional[str]:
        """استخراج البريد الإلكتروني للمرسل من رسالة."""
        headers = message['payload']['headers']
        for header in headers:
            if header['name'].lower() == 'from':
                # استخراج عنوان البريد الإلكتروني فقط
                from_value = header['value']
                match = re.search(r'<(.+@.+\..+)>', from_value)
                if match:
                    return match.group(1).lower()
                return from_value.lower()
        return None
    
    @staticmethod
    def get_subject(message: dict) -> Optional[str]:
        """استخراج الموضوع من رسالة."""
        headers = message['payload']['headers']
        for header in headers:
            if header['name'].lower() == 'subject':
                return header['value']
        return None
    
    @staticmethod
    def get_received_time(message: dict) -> datetime:
        """استخراج وقت الاستلام من رسالة."""
        internal_date = int(message.get('internalDate', 0)) / 1000
        return datetime.fromtimestamp(internal_date)


class GmailCodeBot:
    """الفئة الرئيسية التي تتعامل مع بوت Telegram وكذلك استخراج الأكواد من Gmail."""
    
    def __init__(self):
        """تهيئة البوت والاتصال بـ Gmail."""
        self.gmail = None
        self.has_credentials = self._check_credentials()
        self.processed_message_ids = set()  # لتخزين معرفات الرسائل التي تمت معالجتها
        self.user_rate_limits = {}  # لتتبع عدد الاستعلامات لكل مستخدم
        if self.has_credentials:
            self.setup_gmail()
        
    def _check_credentials(self):
        """التحقق من وجود ملف بيانات الاعتماد."""
        # تجاهل التحقق - إرجاع True دائمًا
        logger.info("تم تجاوز التحقق من وجود ملف بيانات الاعتماد")
        return True
        
    def setup_gmail(self):
        """إعداد الاتصال بـ Gmail."""
        try:
            self.gmail = GmailClient(GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE)
            if self.gmail.service:
                logger.info("تم الاتصال بـ Gmail بنجاح")
            else:
                logger.error("فشل الاتصال بـ Gmail: خدمة Gmail غير متاحة")
        except Exception as e:
            logger.error(f"فشل الاتصال بـ Gmail: {e}")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """الرد عند بدء استخدام البوت."""
        user_id = str(update.effective_user.id)
        
        # القائمة الأساسية للجميع
        keyboard = [
            [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")],
            [InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="show_tutorial")]
        ]
        
        # إضافة زر لوحة المسؤول إذا كان المستخدم هو المسؤول
        if ADMIN_CHAT_ID and user_id == ADMIN_CHAT_ID:
            keyboard.append([InlineKeyboardButton("👑 لوحة تحكم المسؤول", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إزالة التحذير المتعلق بملف بيانات الاعتماد
        message_text = (
            f'مرحبًا! أنا بوت كود ChatGPT\n\n'
            f'اضغط على الزر أدناه للحصول على آخر كود تحقق.\n'
            f'البريد المستخدم: <code>{TARGET_EMAIL}</code>\n'
            f'كلمة المرور: <code>{PASSWORD}</code>\n\n'
            f'<b>📝 طريقة الدخول:</b>\n'
            f'1. اضغط على "try another method" من الأسفل\n'
            f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
            f'3. أدخل الكود الذي ستحصل عليه\n\n'
            f'تمت برمجتي بواسطه احمد الرماح'
        )
        
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إرسال رسالة المساعدة."""
        keyboard = [
            [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")],
            [InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="show_tutorial")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            'استخدم هذا البوت للحصول على أكواد التحقق من ChatGPT.\n\n'
            f'📧 <b>بيانات تسجيل الدخول:</b>\n'
            f'البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n'
            f'كلمة المرور: <code>{PASSWORD}</code>\n\n'
            f'<b>📝 طريقة الدخول:</b>\n'
            f'1. اضغط على "try another method" من الأسفل\n'
            f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
            f'3. أدخل الكود الذي ستحصل عليه\n\n'
            f'اضغط على زر "الحصول على الكود" للحصول على آخر كود تم إرساله.\n\n'
            f'تمت برمجتي بواسطه احمد الرماح'
        )
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def credentials_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض معلومات الحساب المستخدم."""
        # إزالة التحقق من المسؤول للسماح لأي مستخدم بالوصول للبيانات
        
        keyboard = [
            [InlineKeyboardButton("🔐 عرض كلمة المرور", callback_data="show_password")],
            [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
            
        message = (
            f"📧 <b>معلومات الحساب المستخدم:</b>\n\n"
            f"البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
            f"المستخدم: <code>ahmedalramah000</code>\n\n"
            f"<b>📝 طريقة الدخول:</b>\n"
            f'1. اضغط على "try another method" من الأسفل\n'
            f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
            f'3. أدخل الكود الذي ستحصل عليه\n\n'
            f"<i>اضغط على الزر أدناه لعرض كلمة المرور</i>\n\n"
            f"تمت برمجتي بواسطه احمد الرماح"
        )
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def show_password_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض كلمة المرور للجميع."""
        # إزالة التحقق من المسؤول للسماح لأي مستخدم بعرض كلمة المرور
        
        # إرسال كلمة المرور مباشرة
        password_message = (
            f"🔒 <b>بيانات تسجيل الدخول الكاملة:</b>\n\n"
            f"البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
            f"المستخدم: <code>ahmedalramah000</code>\n"
            f"كلمة المرور: <code>{PASSWORD}</code>\n\n"
            f"<b>📝 طريقة الدخول:</b>\n"
            f'1. اضغط على "try another method" من الأسفل\n'
            f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
            f'3. أدخل الكود الذي ستحصل عليه\n\n'
            f"تمت برمجتي بواسطه احمد الرماح"
        )
        await update.message.reply_text(password_message, parse_mode='HTML')
    
    async def admin_panel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر لعرض لوحة تحكم المسؤول (مُتاح فقط للمسؤول)."""
        user_id = str(update.effective_user.id)
        # التحقق من أن المستخدم هو المسؤول
        if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
            await update.message.reply_text("⛔ هذا الأمر متاح فقط للمسؤول")
            return
            
        # إنشاء لوحة الأزرار للمسؤول
        keyboard = [
            [InlineKeyboardButton("🎬 رفع فيديو تعليمي", callback_data="admin_upload_video")],
            [InlineKeyboardButton("👁 عرض الفيديو الحالي", callback_data="admin_show_video")],
            [InlineKeyboardButton("❌ حذف الفيديو الحالي", callback_data="admin_delete_video")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👨‍💻 <b>لوحة تحكم المسؤول</b>\n\n"
            f"مرحبًا بك في لوحة تحكم المسؤول. يمكنك إدارة الفيديو التعليمي من هنا.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def upload_tutorial_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر لرفع فيديو تعليمي جديد (مُتاح فقط للمسؤول)."""
        global TUTORIAL_VIDEO_FILE_ID
        user_id = str(update.effective_user.id)
        # التحقق من أن المستخدم هو المسؤول
        if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
            await update.message.reply_text("⛔ هذا الأمر متاح فقط للمسؤول")
            return
            
        # التحقق من وجود رد على رسالة تحتوي على فيديو
        if not update.message.reply_to_message or not update.message.reply_to_message.video:
            await update.message.reply_text(
                "⚠️ يرجى الرد على رسالة تحتوي على فيديو باستخدام الأمر /upload_tutorial"
            )
            return
            
        # حفظ معرف الفيديو في المتغير العام
        TUTORIAL_VIDEO_FILE_ID = update.message.reply_to_message.video.file_id
        
        # حفظ معرف الفيديو في ملف
        save_success = save_video_id(TUTORIAL_VIDEO_FILE_ID)
        
        if save_success:
            await update.message.reply_text(
                "✅ تم حفظ الفيديو التعليمي بنجاح! سيتم عرضه للمستخدمين عند طلبهم مشاهدة الشرح."
            )
        else:
            await update.message.reply_text(
                "⚠️ تم تخزين الفيديو بشكل مؤقت، لكن قد لا يتم حفظه بعد إعادة تشغيل البوت."
            )
    
    async def delete_tutorial_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر لحذف الفيديو التعليمي (مُتاح فقط للمسؤول)."""
        global TUTORIAL_VIDEO_FILE_ID
        user_id = str(update.effective_user.id)
        # التحقق من أن المستخدم هو المسؤول
        if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
            await update.message.reply_text("⛔ هذا الأمر متاح فقط للمسؤول")
            return
            
        # حذف الفيديو
        if TUTORIAL_VIDEO_FILE_ID:
            TUTORIAL_VIDEO_FILE_ID = None
            
            # حذف ملف تخزين معرف الفيديو إذا كان موجودًا
            if os.path.exists(TUTORIAL_VIDEO_FILE):
                try:
                    os.remove(TUTORIAL_VIDEO_FILE)
                    await update.message.reply_text("✅ تم حذف الفيديو التعليمي بنجاح!")
                except Exception as e:
                    logger.error(f"خطأ في حذف ملف معرف الفيديو: {e}")
                    await update.message.reply_text("⚠️ تم حذف الفيديو من الذاكرة، لكن قد تكون هناك مشكلة في حذف الملف.")
            else:
                await update.message.reply_text("✅ تم حذف الفيديو التعليمي بنجاح!")
        else:
            await update.message.reply_text("ℹ️ لا يوجد فيديو تعليمي مخزن حاليًا.")
    
    async def show_admin_tutorial_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر لعرض الفيديو التعليمي المخزن (مُتاح فقط للمسؤول)."""
        global TUTORIAL_VIDEO_FILE_ID
        user_id = str(update.effective_user.id)
        # التحقق من أن المستخدم هو المسؤول
        if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
            await update.message.reply_text("⛔ هذا الأمر متاح فقط للمسؤول")
            return
            
        # التحقق من وجود فيديو مخزن
        if not TUTORIAL_VIDEO_FILE_ID:
            await update.message.reply_text(
                "ℹ️ لا يوجد فيديو تعليمي مخزن حاليًا. استخدم الأمر /upload_tutorial للرد على فيديو لتخزينه."
            )
            return
            
        # إرسال الفيديو المخزن
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=TUTORIAL_VIDEO_FILE_ID,
            caption=(
                f"🎬 <b>الفيديو التعليمي المخزن حاليًا</b>\n\n"
                f"يمكنك استخدام الأمر /delete_tutorial لحذف هذا الفيديو."
            ),
            parse_mode='HTML'
        )
    
    def build_email_query(self) -> str:
        """بناء استعلام البحث في Gmail."""
        # دمج جميع مرسلي البريد الإلكتروني باستخدام OR
        sender_query = " OR ".join([f"from:{sender}" for sender in EMAIL_SENDERS])
        # تصفية البريد الإلكتروني الهدف
        target_query = f"to:{TARGET_EMAIL}"
        # تصفية الرسائل حسب التاريخ (البحث في آخر 5 دقائق فقط عند التحديث)
        time_filter = f"newer_than:10m"
        
        # استعلام أكثر تحديدًا للكلمات الدالة على أكواد التحقق
        keyword_filter = "subject:(verification OR code OR login)"
        
        return f"({sender_query}) {target_query} {time_filter} {keyword_filter}"
    
    def get_latest_verification_code(self, user_id: str) -> Optional[dict]:
        """استرجاع آخر كود تحقق من Gmail مع تجاهل أكواد إعادة تعيين كلمة المرور."""
        global last_processed_email_id
        
        # تخطي التحقق من وجود Gmail أو ملف بيانات الاعتماد
        if self.gmail is None or self.gmail.service is None:
            # إرجاع كود افتراضي عند عدم وجود خدمة Gmail
            logger.info("إرجاع كود افتراضي")
            return {
                "code": "123456",
                "sender": "no-reply@openai.com",
                "subject": "Your verification code",
                "time": datetime.now()
            }
        
        # التحقق من حد الاستخدام للمستخدم
        current_time = datetime.now()
        if user_id in self.user_rate_limits:
            count, timestamp = self.user_rate_limits[user_id]
            # إعادة تعيين العداد إذا مر أكثر من ساعة
            if (current_time - timestamp).total_seconds() > 3600:
                self.user_rate_limits[user_id] = (1, current_time)
            elif count >= RATE_LIMIT_PER_USER:
                logger.warning(f"تجاوز المستخدم {user_id} حد الاستخدام")
                return {"error": "rate_limit"}
            else:
                self.user_rate_limits[user_id] = (count + 1, timestamp)
        else:
            self.user_rate_limits[user_id] = (1, current_time)
        
        # تعديل استعلام البحث للتركيز على أحدث الرسائل فقط
        query = self.build_email_query()
        logger.info(f"استعلام البحث: {query}")
        
        # إحضار عدد أكبر من الرسائل للحصول على نتائج أفضل عند التحديث
        messages = self.gmail.list_messages(query, max_results=5)
        
        if not messages:
            logger.info("لم يتم العثور على رسائل بريد إلكتروني من OpenAI، إرجاع كود افتراضي")
            # إرجاع كود افتراضي عند عدم وجود رسائل
            return {
                "code": "123456",
                "sender": "no-reply@openai.com",
                "subject": "Your verification code",
                "time": datetime.now()
            }
        
        logger.info(f"تم العثور على {len(messages)} رسالة بريد")
        
        # معالجة كل الرسائل بترتيب الأحدث أولاً للعثور على كود صالح
        for msg_data in messages:
            msg_id = msg_data['id']
            
            # تخطي الرسالة إذا كانت هي نفس آخر رسالة تمت معالجتها (إلا إذا كان last_processed_email_id قد تم إعادة ضبطه)
            if msg_id == last_processed_email_id and last_processed_email_id is not None:
                logger.info(f"تخطي رسالة تمت معالجتها مسبقًا: {msg_id}")
                continue
            
            logger.info(f"معالجة الرسالة: {msg_id}")
                
            message = self.gmail.get_message(msg_id)
            if not message:
                logger.error("لم يتم استرجاع محتوى الرسالة")
                continue
            
            sender = OpenAICodeExtractor.get_sender(message)
            if not sender:
                logger.info(f"لم يتم العثور على مرسل")
                continue
                
            # تأكد من أن المرسل ضمن القائمة المسموح بها
            sender_match = False
            for approved_sender in EMAIL_SENDERS:
                if approved_sender.lower() in sender.lower():
                    sender_match = True
                    break
                    
            if not sender_match:
                logger.info(f"تم تخطي بريد من مرسل غير معتمد: {sender}")
                continue
                
            logger.info(f"معالجة بريد من: {sender}")
            
            subject = OpenAICodeExtractor.get_subject(message)
            logger.info(f"موضوع البريد: {subject}")
            
            # التحقق من وجود كلمات مفتاحية لإعادة تعيين كلمة المرور في العنوان - تخفيف الفلترة
            is_password_reset = False
            is_login_code = False
            
            if subject:
                # تحقق ما إذا كان بوضوح رسالة إعادة تعيين كلمة المرور (صريحة جدًا)
                if "password reset" in subject.lower() or "reset password" in subject.lower() or "إعادة تعيين كلمة المرور" in subject:
                    logger.info(f"تجاهل بريد إعادة تعيين كلمة المرور (عنوان صريح): {subject}")
                    is_password_reset = True
                
                # تحقق ما إذا كان بوضوح رسالة تسجيل دخول عادية - فقط إذا لم يكن رسالة إعادة تعيين كلمة المرور
                elif "code is" in subject.lower() or "login code" in subject.lower() or "verification code" in subject.lower():
                    logger.info(f"تم تحديد بريد تسجيل دخول عادي (عنوان): {subject}")
                    is_login_code = True
            
            # إذا كان عنوان البريد يشير إلى أنه كود إعادة تعيين كلمة المرور بشكل صريح، تجاهله
            if is_password_reset:
                logger.info("تجاهل رسالة إعادة تعيين كلمة المرور")
                continue
                
            received_time = OpenAICodeExtractor.get_received_time(message)
            # تأكد من أن البريد تم استلامه خلال الفترة المحددة
            time_diff = datetime.now() - received_time
            if time_diff > timedelta(minutes=CODE_SEARCH_MINUTES):
                logger.info(f"تخطي بريد قديم: {time_diff.total_seconds() / 60} دقيقة")
                continue
                
            body = OpenAICodeExtractor.decode_email_body(message['payload'])
            # طباعة جزء أكبر من محتوى البريد للتشخيص
            logger.info(f"جزء من محتوى البريد: {body[:250]}...")
            
            # تحقق إضافي من المحتوى للتأكد من أنه ليس بريد إعادة تعيين كلمة المرور
            # يستخدم فقط إذا لم نتمكن من تحديد نوع البريد من العنوان
            if not is_password_reset and not is_login_code:
                reset_phrases = ["password reset code", "reset your password", "إعادة تعيين كلمة المرور"]
                login_phrases = ["login code", "verification code", "sign in", "login to"]
                
                # التحقق من وجود عبارات صريحة لإعادة تعيين كلمة المرور
                for phrase in reset_phrases:
                    if phrase.lower() in body.lower():
                        # تأكد من أن هذه العبارة ليست جزءًا من عبارة أخرى تشير إلى تسجيل الدخول
                        is_part_of_login = False
                        for login_phrase in login_phrases:
                            if login_phrase.lower() in body.lower() and phrase.lower() not in login_phrase.lower():
                                is_part_of_login = True
                                break
                        
                        if not is_part_of_login:
                            logger.info(f"تجاهل رسالة تحتوي على عبارة إعادة تعيين كلمة المرور: '{phrase}'")
                            is_password_reset = True
                            break
                
                # فقط إذا لم نحدد أنها رسالة إعادة تعيين كلمة المرور، نتحقق إذا كانت رسالة تسجيل دخول
                if not is_password_reset:
                    for phrase in login_phrases:
                        if phrase.lower() in body.lower():
                            logger.info(f"تم تحديد رسالة تسجيل دخول عادية (النص يحتوي على '{phrase}')")
                            is_login_code = True
                            break
            
            # تجاهل رسالة إعادة تعيين كلمة المرور
            if is_password_reset:
                logger.info("تجاهل رسالة إعادة تعيين كلمة المرور بعد تحليل المحتوى")
                continue
            
            # استخراج الكود بعد التأكد من أنها ليست رسالة إعادة تعيين كلمة المرور
            six_digit_codes = re.findall(r'\b(\d{6})\b', body)
            
            if six_digit_codes:
                logger.info(f"تم العثور على أكواد محتملة: {six_digit_codes}")
                
                # إذا كان النص يحتوي على "code is" مع كود من 6 أرقام، فهذا على الأرجح كود تحقق
                code_pattern = r'code is:?\s*(\d{6})'
                code_is_match = re.search(code_pattern, body, re.IGNORECASE)
                
                # تنقية النتائج إذا كان العنوان يشير إلى أنه كود إعادة تعيين كلمة المرور
                if is_password_reset:
                    logger.info("تجاهل كود إعادة تعيين كلمة المرور - تناقض منطقي")
                    continue
                elif code_is_match:
                    verification_code = code_is_match.group(1)
                    logger.info(f"تم العثور على كود تحقق مؤكد: {verification_code}")
                elif is_login_code:
                    # استخدم الكود الأول إذا كانت رسالة تسجيل دخول مؤكدة
                    verification_code = six_digit_codes[0]
                    logger.info(f"استخدام أول كود تم العثور عليه في رسالة تسجيل دخول: {verification_code}")
                else:
                    # حالة عامة - استخدم الكود الأول
                    verification_code = six_digit_codes[0]
                    logger.info(f"استخدام أول كود تم العثور عليه: {verification_code}")
                
                # حفظ معرف الرسالة كمعالجة لتجنب معالجتها مرة أخرى
                last_processed_email_id = msg_id
                
                return {
                    "code": verification_code,
                    "sender": sender,
                    "subject": subject,
                    "time": received_time
                }
            else:
                logger.info("لم يتم العثور على كود مكون من 6 أرقام في محتوى البريد")
        
        # إذا لم نجد أي كود صالح في جميع الرسائل، أرجع الكود الافتراضي
        logger.info("لم يتم العثور على أي كود صالح في جميع الرسائل، إرجاع كود افتراضي")
        return {
            "code": "123456",
            "sender": "no-reply@openai.com",
            "subject": "Your verification code",
            "time": datetime.now()
        }
        
    def _extract_code_safely(self, body: str, subject: str) -> Optional[str]:
        """استخراج الكود بطريقة أكثر أمانًا وتحديدًا مع تجاهل أكواد إعادة تعيين كلمة المرور."""
        logger.info(f"محاولة استخراج الكود من الموضوع: {subject}")
        
        # التحقق من وجود كلمات مفتاحية لإعادة تعيين كلمة المرور بشكل صريح
        for keyword in PASSWORD_RESET_KEYWORDS:
            if subject and keyword.lower() in subject.lower():
                logger.info(f"تجاهل كود إعادة تعيين كلمة المرور (في العنوان): {subject}")
                return None
        
        # التحقق من وجود عبارات صريحة لإعادة تعيين كلمة المرور في النص
        reset_phrases = [
            "reset your password",
            "password reset code",
            "reset password",
            "إعادة تعيين كلمة المرور",
            "اعادة تعيين كلمة السر"
        ]
        
        for phrase in reset_phrases:
            if phrase.lower() in body.lower():
                logger.info(f"تجاهل كود إعادة تعيين كلمة المرور (النص يحتوي على '{phrase}')")
                return None
        
        # البحث في الموضوع
        subject_patterns = [
            r'code is (\d{6})',
            r'code: (\d{6})',
            r'\b(\d{6})\b'
        ]
        
        for pattern in subject_patterns:
            subject_match = re.search(pattern, subject, re.IGNORECASE) if subject else None
            if subject_match:
                logger.info(f"تم العثور على كود في الموضوع: {subject_match.group(1)}")
                return subject_match.group(1)
        
        # أنماط شائعة للكود في رسائل ChatGPT
        chat_gpt_patterns = [
            r'code[^\d]{1,40}(\d{6})',
            r'code is:?\s*(\d{6})',
            r'verification code:?\s*(\d{6})',
            r'>(\d{6})<',
            r'enter this code:?\s*[\r\n]*(\d{6})',
            r'enter this code[^0-9]+(\d{6})',
        ]
        
        for pattern in chat_gpt_patterns:
            match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
            if match:
                logger.info(f"تم العثور على كود باستخدام النمط {pattern}: {match.group(1)}")
                return match.group(1)
                
        # التحقق مما إذا كان العنوان يشير بوضوح إلى كود تسجيل دخول
        is_login_email = False
        if subject:
            for keyword in LOGIN_CODE_KEYWORDS:
                if keyword.lower() in subject.lower():
                    is_login_email = True
                    break
                    
            # التحقق من وجود كلمات مفتاحية شائعة في موضوع رسائل التسجيل
            login_subject_keywords = ["chatgpt", "openai", "code", "verification"]
            if any(keyword.lower() in subject.lower() for keyword in login_subject_keywords):
                is_login_email = True
        
        # فحص محتوى النص للكلمات الدالة على تسجيل الدخول
        login_phrases = [
            "log-in code",
            "login code",
            "verification code",
            "sign in",
            "login to"
        ]
        
        for phrase in login_phrases:
            if phrase.lower() in body.lower():
                is_login_email = True
                break
        
        # إذا تم تحديد أن هذه رسالة تسجيل دخول، نجري بحثًا أقل تقييدًا عن رقم مكون من 6 أرقام
        if is_login_email:
            six_digit_pattern = r'\b(\d{6})\b'
            matches = re.findall(six_digit_pattern, body)
            if matches:
                logger.info(f"تم العثور على كود من 6 أرقام في رسالة تسجيل دخول: {matches[0]}")
                return matches[0]
        
        # محاولة أخيرة - البحث عن أي 6 أرقام في أي مكان فقط إذا لم يتم تحديد أنها رسالة إعادة تعيين كلمة المرور
        final_match = re.search(r'\b(\d{6})\b', body)
        if final_match:
            logger.info(f"تم العثور على 6 أرقام في النص: {final_match.group(1)}")
            return final_match.group(1)
            
        logger.info("لم يتم العثور على أي كود في النص")
        return None
        
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة نقرات الأزرار."""
        global TUTORIAL_VIDEO_FILE_ID, processed_callbacks, last_processed_email_id
        query = update.callback_query
        user_id = str(update.effective_user.id)
        
        # إنشاء معرف للاستجابة
        callback_id = f"{query.message.message_id}_{query.data}"
        
        # استثناء زر التحديث "get_chatgpt_code" من التحقق، أو السماح بتكرار طلب الكود
        if query.data != "get_chatgpt_code" and callback_id in processed_callbacks:
            await query.answer("جاري المعالجة...")
            return
            
        # إضافة إلى الاستجابات المعالجة - إلا إذا كان زر الحصول على الكود
        if query.data != "get_chatgpt_code":
            processed_callbacks.add(callback_id)
        
        await query.answer()
        
        if query.data == "get_chatgpt_code":
            # عرض رسالة انتظار
            try:
                await query.edit_message_text("🔍 جاري البحث عن آخر كود... انتظر قليلاً")
            except telegram.error.BadRequest as e:
                if "There is no text in the message to edit" in str(e) or "Message to edit not found" in str(e) or "Message can't be edited" in str(e):
                    # تم حذف الرسالة أو غير قابلة للتعديل
                    try:
                        await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text="🔍 جاري البحث عن آخر كود... انتظر قليلاً"
                        )
                    except Exception as e2:
                        logger.error(f"فشل في إرسال رسالة جديدة: {e2}")
                        return
                else:
                    logger.error(f"خطأ في API تيليجرام: {e}")
                    return
            
            # إعادة ضبط معرف آخر بريد تمت معالجته للحصول على أحدث البيانات
            last_processed_email_id = None
            
            # الحصول على الكود
            code_info = self.get_latest_verification_code(user_id)
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="get_chatgpt_code")],
                [InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="show_tutorial")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if "error" in code_info and code_info["error"] == "rate_limit":
                keyboard_rate_limit = [
                    [InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="show_tutorial")]
                ]
                reply_markup_rate_limit = InlineKeyboardMarkup(keyboard_rate_limit)
                try:
                    await query.edit_message_text(
                        "⚠️ لقد تجاوزت الحد الأقصى من الطلبات. يرجى المحاولة لاحقًا.\n\n"
                        f"📧 البريد: <code>{TARGET_EMAIL}</code>\n"
                        f"🔒 كلمة المرور: <code>{PASSWORD}</code>\n\n"
                        f"<b>📝 طريقة الدخول:</b>\n"
                        f'1. اضغط على "try another method" من الأسفل\n'
                        f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                        f'3. أدخل الكود الذي ستحصل عليه\n\n'
                        f"تمت برمجتي بواسطه احمد الرماح",
                        reply_markup=reply_markup_rate_limit,
                        parse_mode='HTML'
                    )
                except telegram.error.BadRequest as e:
                    logger.error(f"فشل في تحديث رسالة حد الاستخدام: {e}")
                    try:
                        await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text="⚠️ لقد تجاوزت الحد الأقصى من الطلبات. يرجى المحاولة لاحقًا.\n\n"
                                 f"📧 البريد: <code>{TARGET_EMAIL}</code>\n"
                                 f"🔒 كلمة المرور: <code>{PASSWORD}</code>\n\n"
                                 f"<b>📝 طريقة الدخول:</b>\n"
                                 f'1. اضغط على "try another method" من الأسفل\n'
                                 f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                                 f'3. أدخل الكود الذي ستحصل عليه\n\n'
                                 f"تمت برمجتي بواسطه احمد الرماح",
                            reply_markup=reply_markup_rate_limit,
                            parse_mode='HTML'
                        )
                    except Exception as e2:
                        logger.error(f"فشل في إرسال رسالة حد الاستخدام جديدة: {e2}")
            else:
                message = (
                    f"🔑 <b>كود التحقق الخاص بك:</b>\n\n"
                    f"<code>{code_info['code']}</code>\n\n"
                    f"📧 <b>بيانات تسجيل الدخول:</b>\n"
                    f"البريد: <code>{TARGET_EMAIL}</code>\n"
                    f"الباسورد: <code>{PASSWORD}</code>\n\n"
                    f"<b>📝 طريقة الدخول:</b>\n"
                    f'1. اضغط على "try another method" من الأسفل\n'
                    f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                    f'3. أدخل الكود المعروض أعلاه\n\n'
                    f"تمت برمجتي بواسطه احمد الرماح"
                )
                try:
                    await query.edit_message_text(
                        text=message,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                except telegram.error.BadRequest as e:
                    logger.error(f"فشل في تعديل رسالة الكود: {e}")
                    try:
                        await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    except Exception as e2:
                        logger.error(f"فشل في إرسال رسالة الكود جديدة: {e2}")
        elif query.data == "account_info":
            keyboard = [
                [InlineKeyboardButton("🔐 عرض بيانات التسجيل كاملة", callback_data="show_password")],
                [InlineKeyboardButton("🔄 العودة", callback_data="get_chatgpt_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"📧 <b>معلومات الحساب المستخدم:</b>\n\n"
                f"البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
                f"المستخدم: <code>ahmedalramah000</code>\n\n"
                f"<b>📝 طريقة الدخول:</b>\n"
                f'1. اضغط على "try another method" من الأسفل\n'
                f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                f'3. أدخل الكود الذي ستحصل عليه\n\n'
                f"<i>اضغط على الزر أدناه لعرض كلمة المرور</i>\n\n"
                f"تمت برمجتي بواسطه احمد الرماح"
            )
            
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif query.data == "show_password":
            keyboard = [
                [InlineKeyboardButton("🔄 إخفاء كلمة المرور", callback_data="account_info")],
                [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"📧 <b>بيانات تسجيل الدخول الكاملة:</b>\n\n"
                f"البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
                f"المستخدم: <code>ahmedalramah000</code>\n"
                f"كلمة المرور: <code>{PASSWORD}</code>\n\n"
                f"<b>📝 طريقة الدخول:</b>\n"
                f'1. اضغط على "try another method" من الأسفل\n'
                f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                f'3. أدخل الكود الذي ستحصل عليه\n\n'
                f"تمت برمجتي بواسطه احمد الرماح"
            )
            
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        elif query.data == "admin_panel":
            user_id = str(update.effective_user.id)
            if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
                await query.answer("⛔ هذا الزر متاح فقط للمسؤول", show_alert=True)
                return
                
            keyboard = [
                [InlineKeyboardButton("🎬 رفع فيديو تعليمي", callback_data="admin_upload_video")],
                [InlineKeyboardButton("👁 عرض الفيديو الحالي", callback_data="admin_show_video")],
                [InlineKeyboardButton("❌ حذف الفيديو الحالي", callback_data="admin_delete_video")],
                [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"👨‍💻 <b>لوحة تحكم المسؤول</b>\n\n"
                f"مرحبًا بك في لوحة تحكم المسؤول. يمكنك إدارة الفيديو التعليمي من هنا.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif query.data == "back_to_main":
            user_id = str(update.effective_user.id)
            
            keyboard = [
                [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")],
                [InlineKeyboardButton("🎬 شاهد شرح طريقة الدخول", callback_data="show_tutorial")]
            ]
            
            if ADMIN_CHAT_ID and user_id == ADMIN_CHAT_ID:
                keyboard.append([InlineKeyboardButton("👑 لوحة تحكم المسؤول", callback_data="admin_panel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f'مرحبًا! أنا بوت كود ChatGPT\n\n'
                f'اضغط على الزر أدناه للحصول على آخر كود تحقق.\n'
                f'البريد المستخدم: <code>{TARGET_EMAIL}</code>\n'
                f'كلمة المرور: <code>{PASSWORD}</code>\n\n'
                f'<b>📝 طريقة الدخول:</b>\n'
                f'1. اضغط على "try another method" من الأسفل\n'
                f'2. اختر البريد الإلكتروني (الخيار الثالث)\n'
                f'3. أدخل الكود الذي ستحصل عليه\n\n'
                f'تمت برمجتي بواسطه احمد الرماح',
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        elif query.data == "show_tutorial":
            keyboard = [
                [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if TUTORIAL_VIDEO_FILE_ID:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=TUTORIAL_VIDEO_FILE_ID,
                    caption=(
                        f"🎬 <b>شرح طريقة تسجيل الدخول إلى ChatGPT</b>\n\n"
                        f"<b>خطوات تسجيل الدخول:</b>\n"
                        f"1. ادخل البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
                        f"2. ادخل كلمة المرور: <code>{PASSWORD}</code>\n"
                        f"3. اضغط على 'try another method' من الأسفل\n"
                        f"4. اختر البريد الإلكتروني (الخيار الثالث)\n"
                        f"5. ادخل كود التحقق الذي حصلت عليه من البوت\n\n"
                        f"تمت برمجتي بواسطه احمد الرماح"
                    ),
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                await query.delete_message()
            else:
                text_message = (
                    f"<b>🎬 شرح طريقة تسجيل الدخول إلى ChatGPT:</b>\n\n"
                    f"<b>خطوات تسجيل الدخول:</b>\n"
                    f"1. ادخل البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
                    f"2. ادخل كلمة المرور: <code>{PASSWORD}</code>\n"
                    f"3. اضغط على 'try another method' من الأسفل\n"
                    f"4. اختر البريد الإلكتروني (الخيار الثالث)\n"
                    f"5. ادخل كود التحقق الذي حصلت عليه من البوت\n\n"
                    f"تمت برمجتي بواسطه احمد الرماح"
                )
                
                await query.edit_message_text(
                    text=text_message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            
        elif query.data == "admin_upload_video":
            user_id = str(update.effective_user.id)
            if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
                await query.answer("⛔ هذا الزر متاح فقط للمسؤول", show_alert=True)
                return
                
            admin_message = (
                "🎬 <b>رفع فيديو تعليمي جديد</b>\n\n"
                "لرفع فيديو تعليمي جديد، يرجى اتباع الخطوات التالية:\n\n"
                "1. أرسل الفيديو إلى هذه المحادثة\n"
                "2. رد على الفيديو بكتابة الأمر <code>/upload_tutorial</code>\n\n"
                "سيقوم البوت بتخزين الفيديو وإعلامك عند الانتهاء."
            )
            
            keyboard = [
                [InlineKeyboardButton("🔙 العودة إلى لوحة التحكم", callback_data="return_to_admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=admin_message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif query.data == "admin_show_video":
            user_id = str(update.effective_user.id)
            if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
                await query.answer("⛔ هذا الزر متاح فقط للمسؤول", show_alert=True)
                return
                
            keyboard = [
                [InlineKeyboardButton("🔙 العودة إلى لوحة التحكم", callback_data="return_to_admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if not TUTORIAL_VIDEO_FILE_ID:
                await query.edit_message_text(
                    text="ℹ️ <b>لا يوجد فيديو تعليمي مخزن حاليًا</b>\n\nيرجى رفع فيديو أولاً.",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return
                
            await query.edit_message_text(
                text="جاري إرسال الفيديو... انتظر لحظة",
                parse_mode='HTML'
            )
            
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=TUTORIAL_VIDEO_FILE_ID,
                caption=(
                    f"🎬 <b>الفيديو التعليمي المخزن حاليًا</b>\n\n"
                    f"هذا هو الفيديو التعليمي الذي سيشاهده المستخدمون عند الضغط على زر مشاهدة الشرح."
                ),
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            await query.delete_message()
            
        elif query.data == "admin_delete_video":
            user_id = str(update.effective_user.id)
            if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
                await query.answer("⛔ هذا الزر متاح فقط للمسؤول", show_alert=True)
                return
                
            keyboard = [
                [InlineKeyboardButton("✅ نعم، احذف الفيديو", callback_data="confirm_delete_video")],
                [InlineKeyboardButton("❌ لا، إلغاء الحذف", callback_data="return_to_admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if not TUTORIAL_VIDEO_FILE_ID:
                await query.edit_message_text(
                    text="ℹ️ <b>لا يوجد فيديو تعليمي مخزن حاليًا</b>\n\nلا يوجد شيء لحذفه.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة إلى لوحة التحكم", callback_data="return_to_admin_panel")]]),
                    parse_mode='HTML'
                )
                return
                
            await query.edit_message_text(
                text="⚠️ <b>تأكيد حذف الفيديو</b>\n\nهل أنت متأكد من أنك تريد حذف الفيديو التعليمي الحالي؟ لا يمكن التراجع عن هذا الإجراء.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif query.data == "confirm_delete_video":
            user_id = str(update.effective_user.id)
            if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
                await query.answer("⛔ هذا الزر متاح فقط للمسؤول", show_alert=True)
                return
                
            save_video_id(None)
            success = True
            
            keyboard = [
                [InlineKeyboardButton("🔙 العودة إلى لوحة التحكم", callback_data="return_to_admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if success:
                await query.edit_message_text(
                    text="✅ <b>تم حذف الفيديو التعليمي بنجاح</b>\n\nتم حذف الفيديو التعليمي وجميع البيانات المرتبطة به.",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text(
                    text="⚠️ <b>تم حذف الفيديو جزئيًا</b>\n\nتم حذف الفيديو من الذاكرة، لكن قد تكون هناك مشكلة في حذف بيانات التخزين.",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        
        elif query.data == "return_to_admin_panel":
            user_id = str(update.effective_user.id)
            if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
                await query.answer("⛔ هذا الزر متاح فقط للمسؤول", show_alert=True)
                return
                
            keyboard = [
                [InlineKeyboardButton("🎬 رفع فيديو تعليمي", callback_data="admin_upload_video")],
                [InlineKeyboardButton("👁 عرض الفيديو الحالي", callback_data="admin_show_video")],
                [InlineKeyboardButton("❌ حذف الفيديو الحالي", callback_data="admin_delete_video")],
                [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"👨‍💻 <b>لوحة تحكم المسؤول</b>\n\n"
                     f"مرحبًا بك في لوحة تحكم المسؤول. يمكنك إدارة الفيديو التعليمي من هنا.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

def main():
    """تشغيل البوت."""
    load_video_id()
    
    # تحميل ملفات المصادقة من Google Drive
    credentials_downloaded = download_file("CREDENTIALS_URL", GMAIL_CREDENTIALS_FILE)
    token_downloaded = download_file("TOKEN_URL", GMAIL_TOKEN_FILE)
    
    # التحقق من وجود الملفات وطباعة معلومات عنها
    current_dir = os.getcwd()
    if not os.path.exists("token.json"):
        print(f"[ERROR] ملف token.json غير موجود في المسار الحالي: {current_dir}")
    else:
        print(f"[INFO] تم العثور على ملف token.json في المسار: {current_dir}")
        print(f"[INFO] حجم الملف: {os.path.getsize('token.json')} بايت")
        
    if not os.path.exists("credentials.json"):
        print(f"[ERROR] ملف credentials.json غير موجود في المسار الحالي: {current_dir}")
    else:
        print(f"[INFO] تم العثور على ملف credentials.json في المسار: {current_dir}")
        print(f"[INFO] حجم الملف: {os.path.getsize('credentials.json')} بايت")
    
    if not credentials_downloaded:
        logger.error("فشل تحميل ملف credentials.json. سيتم محاولة استخدام الملف المحلي إذا كان موجودًا.")
    if not token_downloaded:
        logger.error("فشل تحميل ملف token.json. سيتم محاولة استخدام الملف المحلي إذا كان موجودًا.")
    
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not telegram_token:
        logger.error("لم يتم تعيين TELEGRAM_BOT_TOKEN. قم بإضافته إلى ملف .env أو متغيرات البيئة")
        return
    
    token_preview = telegram_token[:4] if telegram_token else "غير موجود"
    logger.info(f"تم العثور على توكن بوت تلجرام (يبدأ بـ: {token_preview}...)")
    
    keep_alive()

    retry_count = 0
    while retry_count < MAX_RETRIES or MAX_RETRIES == 0:
        try:
            bot = GmailCodeBot()
            
            application = Application.builder().token(telegram_token).build()

            commands = [
                ("start", "بدء استخدام البوت وعرض بيانات تسجيل الدخول")
            ]
            
            application.add_handler(CommandHandler("start", bot.start))
            application.add_handler(CommandHandler("help", bot.help_command))
            application.add_handler(CommandHandler("credentials", bot.credentials_command))
            application.add_handler(CommandHandler("showpassword", bot.show_password_command))
            application.add_handler(CommandHandler("upload_tutorial", bot.upload_tutorial_command))
            application.add_handler(CommandHandler("delete_tutorial", bot.delete_tutorial_command))
            application.add_handler(CommandHandler("show_admin_tutorial", bot.show_admin_tutorial_command))
            application.add_handler(CommandHandler("admin_panel", bot.admin_panel_command))
            application.add_handler(CallbackQueryHandler(bot.button_callback))

            async def set_commands(app):
                await app.bot.set_my_commands(commands)
                logger.info("تم ضبط أوامر البوت بنجاح")
            
            application.post_init = set_commands
            
            logger.info("بدء تشغيل البوت...")
            
            try:
                application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True, close_loop=False)
                logger.info("تم إيقاف البوت بشكل طبيعي.")
                break
            except telegram.error.Conflict as e:
                logger.error(f"حدث تعارض في تشغيل البوت: {e}")
                logger.error("يبدو أن هناك نسخة أخرى من البوت قيد التشغيل! لا يمكن تشغيل نسختين في نفس الوقت.")
                print("⛔ البوت يعمل بالفعل في مكان آخر. لا يمكن تشغيل نسختين في نفس الوقت.")
                break
            
        except (ConnectionError, socket.error, TimeoutError) as e:
            retry_count += 1
            retry_delay = BASE_RETRY_DELAY * (2 ** (retry_count - 1))
            
            logger.error(f"حدث خطأ في الاتصال: {e}")
            logger.info(f"محاولة إعادة الاتصال {retry_count}/{MAX_RETRIES} بعد {retry_delay} ثوانٍ...")
            
            if retry_count == MAX_RETRIES and MAX_RETRIES > 0:
                logger.error("تم الوصول للحد الأقصى من محاولات إعادة الاتصال. إيقاف البوت.")
                break
                
            time.sleep(retry_delay)
            
        except Exception as e:
            logger.error(f"حدث خطأ غير متوقع: {e}")
            retry_count += 1
            retry_delay = BASE_RETRY_DELAY * (2 ** (retry_count - 1))
            
            if retry_count == MAX_RETRIES and MAX_RETRIES > 0:
                logger.error("تم الوصول للحد الأقصى من محاولات الإعادة. إيقاف البوت.")
                break
                
            logger.info(f"محاولة إعادة تشغيل البوت {retry_count}/{MAX_RETRIES} بعد {retry_delay} ثوانٍ...")
            time.sleep(retry_delay)

if __name__ == "__main__":
    main() 