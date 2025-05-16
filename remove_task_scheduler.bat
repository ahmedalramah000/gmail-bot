@echo off
echo Removing Windows Task Scheduler for the Telegram bot...

set TASK_NAME=TelegramBotTask

REM Check if the task exists before trying to delete it
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo Found task "%TASK_NAME%", removing it now...
    schtasks /delete /tn "%TASK_NAME%" /f
    echo Task successfully removed.
) else (
    echo Task "%TASK_NAME%" not found. Nothing to remove.
)

echo.
pause 