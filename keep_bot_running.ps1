# سكريبت للحفاظ على البوت قيد التشغيل
$process = Start-Process python -ArgumentList "gmail_bot.py" -PassThru
Write-Host "تم تشغيل البوت بنجاح! معرف العملية:" $process.Id
Write-Host "البوت يعمل الآن في الخلفية ويتابع رسائل البريد..."
Write-Host "لإيقاف البوت، استخدم الأمر: Stop-Process -Id" $process.Id 