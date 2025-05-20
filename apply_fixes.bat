@echo off
echo Applying fixes to Gmail-Telegram bot...
python openai_code_forwarder.py

echo.
echo Fixes applied successfully!
echo.
echo Press any key to run the fixed bot...
pause > nul

echo Starting fixed bot...
python fixed_gmail_bot.py 