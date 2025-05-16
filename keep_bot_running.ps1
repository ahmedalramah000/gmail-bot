# سكريبت للحفاظ على تشغيل البوت باستمرار
# يقوم بإعادة تشغيل البوت تلقائيًا إذا توقف لأي سبب

# تكوين عدم السماح للحاسوب بالدخول في وضع السكون
try {
    # تعطيل السكون 
    $ErrorActionPreference = "SilentlyContinue"
    # منع جهاز الكمبيوتر من الدخول في وضع السكون أثناء تشغيل السكريبت
    $powerCfg = Start-Process -FilePath "powercfg.exe" -ArgumentList "/change standby-timeout-ac 0" -NoNewWindow -Wait -PassThru
    $powerCfg = Start-Process -FilePath "powercfg.exe" -ArgumentList "/change hibernate-timeout-ac 0" -NoNewWindow -Wait -PassThru
    $powerCfg = Start-Process -FilePath "powercfg.exe" -ArgumentList "/change disk-timeout-ac 0" -NoNewWindow -Wait -PassThru
    $powerCfg = Start-Process -FilePath "powercfg.exe" -ArgumentList "/change monitor-timeout-ac 0" -NoNewWindow -Wait -PassThru
    
    Write-Host "تم تعطيل وضع السكون بنجاح للحفاظ على البوت نشطًا" -ForegroundColor Green
}
catch {
    Write-Host "لم نتمكن من تعطيل وضع السكون تلقائيًا. قد يتوقف البوت إذا دخل الجهاز في وضع السكون." -ForegroundColor Yellow
}

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$botScript = Join-Path -Path $scriptPath -ChildPath "gmail_bot.py"
$logFile = Join-Path -Path $scriptPath -ChildPath "bot_log.txt"

# وظيفة لكتابة السجلات مع الوقت
function Write-Log {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    # عرض في وحدة التحكم
    Write-Host $logMessage -ForegroundColor $ForegroundColor
    
    # إضافة إلى ملف السجل
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "بدء تشغيل بوت أكواد ChatGPT..." -ForegroundColor Green
Write-Log "البوت سيظل يعمل باستمرار وسيعاد تشغيله تلقائيًا إذا توقف" -ForegroundColor Green
Write-Log "اضغط Ctrl+C مع Hold لإيقاف السكريبت" -ForegroundColor Yellow
Write-Log ""

# ضبط عدد المحاولات وتأخير إعادة المحاولة
$maxRetries = 0  # 0 يعني عدد غير محدود من المحاولات
$baseRetryDelay = 5 # ثوانٍ
$retryCount = 0

while ($true) {
    $retryDelay = $baseRetryDelay * [Math]::Pow(2, [Math]::Min($retryCount, 6))  # زيادة أسية مع حد أقصى
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Log "[$timestamp] بدء تشغيل البوت..." -ForegroundColor Cyan
    
    try {
        # تشغيل البوت
        $process = Start-Process -FilePath "python" -ArgumentList $botScript -NoNewWindow -PassThru
        
        # انتظار انتهاء العملية
        $process.WaitForExit()
        
        $exitCode = $process.ExitCode
        
        if ($exitCode -eq 0) {
            Write-Log "البوت انتهى بشكل طبيعي. جاري إعادة التشغيل..." -ForegroundColor Yellow
            $retryCount = 0  # إعادة تعيين عداد المحاولات عند الإنهاء الطبيعي
        } 
        else {
            $retryCount++
            Write-Log "البوت توقف بشكل غير طبيعي (كود الخروج: $exitCode). محاولة إعادة التشغيل..." -ForegroundColor Red
        }
    } 
    catch {
        $retryCount++
        Write-Log "حدث خطأ: $_" -ForegroundColor Red
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    if ($maxRetries -gt 0 -and $retryCount -ge $maxRetries) {
        Write-Log "تم الوصول إلى الحد الأقصى لعدد المحاولات ($maxRetries). إيقاف السكريبت." -ForegroundColor Red
        break
    }
    
    Write-Log "[$timestamp] توقف البوت. إعادة التشغيل خلال $retryDelay ثوانٍ..." -ForegroundColor Yellow
    
    # انتظار قبل إعادة التشغيل
    Start-Sleep -Seconds $retryDelay
} 