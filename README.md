# بوت تلجرام لأكواد ChatGPT

بوت تلجرام يقوم بمراقبة بريدك الإلكتروني للحصول على أكواد التحقق من ChatGPT وإرسالها إليك عبر تلجرام، مما يسهل تسجيل الدخول إلى ChatGPT من أجهزة مختلفة.

## المميزات

- مراقبة بريد Gmail للرسائل من OpenAI (no-reply@openai.com, login-code@openai.com, noreply@tm.openai.com)
- استخراج أكواد التحقق المكونة من 6 أرقام من محتوى البريد
- إرسال الأكواد إلى محادثة تلجرام محددة
- يعمل باستمرار، ويتحقق من الرسائل الجديدة على فترات قابلة للتكوين
- يرسل فقط الأكواد الجديدة والفريدة
- يتعامل مع تنسيقات البريد المختلفة وترميز Base64
- تمييز بين أكواد تسجيل الدخول وأكواد إعادة تعيين كلمة المرور
- واجهة زر سهلة الاستخدام للحصول على آخر كود
- دعم المصادقة عبر App Password أو OAuth (خياران مختلفان للمصادقة)

## الإعداد

### المتطلبات

- Python 3.6+
- حساب في Google Cloud Platform (إذا كنت تستخدم OAuth) أو App Password من Gmail (أسهل)
- بوت تلجرام ومعرف محادثة

### 1. تثبيت المكتبات المطلوبة

```bash
pip install -r requirements.txt
```

### 2. طرق المصادقة مع Gmail

يمكنك استخدام إحدى الطريقتين التاليتين للمصادقة مع Gmail:

#### الطريقة 1: استخدام OAuth (الطريقة التقليدية)

1. انتقل إلى [لوحة تحكم Google Cloud](https://console.cloud.google.com/)
2. أنشئ مشروعًا جديدًا
3. انتقل إلى "APIs & Services" > "Library"
4. ابحث عن "Gmail API" وقم بتفعيله
5. انتقل إلى "APIs & Services" > "Credentials"
6. انقر على "Create Credentials" > "OAuth client ID"
7. قم بتكوين شاشة الموافقة على OAuth (يمكن أن تكون "External" للاختبار)
8. اختر "Desktop app" كنوع التطبيق
9. قم بتنزيل ملف JSON وحفظه باسم `credentials.json.json` في مجلد المشروع

#### الطريقة 2: استخدام App Password (أسهل وموصى بها لتجنب مشاكل التوكن)

1. قم بتفعيل المصادقة الثنائية على حساب Google الخاص بك:
   - انتقل إلى [إعدادات أمان Google](https://myaccount.google.com/security)
   - قم بتفعيل المصادقة ذات الخطوتين إذا لم تكن مفعلة بالفعل
2. إنشاء كلمة مرور للتطبيق:
   - انتقل إلى [كلمات مرور التطبيقات](https://myaccount.google.com/apppasswords)
   - اختر "تطبيق آخر" واكتب اسمًا مثل "بوت تلجرام"
   - انسخ كلمة المرور المكونة من 16 حرفًا التي تم إنشاؤها
3. قم بتعديل ملف `.env` أو `env_template` وضبط:
   - `USE_APP_PASSWORD=true`
   - `APP_PASSWORD=YOUR_APP_PASSWORD` (كلمة المرور التي حصلت عليها)
4. مع هذه الطريقة، لن تحتاج إلى ملفات `credentials.json.json` أو `token.json`

### 3. إنشاء بوت تلجرام

1. افتح تلجرام وابحث عن [@BotFather](https://t.me/botfather)
2. أرسل الأمر `/newbot` واتبع التعليمات
3. انسخ رمز البوت (token) الذي يقدمه BotFather
4. ابدأ محادثة مع البوت الجديد الخاص بك
5. احصل على معرف المحادثة الخاص بك عن طريق:
   - إضافة [@userinfobot](https://t.me/userinfobot) إلى المحادثة
   - سيرد البوت بمعرف المحادثة الخاص بك

### 4. تكوين البوت

قم بإنشاء ملف `.env` في مجلد المشروع بالمحتوى التالي (أو قم بتعديل ملف `env_template`):

```
# إعدادات التليجرام
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# البريد الإلكتروني المستخدم
TARGET_EMAIL=your_target_email@example.com
PASSWORD=your_password

# إعدادات طريقة المصادقة مع Gmail
# اختر طريقة المصادقة:
# - لاستخدام OAuth (الطريقة الافتراضية): اجعل USE_APP_PASSWORD=false
# - لاستخدام App Password: اجعل USE_APP_PASSWORD=true وأدخل كلمة مرور التطبيق في APP_PASSWORD
USE_APP_PASSWORD=false
APP_PASSWORD=

# قائمة مرسلي البريد الإلكتروني المسموح بهم
EMAIL_SENDERS=no-reply@openai.com,login-code@openai.com,noreply@tm.openai.com

# المدة الزمنية للبحث عن الأكواد (بالدقائق)
CODE_SEARCH_MINUTES=60

# الحد الأقصى للاستعلامات لكل مستخدم
RATE_LIMIT_PER_USER=10

# ملفات Gmail API (لازمة فقط إذا كنت تستخدم OAuth)
GMAIL_CREDENTIALS_FILE=credentials.json.json
GMAIL_TOKEN_FILE=token.json
```

استبدل القيم الموجودة بالقيم الفعلية الخاصة بك.

## تشغيل البوت

### تشغيل محلي

```bash
python gmail_bot.py
```

في المرة الأولى التي تقوم فيها بتشغيل البوت، سيفتح نافذة متصفح تطلب منك المصادقة للوصول إلى حساب Gmail الخاص بك. بعد المصادقة، سيبدأ البوت في مراقبة صندوق الوارد الخاص بك.

### تشغيل على Replit (24/7 مجانًا)

للحفاظ على البوت يعمل 24/7 مجانًا على Replit:

1. إنشاء حساب على [Replit](https://replit.com)
2. إنشاء Repl جديد واختيار Python
3. رفع جميع ملفات المشروع أو النسخ من GitHub
4. إضافة بيانات الاعتماد الخاصة بك:
   - انتقل إلى علامة التبويب Secrets (أيقونة القفل في الشريط الجانبي)
   - أضف جميع متغيرات البيئة الخاصة بك (نفس ما في ملف .env)
5. يتضمن المشروع `keep_alive.py` الذي ينشئ خادم ويب لمنع Replit من إيقاف التشغيل
6. قم بإعداد مراقب وقت التشغيل:
   - أنشئ حسابًا على [UptimeRobot](https://uptimerobot.com)
   - أضف مراقبًا جديدًا من نوع HTTP(s)
   - استخدم عنوان URL لمشروع Replit الخاص بك (سيكون شيئًا مثل `https://your-project-name.your-username.repl.co`)
   - اضبط فترة المراقبة على 5 دقائق
7. انقر على "Run" لبدء تشغيل البوت

### تشغيل على Oracle Cloud (مجاني مدى الحياة)

لتشغيل البوت 24/7 على Oracle Cloud Always Free:

1. قم بالتسجيل في [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
2. أنشئ خادمًا افتراضيًا (VM) باستخدام Oracle Linux
3. ارفع ملفات المشروع إلى الخادم
4. اتبع تعليمات الإعداد والتثبيت في ملف `setup_oracle_cloud.sh` المرفق مع المشروع
5. استخدم الملفات المساعدة (`run_bot.sh`, `setup_service.sh`) لتشغيل البوت كخدمة نظام تعمل في الخلفية
6. اضبط البوت ليعمل تلقائيًا عند إعادة تشغيل الخادم باستخدام `setup_autostart.sh`

### تشغيل على Render (مجاني)

خدمة Render توفر استضافة مجانية للتطبيقات:

1. أنشئ حسابًا على [Render](https://render.com/) 
2. انقر على "New" ثم اختر "Web Service"
3. اختر "Build and deploy from a Git repository"
4. اختر مستودع GitHub الخاص بك: `https://github.com/ahmedalramah000/gmail-bot`
5. املأ التفاصيل التالية:
   - **Name**: `telegrambot` (أو أي اسم تريده)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python gmail_bot.py`
6. اختر الخطة المجانية Free Plan
7. في قسم "Environment Variables"، أضف المتغيرات التالية:
   - `TELEGRAM_BOT_TOKEN`: توكن البوت الخاص بك
   - `TELEGRAM_CHAT_ID`: معرف المحادثة الخاص بك
   - `TARGET_EMAIL`: بريدك الإلكتروني
   - `CREDENTIALS_URL`: رابط مباشر لملف `credentials.json.json` (من Google Drive أو Dropbox)
   - `TOKEN_URL`: رابط مباشر لملف `token.json` (من Google Drive أو Dropbox)
8. انقر على "Create Web Service"

#### كيفية الحصول على روابط مباشرة للملفات:

1. **لملفات Google Drive**:
   - ارفع الملفات إلى Google Drive
   - شارك الملف وحدد "أي شخص لديه الرابط"
   - استخرج معرف الملف من رابط المشاركة (الجزء بعد `/d/` وقبل `/view`)
   - أنشئ رابطًا بالصيغة: `https://drive.google.com/uc?export=download&id=FILE_ID`

2. **لملفات Dropbox**:
   - ارفع الملفات إلى Dropbox
   - شارك الملف للحصول على رابط عام
   - استبدل `dl=0` بـ `dl=1` في نهاية الرابط

#### ملاحظات هامة:
- تأكد من أن الروابط مباشرة وتؤدي إلى تحميل الملفات فورًا
- لا تشارك روابط ملفات الاعتماد مع أي شخص
- يمكنك استخدام خدمات أخرى مثل GitHub Gist (رابط خام) أو أي خدمة استضافة ملفات تتيح روابط مباشرة

## اعتبارات الأمان

- البوت يتطلب فقط وصول للقراءة فقط إلى بريد Gmail الخاص بك
- يتم تخزين رمز تفويض Gmail محليًا في ملف `token.json`
- ضع في اعتبارك تشغيل هذا على جهاز آمن وقيد التشغيل دائمًا مثل Raspberry Pi أو خادم سحابي
- لا تشارك أبدًا ملفات `credentials.json.json` أو `token.json` الخاصة بك

## استكشاف الأخطاء وإصلاحها

- **خطأ invalid_grant: Token has been expired or revoked**: هذا يعني أن توكن OAuth قد انتهت صلاحيته. يمكنك حل هذه المشكلة بإحدى الطريقتين:
  1. حذف ملف `token.json` وإعادة تشغيل البوت ليقوم بعملية المصادقة من جديد
  2. التحويل لاستخدام App Password بدلاً من OAuth (أنظر القسم الخاص بطرق المصادقة)

- **أخطاء المصادقة**: احذف ملف `token.json` وأعد تشغيل البوت لإعادة المصادقة.
- **لم يتم العثور على رسائل بريد إلكتروني**: تحقق من استخدام عناوين البريد الإلكتروني الصحيحة للمرسل في التكوين الخاص بك.
- **أخطاء تلجرام**: تحقق من رمز البوت ومعرف المحادثة، وتأكد من أن البوت لديه إذن لإرسال رسائل إلى المحادثة.
- **مشاكل التشفير**: إذا واجهت أخطاء Unicode أو تشفير، تأكد من أن نظام التشغيل الخاص بك يدعم الحروف العربية ومتغيرات البيئة مضبوطة على UTF-8.

## الرخصة

هذا المشروع مرخص بموجب ترخيص MIT - راجع ملف LICENSE للحصول على التفاصيل.

# دليل تشغيل بوت التليجرام على Oracle Cloud

هذا الدليل يشرح كيفية إعداد البوت للعمل على Oracle Cloud Always Free بشكل دائم ومستمر.

## خطوات الإعداد

### 1. التسجيل في Oracle Cloud

1. قم بالتسجيل في [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
2. أكمل عملية التسجيل واختر منطقة قريبة منك
3. انتظر حتى يتم تفعيل حسابك (قد يستغرق هذا بضع ساعات)

### 2. إنشاء خادم افتراضي

1. سجل الدخول إلى لوحة تحكم Oracle Cloud
2. انتقل إلى **Compute** > **Instances**
3. انقر على **Create Instance**
4. اختر اسمًا للخادم
5. في قسم **Image and shape**، تأكد من اختيار **Oracle Linux** (الإصدار الأحدث)
6. في قسم **Networking**، تأكد من اختيار **Assign a public IPv4 address**
7. انقر على **Create**

### 3. الاتصال بالخادم

1. بعد إنشاء الخادم، سيتم عرض تفاصيل الاتصال بما في ذلك عنوان IP
2. اتصل بالخادم باستخدام SSH:
   - على Windows: استخدم PuTTY أو Windows Terminal: `ssh opc@YOUR_IP_ADDRESS`
   - على Mac/Linux: افتح Terminal واكتب: `ssh opc@YOUR_IP_ADDRESS`
3. استخدم المفتاح الخاص الذي تم تنزيله أثناء إنشاء الخادم للاتصال

### 4. نقل الملفات إلى الخادم

نقل الملفات باستخدام SCP:
```bash
scp -i /path/to/private_key setup_oracle_cloud.sh run_bot.sh setup_autostart.sh setup_service.sh gmail_bot.py config.py keep_alive.py requirements.txt credentials.json.json token.json opc@YOUR_IP_ADDRESS:~/
```

أو استخدم برنامج نقل ملفات SFTP مثل FileZilla.

### 5. إعداد بيئة التشغيل

1. اتصل بالخادم عبر SSH
2. نفذ سكريبت الإعداد:
   ```bash
   chmod +x setup_oracle_cloud.sh
   ./setup_oracle_cloud.sh
   ```

### 6. نقل ملفات البوت إلى المجلد المناسب

1. انقل جميع ملفات البوت إلى مجلد `telegram_bot`:
   ```bash
   cp *.py *.json *.json.json .env ~/telegram_bot/
   ```

### 7. طرق تشغيل البوت (اختر طريقة واحدة)

#### الطريقة 1: التشغيل باستخدام سكريبت التشغيل

1. اجعل السكريبت قابل للتنفيذ ثم شغله:
   ```bash
   chmod +x run_bot.sh
   ./run_bot.sh
   ```

#### الطريقة 2: إعداد تشغيل تلقائي عند إعادة التشغيل

1. اجعل السكريبت قابل للتنفيذ ثم شغله:
   ```bash
   chmod +x setup_autostart.sh
   ./setup_autostart.sh
   ```

#### الطريقة 3: إعداد البوت كخدمة نظام (موصى بها)

1. اجعل السكريبت قابل للتنفيذ ثم شغله:
   ```bash
   chmod +x setup_service.sh
   ./setup_service.sh
   ```

## التحقق من عمل البوت

بعد الإعداد، يمكنك التحقق من عمل البوت بإحدى الطرق التالية:

- إذا كنت تستخدم البوت كخدمة:
  ```bash
  sudo systemctl status telegram-bot
  ```

- لعرض سجلات البوت:
  ```bash
  tail -f ~/telegram_bot/bot.log
  ```

## استكشاف الأخطاء وإصلاحها

إذا واجهت مشاكل، تحقق من:

1. تأكد من وجود جميع ملفات البوت في المجلد `~/telegram_bot`
2. تأكد من تثبيت جميع المكتبات المطلوبة:
   ```bash
   pip3 install -r requirements.txt
   ```
3. تحقق من سجلات البوت:
   ```bash
   tail -f ~/telegram_bot/bot.log
   ```

## أوامر مفيدة

- تشغيل البوت يدويًا: `cd ~/telegram_bot && python3 gmail_bot.py`
- إعادة تشغيل خدمة البوت: `sudo systemctl restart telegram-bot`
- إيقاف البوت: `sudo systemctl stop telegram-bot`
- عرض سجلات الخدمة: `journalctl -u telegram-bot`
- عرض جلسات screen النشطة: `screen -ls`
- الاتصال بجلسة screen: `screen -r telegram_bot`