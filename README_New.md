# بوت تلجرام للحصول على أكواد التحقق من ChatGPT | Telegram Bot for ChatGPT Verification Codes

## 🇸🇦 الوصف

بوت تلجرام يقوم باستخراج أكواد التحقق من بريد Gmail المرتبط بحساب ChatGPT. البوت يقوم بالاتصال بـ Gmail عبر Gmail API أو App Password لاستخراج آخر رمز تحقق تم إرساله من OpenAI.

## 🇬🇧 Description

A Telegram bot that extracts verification codes from a Gmail account associated with ChatGPT. The bot connects to Gmail via the Gmail API or App Password to extract the latest verification code sent by OpenAI.

---

## 🔄 التحديث الجديد | New Update

### 🇸🇦 المميزات الجديدة:

1. **تحميل ملفات المصادقة تلقائيًا**: البوت يقوم الآن بتحميل ملفات `credentials.json` و `token.json` تلقائياً من Google Drive.
2. **تحسين التعامل مع ملف Token**: إصلاح طريقة التعامل مع ملف `token.json` عندما يكون غير موجود أو غير صالح.
3. **التعامل مع تعارض البوت**: تحسين الرسائل التي تظهر عندما تكون هناك نسخة أخرى من البوت قيد التشغيل.

### 🇬🇧 New Features:

1. **Automatic Authentication Files Download**: The bot now downloads `credentials.json` and `token.json` files automatically from Google Drive.
2. **Improved Token File Handling**: Fixed handling of `token.json` file when it's missing or invalid.
3. **Bot Conflict Handling**: Improved messages when another instance of the bot is already running.

---

## ⚙️ الإعداد | Setup

### 🇸🇦 ملف البيئة (.env):

```
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Admin Chat ID
TELEGRAM_CHAT_ID=your_admin_chat_id

# روابط ملفات المصادقة من Google Drive
CREDENTIALS_URL=https://drive.google.com/uc?export=download&id=your_credentials_id
TOKEN_URL=https://drive.google.com/uc?export=download&id=your_token_id

# إعدادات البريد الإلكتروني
TARGET_EMAIL=your_email@gmail.com
PASSWORD=your_password
EMAIL_SENDERS=no-reply@openai.com,login-code@openai.com,noreply@tm.openai.com
CODE_SEARCH_MINUTES=60
RATE_LIMIT_PER_USER=10

# إعدادات App Password
USE_APP_PASSWORD=false
APP_PASSWORD=
```

### 🇬🇧 Environment File (.env):

```
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Admin Chat ID
TELEGRAM_CHAT_ID=your_admin_chat_id

# Gmail Authentication URLs from Google Drive
CREDENTIALS_URL=https://drive.google.com/uc?export=download&id=your_credentials_id
TOKEN_URL=https://drive.google.com/uc?export=download&id=your_token_id

# Email Settings
TARGET_EMAIL=your_email@gmail.com
PASSWORD=your_password
EMAIL_SENDERS=no-reply@openai.com,login-code@openai.com,noreply@tm.openai.com
CODE_SEARCH_MINUTES=60
RATE_LIMIT_PER_USER=10

# App Password Settings
USE_APP_PASSWORD=false
APP_PASSWORD=
```

---

## 🚀 التثبيت والتشغيل | Installation and Running

### 🇸🇦 التثبيت:

```bash
# تثبيت المكتبات المطلوبة
pip install -r requirements.txt

# إعداد ملف البيئة
cp env_template_new .env
# قم بتعديل ملف .env بمعلوماتك الخاصة
```

### 🇬🇧 Installation:

```bash
# Install required libraries
pip install -r requirements.txt

# Setup environment file
cp env_template_new .env
# Edit .env file with your information
```

### 🇸🇦 التشغيل:

```bash
# تشغيل البوت
python gmail_bot.py

# للتشغيل في الخلفية (لينكس/ماك)
nohup python gmail_bot.py &

# للتشغيل في الخلفية (ويندوز)
start /b python gmail_bot.py
```

### 🇬🇧 Running:

```bash
# Run the bot
python gmail_bot.py

# Run in background (Linux/Mac)
nohup python gmail_bot.py &

# Run in background (Windows)
start /b python gmail_bot.py
```

---

## 🔒 إعداد ملفات المصادقة | Authentication Files Setup

### 🇸🇦 تحميل الملفات إلى Google Drive:

1. أنشئ ملفات `credentials.json` و `token.json` باستخدام Google API Console
2. قم برفع الملفات إلى Google Drive
3. قم بالنقر بزر الماوس الأيمن على كل ملف واختر "احصل على رابط"
4. تأكد من أن الإعداد هو "أي شخص لديه الرابط يمكنه الوصول"
5. قم بتحويل الرابط إلى صيغة التنزيل المباشر:
   - من: `https://drive.google.com/file/d/YOUR_FILE_ID/view?usp=sharing`
   - إلى: `https://drive.google.com/uc?export=download&id=YOUR_FILE_ID`
6. أضف الروابط المباشرة إلى ملف `.env`

### 🇬🇧 Uploading Files to Google Drive:

1. Create `credentials.json` and `token.json` files using Google API Console
2. Upload the files to Google Drive
3. Right-click each file and select "Get link"
4. Make sure the setting is "Anyone with the link can access"
5. Convert the link to direct download format:
   - From: `https://drive.google.com/file/d/YOUR_FILE_ID/view?usp=sharing`
   - To: `https://drive.google.com/uc?export=download&id=YOUR_FILE_ID`
6. Add the direct links to your `.env` file

---

## 🤖 أوامر البوت | Bot Commands

### 🇸🇦 الأوامر:
- `/start` - بدء استخدام البوت وعرض القائمة الرئيسية
- `/help` - عرض معلومات المساعدة
- `/credentials` - عرض بيانات تسجيل الدخول
- `/showpassword` - عرض كلمة المرور
- `/admin_panel` - الوصول إلى لوحة المسؤول (للمسؤول فقط)

### 🇬🇧 Commands:
- `/start` - Start using the bot and display the main menu
- `/help` - Show help information
- `/credentials` - Show login credentials
- `/showpassword` - Show password
- `/admin_panel` - Access admin panel (admin only)

---

## 📝 المتطلبات | Requirements

تم تحديث ملف `requirements.txt` ليتضمن:

```
python-telegram-bot>=20.0
google-auth-oauthlib>=0.4.6
google-api-python-client>=2.0.0
python-dotenv>=0.19.0
requests>=2.28.0
```

---

## 👨‍💻 المطور | Developer

تمت برمجة البوت بواسطة **أحمد الرماح**

The bot was developed by **Ahmed Alramah** 