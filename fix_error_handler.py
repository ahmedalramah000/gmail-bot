"""
This file contains the error handler function for the Gmail-Telegram Bot.
It catches all exceptions that occur during message handling and logs them,
while also notifying the user about the error.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

# Error handler function
async def error_handler(update, context):
    """Log errors caused by updates and notify the user."""
    logger = logging.getLogger(__name__)
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Create detailed error log
    if update:
        if update.effective_message:
            logger.error(f"Message: {update.effective_message.text}")
        if update.effective_user:
            logger.error(f"User: {update.effective_user.id} - {update.effective_user.first_name}")
        if update.callback_query:
            logger.error(f"Callback query: {update.callback_query.data}")
    
    # Notify user
    if update and update.effective_chat:
        try:
            # Send a friendly message to the user
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى."
            )
        except Exception as e:
            logger.error(f"Error while sending error message: {e}")
            
    # Log traceback details
    if context.error:
        import traceback
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)
        logger.error(f"Traceback:\n{tb_string}")

# How to use:
"""
Add this to your main function:

# Add error handler
application.add_error_handler(error_handler)
""" 