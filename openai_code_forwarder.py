#!/usr/bin/env python3
"""
OpenAI Code Forwarder - Monitors Gmail for OpenAI login codes and forwards them to Telegram.
"""

# Import telegram compatibility module first
import telegram_compat

import re
import base64
import time
import json
import os
from datetime import datetime
import logging
from typing import Optional, List
import asyncio

from telegram import Bot
from telegram.constants import ParseMode
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Import configuration
from config import (
    GMAIL_CREDENTIALS_FILE, 
    GMAIL_TOKEN_FILE, 
    TELEGRAM_BOT_TOKEN, 
    TELEGRAM_CHAT_ID,
    EMAIL_CHECK_INTERVAL,
    EMAIL_SENDERS,
    GMAIL_API_SCOPES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class GmailClient:
    """Handles Gmail API operations."""
    
    def __init__(self, credentials_file: str, token_file: str):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as token:
                creds = Credentials.from_authorized_user_info(
                    json.load(token), GMAIL_API_SCOPES
                )
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, GMAIL_API_SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    
    def list_messages(self, query: str, max_results: int = 10) -> List[dict]:
        """List messages matching the specified query."""
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId='me', q=query, maxResults=max_results)
                .execute()
            )
            messages = results.get('messages', [])
            return messages
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            return []
    
    def get_message(self, msg_id: str) -> Optional[dict]:
        """Get a specific message by ID."""
        try:
            return (
                self.service.users()
                .messages()
                .get(userId='me', id=msg_id, format='full')
                .execute()
            )
        except Exception as e:
            logger.error(f"Error getting message {msg_id}: {e}")
            return None


class TelegramClient:
    """Handles Telegram message sending."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)
    
    async def send_message_async(self, text: str) -> bool:
        """Send a message to the specified chat asynchronously."""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id, 
                text=text,
                parse_mode=ParseMode.HTML
            )
            return True
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False
            
    def send_message(self, text: str) -> bool:
        """Send a message to the specified chat (synchronous wrapper)."""
        try:
            # Run the async function in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message_async(text))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False


class OpenAICodeExtractor:
    """Extracts OpenAI verification codes from email messages."""
    
    @staticmethod
    def decode_email_body(payload: dict) -> str:
        """Decode the email body from base64."""
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(
                payload['body']['data'].encode('ASCII')
            ).decode('utf-8')
        
        # Check for multipart message
        if 'parts' in payload:
            for part in payload['parts']:
                body = OpenAICodeExtractor.decode_email_body(part)
                if body:
                    return body
        
        return ""
    
    @staticmethod
    def extract_verification_code(text: str) -> Optional[str]:
        """Extract a 6-digit verification code from text."""
        # Look for patterns like "Your code is: 123456" or just "123456"
        patterns = [
            r'code is:?\s*(\d{6})',        # "Your code is: 123456"
            r'verification code:?\s*(\d{6})',  # "verification code: 123456"
            r'code:?\s*(\d{6})',           # "Code: 123456"
            r'[\s:](\d{6})[\s\.]',         # " 123456 " or ": 123456."
            r'<strong>(\d{6})<\/strong>'   # HTML: <strong>123456</strong>
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def get_sender(message: dict) -> Optional[str]:
        """Extract the sender email from a message."""
        headers = message['payload']['headers']
        for header in headers:
            if header['name'].lower() == 'from':
                # Extract just the email address
                from_value = header['value']
                match = re.search(r'<(.+@.+\..+)>', from_value)
                if match:
                    return match.group(1).lower()
                return from_value.lower()
        return None
    
    @staticmethod
    def get_subject(message: dict) -> Optional[str]:
        """Extract the subject from a message."""
        headers = message['payload']['headers']
        for header in headers:
            if header['name'].lower() == 'subject':
                return header['value']
        return None
    
    @staticmethod
    def get_received_time(message: dict) -> datetime:
        """Extract the received time from a message."""
        # Convert internal date (Unix timestamp in ms) to datetime
        internal_date = int(message.get('internalDate', 0)) / 1000
        return datetime.fromtimestamp(internal_date)


class CodeForwarder:
    """Main class that handles the email monitoring and code forwarding."""
    
    def __init__(
        self, 
        gmail_credentials_file: str,
        gmail_token_file: str,
        telegram_bot_token: str,
        telegram_chat_id: str,
        email_senders: List[str],
        check_interval: int = 60
    ):
        self.gmail = GmailClient(gmail_credentials_file, gmail_token_file)
        self.telegram = TelegramClient(telegram_bot_token, telegram_chat_id)
        self.email_senders = email_senders
        self.check_interval = check_interval
        self.processed_codes = set()  # Track already processed codes
        
    def build_email_query(self) -> str:
        """Build the Gmail search query."""
        # Combine all email senders with OR
        sender_query = " OR ".join([f"from:{sender}" for sender in self.email_senders])
        # Filter for recent emails (last 24 hours)
        return f"({sender_query}) newer_than:1d"
    
    def process_new_emails(self) -> None:
        """Check for new OpenAI verification code emails and forward them."""
        query = self.build_email_query()
        messages = self.gmail.list_messages(query)
        
        if not messages:
            logger.info("No new OpenAI emails found")
            return
        
        # Process messages from newest to oldest
        messages.reverse()
        
        for msg_data in messages:
            message = self.gmail.get_message(msg_data['id'])
            if not message:
                continue
            
            sender = OpenAICodeExtractor.get_sender(message)
            if not sender or not any(s in sender for s in self.email_senders):
                continue
            
            subject = OpenAICodeExtractor.get_subject(message)
            received_time = OpenAICodeExtractor.get_received_time(message)
            body = OpenAICodeExtractor.decode_email_body(message['payload'])
            verification_code = OpenAICodeExtractor.extract_verification_code(body)
            
            if verification_code and verification_code not in self.processed_codes:
                logger.info(f"Found new verification code: {verification_code}")
                
                # Format the message for Telegram
                time_str = received_time.strftime("%Y-%m-%d %H:%M:%S")
                telegram_msg = (
                    f"📬 <b>OpenAI Verification Code</b>\n\n"
                    f"🔑 <code>{verification_code}</code>\n\n"
                    f"📨 From: {sender}\n"
                    f"📅 Time: {time_str}"
                )
                
                # Send to Telegram
                success = self.telegram.send_message(telegram_msg)
                if success:
                    logger.info(f"Sent code {verification_code} to Telegram")
                    self.processed_codes.add(verification_code)
                    
                    # Limit the size of processed_codes to avoid memory issues
                    if len(self.processed_codes) > 100:
                        # Keep only the most recent 50 codes
                        self.processed_codes = set(list(self.processed_codes)[-50:])
    
    def run(self) -> None:
        """Run the forwarder in a loop."""
        logger.info(
            f"Starting OpenAI code forwarder. "
            f"Checking for emails from {', '.join(self.email_senders)} "
            f"every {self.check_interval} seconds."
        )
        
        while True:
            try:
                self.process_new_emails()
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
            
            time.sleep(self.check_interval)


def main():
    """Main entry point."""
    # Validate required configuration
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
        
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        exit(1)
    
    # Check if credentials file exists
    if not os.path.exists(GMAIL_CREDENTIALS_FILE):
        logger.error(
            f"Gmail credentials file not found: {GMAIL_CREDENTIALS_FILE}\n"
            f"Please follow the setup instructions in the README."
        )
        exit(1)
    
    # Create and run the forwarder
    forwarder = CodeForwarder(
        gmail_credentials_file=GMAIL_CREDENTIALS_FILE,
        gmail_token_file=GMAIL_TOKEN_FILE,
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID,
        email_senders=EMAIL_SENDERS,
        check_interval=EMAIL_CHECK_INTERVAL
    )
    
    forwarder.run()


if __name__ == "__main__":
    main() 