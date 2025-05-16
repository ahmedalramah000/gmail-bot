@echo off
echo Installing Bot Service...

REM Download NSSM if not already available
if not exist "%~dp0nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%TEMP%\nssm.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm'"
    powershell -Command "Copy-Item '%TEMP%\nssm\nssm-2.24\win64\nssm.exe' -Destination '%~dp0'"
    del "%TEMP%\nssm.zip"
    rmdir /S /Q "%TEMP%\nssm"
)

REM Get full path to PowerShell and the script
set POWERSHELL_PATH=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe
set SCRIPT_PATH=%~dp0keep_bot_running.ps1

REM Install the service
"%~dp0nssm.exe" install BotTelegramService "%POWERSHELL_PATH%" "-ExecutionPolicy Bypass -File \"%SCRIPT_PATH%\""
"%~dp0nssm.exe" set BotTelegramService DisplayName "Telegram Bot Service"
"%~dp0nssm.exe" set BotTelegramService Description "Keeps the Telegram bot running continuously"
"%~dp0nssm.exe" set BotTelegramService Start SERVICE_AUTO_START
"%~dp0nssm.exe" set BotTelegramService AppStdout "%~dp0service_output.log"
"%~dp0nssm.exe" set BotTelegramService AppStderr "%~dp0service_error.log"

REM Start the service
"%~dp0nssm.exe" start BotTelegramService

echo Bot service installed and started successfully!
echo The bot will now run continuously even when you close your laptop.
echo.
echo Management commands:
echo - To check status: sc query BotTelegramService
echo - To stop: sc stop BotTelegramService
echo - To start: sc start BotTelegramService
echo - To uninstall: nssm remove BotTelegramService

pause 