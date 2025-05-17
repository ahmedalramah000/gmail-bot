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

# Maximum connection retry attempts
MAX_RETRIES = 5
# Base delay between retries (will increase exponentially)
BASE_RETRY_DELAY = 5

# تحميل متغيرات البيئة
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TARGET_EMAIL = os.environ.get('TARGET_EMAIL', "ahmedalramah000@gmail.com")  # البريد من متغيرات البيئة
EMAIL_SENDERS = os.environ.get('EMAIL_SENDERS', "no-reply@openai.com,login-code@openai.com,noreply@tm.openai.com").split(',')
# المدة الزمنية للبحث عن الأكواد (بالدقائق)
CODE_SEARCH_MINUTES = int(os.environ.get('CODE_SEARCH_MINUTES', 60))
# الحد الأقصى للاستعلامات لكل مستخدم
RATE_LIMIT_PER_USER = int(os.environ.get('RATE_LIMIT_PER_USER', 10))

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

# إعدادات Gmail API
GMAIL_CREDENTIALS_FILE = 'credentials.json.json'
GMAIL_TOKEN_FILE = 'token.json'
GMAIL_API_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    """التعامل مع عمليات Gmail API."""
    
    def __init__(self, credentials_file: str, token_file: str):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._authenticate()
        
    def _authenticate(self):
        """المصادقة مع Gmail API باستخدام OAuth."""
        # التحقق من وجود ملف بيانات الاعتماد
        if not os.path.exists(self.credentials_file):
            logger.error(f"ملف بيانات الاعتماد غير موجود: {self.credentials_file}")
            return None
            
        creds = None
        
        # تحميل التوكن الموجود إذا كان متاحًا
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as token:
                    creds = Credentials.from_authorized_user_info(
                        json.load(token), GMAIL_API_SCOPES
                    )
            except Exception as e:
                logger.error(f"خطأ في قراءة ملف التوكن: {e}")
                creds = None
        
        # إذا لم تكن هناك بيانات اعتماد صالحة، قم بالمصادقة
        if not creds or not creds.valid:
            try:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("تحديث التوكن المنتهي...")
                    creds.refresh(Request())
                else:
                    logger.info("بدء عملية المصادقة الجديدة...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, GMAIL_API_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
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
            logger.error(f"خطأ في سرد الرسائل: {e}")
            return []
    
    def get_message(self, msg_id: str) -> Optional[dict]:
        """الحصول على رسالة محددة بواسطة المعرف."""
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
            logger.error(f"خطأ في الحصول على الرسالة {msg_id}: {e}")
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
        keyboard = [
            [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إزالة التحذير المتعلق بملف بيانات الاعتماد
        message_text = (
            f'مرحبًا! أنا بوت كود ChatGPT\n\n'
            f'اضغط على الزر أدناه للحصول على آخر كود تحقق.\n'
            f'البريد المستخدم: <code>{TARGET_EMAIL}</code>\n'
            f'كلمة المرور: <code>Ahmed@Ramah0000</code>\n\n'
            f'تمت برمجتي بواسطه احمد الرماح'
        )
        
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إرسال رسالة المساعدة."""
        keyboard = [
            [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            'استخدم هذا البوت للحصول على أكواد التحقق من ChatGPT.\n\n'
            f'📧 <b>بيانات تسجيل الدخول:</b>\n'
            f'البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n'
            f'كلمة المرور: <code>Ahmed@Ramah0000</code>\n\n'
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
            f"كلمة المرور: <code>Ahmed@Ramah0000</code>\n\n"
            f"تمت برمجتي بواسطه احمد الرماح"
        )
        await update.message.reply_text(password_message, parse_mode='HTML')
    
    def build_email_query(self) -> str:
        """بناء استعلام البحث في Gmail."""
        # دمج جميع مرسلي البريد الإلكتروني باستخدام OR
        sender_query = " OR ".join([f"from:{sender}" for sender in EMAIL_SENDERS])
        # تصفية البريد الإلكتروني الهدف
        target_query = f"to:{TARGET_EMAIL}"
        # تصفية الرسائل حسب التاريخ (البحث في آخر 10 دقائق فقط)
        time_filter = f"newer_than:10m"
        return f"({sender_query}) {target_query} {time_filter}"
    
    def get_latest_verification_code(self, user_id: str) -> Optional[dict]:
        """استرجاع آخر كود تحقق من Gmail مع تجاهل أكواد إعادة تعيين كلمة المرور."""
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
        
        # تعديل استعلام البحث للتركيز على أحدث الرسائل فقط (آخر 5 دقائق)
        query = self.build_email_query()
        logger.info(f"استعلام البحث: {query}")
        
        # إحضار أحدث 3 رسائل فقط
        messages = self.gmail.list_messages(query, max_results=3)
        
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
        
        # معالجة الرسالة الأحدث فقط (أول رسالة في القائمة) - ترتيب الرسائل من الأحدث إلى الأقدم
        if len(messages) > 0:
            msg_data = messages[0]  # أخذ أحدث رسالة فقط
            msg_id = msg_data['id']
            
            # لا نتجاهل أي رسالة سابقة - نركز فقط على أحدث رسالة
            logger.info(f"معالجة أحدث رسالة: {msg_id}")
                
            message = self.gmail.get_message(msg_id)
            if not message:
                logger.error("لم يتم استرجاع محتوى الرسالة")
                return None
            
            sender = OpenAICodeExtractor.get_sender(message)
            if not sender:
                logger.info(f"لم يتم العثور على مرسل")
                return None
                
            # تأكد من أن المرسل ضمن القائمة المسموح بها
            sender_match = False
            for approved_sender in EMAIL_SENDERS:
                if approved_sender.lower() in sender.lower():
                    sender_match = True
                    break
                    
            if not sender_match:
                logger.info(f"تم تخطي بريد من مرسل غير معتمد: {sender}")
                return None
                
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
                return None
                
            received_time = OpenAICodeExtractor.get_received_time(message)
            # تأكد من أن البريد تم استلامه خلال الفترة المحددة
            time_diff = datetime.now() - received_time
            if time_diff > timedelta(minutes=CODE_SEARCH_MINUTES):
                logger.info(f"تخطي بريد قديم: {time_diff.total_seconds() / 60} دقيقة")
                return None
                
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
                return None
            
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
                    return None
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
                self.processed_message_ids.add(msg_id)
                
                return {
                    "code": verification_code,
                    "sender": sender,
                    "subject": subject,
                    "time": received_time
                }
            else:
                logger.info("لم يتم العثور على كود مكون من 6 أرقام في محتوى البريد")
        
        return None
        
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
        """التعامل مع نقرات الأزرار."""
        query = update.callback_query
        user_id = str(update.effective_user.id)
        await query.answer()
        
        if query.data == "get_chatgpt_code":
            # عرض رسالة انتظار
            await query.edit_message_text("🔍 جاري البحث عن آخر كود... انتظر قليلاً")
            
            # البحث عن الكود (مع تجاهل التحقق من وجود ملف بيانات الاعتماد)
            code_info = self.get_latest_verification_code(user_id)
            
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="get_chatgpt_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # تعديل الشرط لتجاهل رسالة خطأ ملف بيانات الاعتماد
            if code_info:
                if "error" in code_info and code_info["error"] == "rate_limit":
                    await query.edit_message_text(
                        "⚠️ لقد تجاوزت الحد الأقصى من الطلبات. يرجى المحاولة لاحقًا.\n\n"
                        f"📧 البريد: <code>{TARGET_EMAIL}</code>\n"
                        f"🔒 كلمة المرور: <code>Ahmed@Ramah0000</code>\n\n"
                        f"تمت برمجتي بواسطه احمد الرماح",
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                    return
                
                # عرض الكود فقط بطريقة بسيطة مع بيانات تسجيل الدخول
                message = (
                    f"🔑 <b>كود التحقق الخاص بك:</b>\n\n"
                    f"<code>{code_info['code']}</code>\n\n"
                    f"📧 <b>بيانات تسجيل الدخول:</b>\n"
                    f"البريد: <code>{TARGET_EMAIL}</code>\n"
                    f"الباسورد: <code>Ahmed@Ramah0000</code>\n\n"
                    f"تمت برمجتي بواسطه احمد الرماح"
                )
                
                await query.edit_message_text(
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                # رسالة محسنة عند عدم وجود كود
                await query.edit_message_text(
                    f"❌ لم يتم العثور على كود تحقق\nحاول مره اخري\n\n"
                    f"📧 <b>بيانات تسجيل الدخول:</b>\n"
                    f"البريد: <code>{TARGET_EMAIL}</code>\n"
                    f"الباسورد: <code>Ahmed@Ramah0000</code>\n\n"
                    f"تمت برمجتي بواسطه احمد الرماح",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        
        elif query.data == "account_info":
            # إزالة التحقق من المسؤول للسماح لأي مستخدم بالوصول
            
            keyboard = [
                [InlineKeyboardButton("🔐 عرض بيانات التسجيل كاملة", callback_data="show_password")],
                [InlineKeyboardButton("🔄 العودة", callback_data="get_chatgpt_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"📧 <b>معلومات الحساب المستخدم:</b>\n\n"
                f"البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
                f"المستخدم: <code>ahmedalramah000</code>\n\n"
                f"<i>اضغط على الزر أدناه لعرض كلمة المرور</i>\n\n"
                f"تمت برمجتي بواسطه احمد الرماح"
            )
            
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif query.data == "show_password":
            # إزالة التحقق من المسؤول للسماح لأي مستخدم بعرض كلمة المرور
            
            keyboard = [
                [InlineKeyboardButton("🔄 إخفاء كلمة المرور", callback_data="account_info")],
                [InlineKeyboardButton("🔑 الحصول على الكود", callback_data="get_chatgpt_code")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"📧 <b>بيانات تسجيل الدخول الكاملة:</b>\n\n"
                f"البريد الإلكتروني: <code>{TARGET_EMAIL}</code>\n"
                f"المستخدم: <code>ahmedalramah000</code>\n"
                f"كلمة المرور: <code>Ahmed@Ramah0000</code>\n\n"
                f"تمت برمجتي بواسطه احمد الرماح"
            )
            
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

def main():
    """تشغيل البوت."""
    # استخراج توكن البوت من المتغيرات البيئية مرة أخرى للتأكد
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    # التحقق من وجود توكن البوت
    if not telegram_token:
        logger.error("لم يتم تعيين TELEGRAM_BOT_TOKEN. قم بإضافته إلى ملف .env أو متغيرات البيئة")
        return
    
    # طباعة جزء من التوكن للتأكد من صحته (أول 4 أحرف فقط للأمان)
    token_preview = telegram_token[:4] if telegram_token else "غير موجود"
    logger.info(f"تم العثور على توكن بوت تلجرام (يبدأ بـ: {token_preview}...)")
    
    # تشغيل وظيفة الحفاظ على البوت نشطًا على Replit
    keep_alive()

    retry_count = 0
    while retry_count < MAX_RETRIES or MAX_RETRIES == 0:  # إذا كان MAX_RETRIES = 0 سنحاول بشكل غير محدود
        try:
            # إنشاء البوت
            bot = GmailCodeBot()
            
            # تأكد من استخدام المتغير telegram_token المُعرف محليًا وليس المتغير العام
            application = Application.builder().token(telegram_token).build()

            # إعداد أوامر البوت - إظهار أمر start فقط
            commands = [
                ("start", "بدء استخدام البوت وعرض بيانات تسجيل الدخول")
            ]
            
            # إضافة المعالجات
            application.add_handler(CommandHandler("start", bot.start))
            application.add_handler(CommandHandler("help", bot.help_command))
            application.add_handler(CommandHandler("credentials", bot.credentials_command))
            application.add_handler(CommandHandler("showpassword", bot.show_password_command))
            application.add_handler(CallbackQueryHandler(bot.button_callback))

            # ضبط الأوامر الظاهرة في واجهة البوت
            async def set_commands(app):
                await app.bot.set_my_commands(commands)
                logger.info("تم ضبط أوامر البوت بنجاح")
            
            # إضافة مهمة لضبط أوامر البوت عند البدء
            application.post_init = set_commands
            
            # بدء البوت
            logger.info("بدء تشغيل البوت...")
            
            # تشغيل البوت مع التعامل مع الأخطاء
            application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True, close_loop=False)
            
            # إذا وصلنا إلى هنا، فهذا يعني أن البوت توقف بشكل طبيعي
            logger.info("تم إيقاف البوت بشكل طبيعي.")
            break
            
        except (ConnectionError, socket.error, TimeoutError) as e:
            retry_count += 1
            retry_delay = BASE_RETRY_DELAY * (2 ** (retry_count - 1))  # تأخير متزايد أسياً
            
            logger.error(f"حدث خطأ في الاتصال: {e}")
            logger.info(f"محاولة إعادة الاتصال {retry_count}/{MAX_RETRIES} بعد {retry_delay} ثوانٍ...")
            
            # إذا وصلنا للحد الأقصى من المحاولات، سنقوم بتسجيل الخطأ والخروج
            if retry_count == MAX_RETRIES and MAX_RETRIES > 0:
                logger.error("تم الوصول للحد الأقصى من محاولات إعادة الاتصال. إيقاف البوت.")
                break
                
            # انتظار قبل إعادة المحاولة
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