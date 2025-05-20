#!/bin/bash
echo "Setting up environment file with UTF-8 encoding..."
cat env_config.txt > .env
echo "Environment file has been set up successfully!"
echo
echo "You can now run the bot with one of the following commands:"
echo "python gmail_bot.py"
echo "or"
echo "python openai_code_forwarder.py"
echo
echo "Press any key to continue..."
read -n 1 