"""
ملف الإعدادات للبوت الخاص بك
"""

import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env إذا كان موجوداً
load_dotenv()

# إعدادات التليجرام
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# البريد الإلكتروني المستهدف
TARGET_EMAIL = os.environ.get('TARGET_EMAIL', "ahmedalramah000@gmail.com")

# قائمة مرسلي البريد الإلكتروني المسموح بهم
EMAIL_SENDERS = os.environ.get('EMAIL_SENDERS', "no-reply@openai.com,login-code@openai.com,noreply@tm.openai.com").split(',')

# فترة فحص البريد الإلكتروني (بالثواني)
EMAIL_CHECK_INTERVAL = int(os.environ.get('EMAIL_CHECK_INTERVAL', 60))

# المدة الزمنية للبحث عن الأكواد (بالدقائق)
CODE_SEARCH_MINUTES = int(os.environ.get('CODE_SEARCH_MINUTES', 60))

# الحد الأقصى للاستعلامات لكل مستخدم
RATE_LIMIT_PER_USER = int(os.environ.get('RATE_LIMIT_PER_USER', 10))

# إعدادات طريقة المصادقة مع Gmail
# يمكن استخدام App Password بدلاً من OAuth
USE_APP_PASSWORD = os.environ.get('USE_APP_PASSWORD', 'false').lower() == 'true'
APP_PASSWORD = os.environ.get('APP_PASSWORD', '')  # كلمة مرور التطبيق من Google

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
GMAIL_CREDENTIALS_FILE = os.environ.get('GMAIL_CREDENTIALS_FILE', 'credentials.json.json')
GMAIL_TOKEN_FILE = os.environ.get('GMAIL_TOKEN_FILE', 'token.json')
GMAIL_API_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'] 