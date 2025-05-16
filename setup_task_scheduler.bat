@echo off
echo Setting up Windows Task Scheduler for the Telegram bot...

set TASK_NAME=TelegramBotTask
set SCRIPT_PATH=%~dp0start_bot.bat
set SCRIPT_DIR=%~dp0

echo Creating Task Scheduler task to run the bot...

REM Create a scheduled task that runs even when the laptop is closed
schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\"" /sc onstart /ru "%USERNAME%" /rl highest /f

REM Set the task to run with highest privileges
schtasks /change /tn "%TASK_NAME%" /rl highest

REM Set the task to run even when the user is not logged in
schtasks /change /tn "%TASK_NAME%" /ru "SYSTEM"

REM Add additional settings for better reliability
schtasks /change /tn "%TASK_NAME%" /st 00:00 /sd 01/01/2023

REM Configure the task to restart on failure
schtasks /change /tn "%TASK_NAME%" /ri 1 /du 00:05

echo.
echo Task created successfully! The bot will now run automatically:
echo - When the system starts
echo - When the task is triggered manually
echo - Even when the laptop is closed
echo.
echo To run the task immediately, use: schtasks /run /tn "%TASK_NAME%"
echo To check status, use: schtasks /query /tn "%TASK_NAME%"
echo To delete the task, use: schtasks /delete /tn "%TASK_NAME%" /f
echo.

pause 