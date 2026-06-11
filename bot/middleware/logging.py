"""
Logging middleware for tracking user activities
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class LoggingMiddleware:
    """Middleware for logging all bot activities"""
    
    def __init__(self):
        self.logger = logging.getLogger('bot.activities')
        self.setup_activity_logger()
    
    def setup_activity_logger(self):
        """Setup separate logger for activities"""
        handler = logging.FileHandler('logs/activities.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def log_message(self, update: Update):
        """Log incoming message"""
        user = update.effective_user
        message_text = None
        
        if update.message:
            message_text = update.message.text or update.message.caption
        elif update.callback_query:
            message_text = update.callback_query.data
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'chat_id': update.effective_chat.id if update.effective_chat else None,
            'message_type': type(update.message).__name__ if update.message else 'callback',
            'message_text': message_text[:100] if message_text else None
        }
        
        self.logger.info(f"User Activity: {log_data}")
    
    async def log_command(self, update: Update, command: str, success: bool = True):
        """Log command execution"""
        user = update.effective_user
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user.id,
            'command': command,
            'success': success
        }
        
        self.logger.info(f"Command Execution: {log_data}")
    
    async def log_error(self, update: Update, error: Exception):
        """Log errors"""
        user = update.effective_user if update else None
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user.id if user else 'Unknown',
            'error_type': type(error).__name__,
            'error_message': str(error)
        }
        
        self.logger.error(f"Bot Error: {log_data}")
