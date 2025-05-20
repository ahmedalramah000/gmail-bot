@echo off
echo Setting up admin button on the bot...
echo ---------------------------------------

echo Step 1: Stopping any running bot instances...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Step 2: Creating backup of the bot file...
copy gmail_bot.py gmail_bot.py.bak

echo Step 3: Instructions for manual update:
echo.
echo ---------------------------------------
echo PLEASE FOLLOW THESE INSTRUCTIONS TO UPDATE YOUR BOT:
echo ---------------------------------------
echo.
echo 1. Open gmail_bot.py in a text editor
echo.
echo 2. Find the start function and replace it with this correctly formatted code:
echo    (See fixed_start_function.py for the correct code)
echo.
echo 3. Find the button_callback function and add admin panel code:
echo    (See admin_panel_callback.py for the code to add)
echo.
echo 4. Save and close the file after making these changes
echo.
echo 5. Run the bot with: python gmail_bot.py
echo.
echo ---------------------------------------
echo.
echo You can find the needed code in files:
echo - fixed_start_function.py
echo - admin_panel_callback.py
echo.
echo Press any key to exit...
pause 