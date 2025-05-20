"""
This file contains the fixed get_latest_verification_code method for the Gmail-Telegram Bot.
It includes a fix to prevent processing the same email multiple times.
"""

import logging
from typing import Optional, Dict, Any
import re

logger = logging.getLogger(__name__)

def get_latest_verification_code(self, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the latest OpenAI verification code from Gmail.
    
    This version includes protection against processing the same email multiple times.
    """
    global last_processed_email_id
    
    try:
        # Check if credentials exist for this user
        if not self.gmail:
            logger.error("Gmail client not initialized")
            return None
        
        # Build query for emails in the last day
        query = f"from:({' OR '.join(OPENAI_EMAIL_SENDERS)}) AND subject:verification"
        # Add time constraint
        query += " newer_than:1d"
        
        # Get message list
        messages = self.gmail.list_messages(query, max_results=5)
        if not messages:
            logger.info("No verification emails found")
            return None
        
        # Process messages from newest to oldest
        messages.reverse()
        
        for msg in messages:
            msg_id = msg['id']
            
            # Check if this email has already been processed
            if msg_id == last_processed_email_id:
                logger.info(f"This email has already been processed: {msg_id}")
                continue
                
            # Get the full message
            message = self.gmail.get_message(msg_id)
            if not message:
                logger.error(f"Failed to get message {msg_id}")
                continue
            
            # Get message details
            headers = message['payload']['headers']
            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), None)
            
            if not subject or 'verification' not in subject.lower():
                logger.debug(f"Skipping email, subject doesn't match: {subject}")
                continue
            
            # Get message body
            body = self._get_message_body(message)
            if not body:
                logger.error(f"Failed to extract body from message {msg_id}")
                continue
            
            # Extract verification code
            verification_code = self._extract_verification_code(body)
            if not verification_code:
                logger.debug(f"No verification code found in message {msg_id}")
                continue
            
            # Store the message ID to avoid processing it again
            last_processed_email_id = msg_id
            
            logger.info(f"Found verification code: {verification_code}")
            return {"code": verification_code}
        
        logger.info("No new verification code found in recent emails")
        return None
        
    except Exception as e:
        logger.error(f"Error getting verification code: {e}")
        # Check for rate limit errors
        if "Rate Limit Exceeded" in str(e) or "quota" in str(e).lower():
            return {"error": "rate_limit"}
        return None
        
# Helper methods that would be part of the same class

def _get_message_body(self, message: Dict[str, Any]) -> Optional[str]:
    """Extract body from a message."""
    try:
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    # Decode base64 data
                    import base64
                    return base64.urlsafe_b64decode(part['body']['data']).decode()
                
                if part['mimeType'] == 'text/html' and 'data' in part['body']:
                    # Decode base64 data
                    import base64
                    return base64.urlsafe_b64decode(part['body']['data']).decode()
                    
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            # Single part message
            import base64
            return base64.urlsafe_b64decode(message['payload']['body']['data']).decode()
            
        return None
    except Exception as e:
        logger.error(f"Error extracting message body: {e}")
        return None

def _extract_verification_code(self, text: str) -> Optional[str]:
    """Extract 6-digit verification code from text."""
    patterns = [
        r'code[^0-9]*(\d{6})',  # Matches "code: 123456"
        r'verification code[^0-9]*(\d{6})',  # Matches "verification code: 123456"
        r'<strong>(\d{6})</strong>',  # Matches HTML <strong>123456</strong>
        r'code is [^0-9]*(\d{6})',  # Matches "code is 123456"
        r'[\s:](\d{6})[\s\.]'  # Matches " 123456 "
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # If no pattern matches, look for any 6 digit number
    match = re.search(r'(\d{6})', text)
    if match:
        return match.group(1)
        
    return None 