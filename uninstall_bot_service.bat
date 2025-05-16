@echo off
echo Stopping and removing Bot Service...

REM Stop the service if it's running
sc stop BotTelegramService

REM Remove the service
"%~dp0nssm.exe" remove BotTelegramService confirm

echo Bot service has been removed.
pause 