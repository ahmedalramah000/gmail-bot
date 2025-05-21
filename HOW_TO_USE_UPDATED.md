# دليل استخدام البوت المُحدَّث

## الميزات الجديدة
تم تحديث البوت ليشمل الميزات التالية:
1. تحميل ملفات المصادقة (`credentials.json` و `token.json`) تلقائيًا من Google Drive
2. التعامل بشكل أفضل مع أخطاء ملف `token.json`
3. التعامل مع حالات تشغيل نسختين من البوت في نفس الوقت

## خطوات الإعداد

### 1. رفع ملفات المصادقة على Google Drive

1. قم برفع ملفي `credentials.json` و `token.json` على Google Drive
2. انقر بزر الماوس الأيمن على كل ملف واختر "احصل على الرابط" | "Get link"
3. تأكد من تعيين صلاحيات المشاركة إلى "أي شخص لديه الرابط يمكنه الوصول" | "Anyone with the link can view"
4. انسخ الرابط الذي يظهر، سيكون بهذا الشكل:
   ```
   https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view?usp=sharing
   ```

### 2. تحويل روابط Google Drive إلى روابط مباشرة

1. استخرج معرّف الملف (ID) من الرابط (الجزء بين `/d/` و `/view`)
   - في المثال السابق، معرّف الملف هو: `1AbCdEfGhIjKlMnOpQrStUvWxYz`

2. استبدل الرابط بصيغة التنزيل المباشر:
   ```
   https://drive.google.com/uc?export=download&id=ID_FILE
   ```
   
   حيث `ID_FILE` هو معرّف الملف الذي استخرجته.

3. على سبيل المثال، الرابط:
   ```
   https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view?usp=sharing
   ```
   
   يصبح:
   ```
   https://drive.google.com/uc?export=download&id=1AbCdEfGhIjKlMnOpQrStUvWxYz
   ```

### 3. إعداد ملف البيئة (.env)

1. انسخ ملف `env_template_new` إلى ملف جديد باسم `.env`:
   ```bash
   cp env_template_new .env
   ```

2. افتح ملف `.env` بأي محرر نصوص وأضف روابط الملفات المباشرة:
   ```
   CREDENTIALS_URL=https://drive.google.com/uc?export=download&id=معرف_ملف_credentials
   TOKEN_URL=https://drive.google.com/uc?export=download&id=معرف_ملف_token
   ```

3. أضف أيضًا متغيرات البيئة الأخرى المطلوبة:
   ```
   TELEGRAM_BOT_TOKEN=توكن_البوت_الخاص_بك
   TELEGRAM_CHAT_ID=معرف_المشرف
   TARGET_EMAIL=البريد_الإلكتروني
   PASSWORD=كلمة_المرور
   ```

### 4. تشغيل البوت

```bash
python gmail_bot.py
```

عند بدء التشغيل، سيحاول البوت تلقائيًا:
1. تحميل ملف `credentials.json` من الرابط المحدد في `CREDENTIALS_URL`
2. تحميل ملف `token.json` من الرابط المحدد في `TOKEN_URL`
3. استخدام الملفات المحلية إذا فشل التحميل

## تشخيص المشاكل

### إذا فشل تحميل الملفات:

1. تحقق من صحة الروابط في ملف `.env`
2. تأكد من أن إعدادات المشاركة تسمح بالوصول العام
3. يمكنك نسخ الملفات يدويًا إلى مجلد البوت

### إذا ظهرت رسالة حول نسخة أخرى من البوت:

هذه رسالة طبيعية عندما تكون هناك نسخة أخرى من البوت قيد التشغيل. تحقق من:
1. إذا كان البوت يعمل بالفعل في نافذة أخرى
2. إذا كان البوت يعمل كخدمة في الخلفية
3. قم بإيقاف النسخة الأخرى قبل تشغيل نسخة جديدة

## ملاحظات هامة

- احرص على عدم مشاركة ملفات المصادقة علنًا، حتى لو كانت على Google Drive
- تأكد من أن روابط الملفات المباشرة صحيحة
- إذا تم تغيير ملفات المصادقة، سيتعين عليك تحديث الروابط في ملف `.env` 