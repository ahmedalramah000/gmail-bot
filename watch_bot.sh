#!/bin/bash

# سكريبت لمراقبة البوت وإعادة تشغيله إذا توقف
BOT_DIR="$HOME/telegram_bot"
BOT_SCRIPT="$BOT_DIR/gmail_bot.py"
LOG_FILE="$BOT_DIR/watchdog.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

start_bot() {
    cd "$BOT_DIR" || exit 1
    log "بدء تشغيل البوت..."
    nohup python3 "$BOT_SCRIPT" > "$BOT_DIR/bot.log" 2>&1 &
    BOT_PID=$!
    log "تم تشغيل البوت بنجاح (PID: $BOT_PID)"
}

check_bot() {
    if pgrep -f "python3 $BOT_SCRIPT" > /dev/null; then
        return 0  # البوت يعمل
    else
        return 1  # البوت متوقف
    fi
}

# إنشاء مجلد البوت إذا لم يكن موجودًا
mkdir -p "$BOT_DIR"

log "بدء تشغيل مراقب البوت..."

# التحقق من وجود البوت
if [ ! -f "$BOT_SCRIPT" ]; then
    log "خطأ: ملف البوت غير موجود في $BOT_SCRIPT"
    exit 1
fi

# حلقة مراقبة البوت
while true; do
    if ! check_bot; then
        log "البوت متوقف، جاري إعادة التشغيل..."
        start_bot
    else
        log "البوت يعمل بشكل طبيعي"
    fi
    
    # انتظار 5 دقائق قبل الفحص التالي
    sleep 300
done 