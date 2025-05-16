#!/usr/bin/env python3
"""
Setup script for OpenAI Code Forwarder.
Validates the configuration and performs initial authorization.
"""

import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Import config
from config import (
    GMAIL_CREDENTIALS_FILE,
    GMAIL_TOKEN_FILE,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    EMAIL_SENDERS,
    GMAIL_API_SCOPES
)

def validate_config():
    """Validate that all required configuration is present."""
    missing = []
    
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    
    if not os.path.exists(GMAIL_CREDENTIALS_FILE):
        print(f"Error: Gmail credentials file not found: {GMAIL_CREDENTIALS_FILE}")
        print("Please download credentials.json from Google Cloud Console")
        sys.exit(1)
    
    if missing:
        print(f"Error: Missing required configuration: {', '.join(missing)}")
        print("Please create a .env file with these variables or set them in your environment.")
        sys.exit(1)

def authenticate_gmail():
    """Authenticate with Gmail API and generate token file."""
    creds = None
    
    # Check if token already exists
    if os.path.exists(GMAIL_TOKEN_FILE):
        print(f"Token file already exists: {GMAIL_TOKEN_FILE}")
        with open(GMAIL_TOKEN_FILE, 'r') as token:
            creds = Credentials.from_authorized_user_info(
                json.load(token), GMAIL_API_SCOPES
            )
    
    # If credentials exist but are invalid or expired, refresh them
    if creds and creds.expired and creds.refresh_token:
        print("Refreshing expired credentials...")
        creds.refresh(Request())
        with open(GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print("Credentials refreshed successfully.")
        return True
    
    # If no valid credentials, run the authorization flow
    if not creds or not creds.valid:
        print("No valid credentials found. Starting authorization flow...")
        flow = InstalledAppFlow.from_client_secrets_file(
            GMAIL_CREDENTIALS_FILE, GMAIL_API_SCOPES
        )
        creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        print(f"Authorization successful! Token saved to {GMAIL_TOKEN_FILE}")
        return True
    
    print("Credentials are valid.")
    return True

def display_config_summary():
    """Display a summary of the current configuration."""
    print("\nConfiguration Summary:")
    print("======================")
    print(f"Gmail Credentials File: {GMAIL_CREDENTIALS_FILE}")
    print(f"Gmail Token File: {GMAIL_TOKEN_FILE}")
    print(f"Telegram Bot Token: {'Configured' if TELEGRAM_BOT_TOKEN else 'Not Configured'}")
    print(f"Telegram Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"Monitored Email Senders: {', '.join(EMAIL_SENDERS)}")
    print("\nSetup complete! You can now run the application with:")
    print("python openai_code_forwarder.py")

def main():
    """Main setup function."""
    print("OpenAI Code Forwarder - Setup")
    print("=============================")
    
    # Validate configuration
    validate_config()
    
    # Authenticate with Gmail
    authenticate_gmail()
    
    # Display summary
    display_config_summary()

if __name__ == "__main__":
    main() 