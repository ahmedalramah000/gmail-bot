@echo off
echo Starting ChatGPT Code Bot...
echo The bot will restart automatically if it stops.
echo Press Ctrl+C to stop.
echo.

:loop
python gmail_bot.py
echo Bot stopped. Restarting in 5 seconds...
timeout /t 5
goto loop 