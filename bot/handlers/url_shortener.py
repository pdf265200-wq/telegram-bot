"""
URL Shortener handler
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from bot.services.url_service import URLService
from bot.middleware.anti_spam import AntiSpamMiddleware
from bot.database.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)
url_service = URLService()
anti_spam = AntiSpamMiddleware()
db = DatabaseManager()

async def url_shortener_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /url command"""
    user_id = update.effective_user.id
    
    # Check anti-spam
    allowed, message = await anti_spam.check_user(user_id)
    if not allowed:
        await update.message.reply_text(message)
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔗 *URL Shortener*\n\n"
            "Send me a long URL to shorten it.\n\n"
            "Usage:\n"
            "• `/url https://example.com/very/long/url`\n"
            "• Or simply send a URL\n\n"
            "Available services: TinyURL, is.gd, Da.gd",
            parse_mode='Markdown'
        )
        return
    
    url = context.args[0]
    await shorten_url(update, context, url)

async def handle_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URL messages for shortening"""
    if update.message and update.message.text:
        text = update.message.text
        # Check if message contains URL
        if url_service.is_valid_url(text):
            await shorten_url(update, context, text)

async def shorten_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Shorten URL and send result"""
    user_id = update.effective_user.id
    
    processing_msg = await update.message.reply_text("🔗 Shortening URL...")
    
    try:
        # Try different services
        short_url, error = url_service.shorten_url(url, 'tinyurl')
        
        if error:
            # Try alternative service
            short_url, error = url_service.shorten_url(url, 'isgd')
        
        if error:
            short_url, error = url_service.shorten_url(url, 'dagd')
        
        if short_url:
            # Log usage
            db.log_usage(user_id, 'url_shortener')
            
            await processing_msg.edit_text(
                f"🔗 *URL Shortened!*\n\n"
                f"*Original:* `{url}`\n"
                f"*Short:* `{short_url}`\n\n"
                f"Click to copy and share!",
                parse_mode='Markdown'
            )
        else:
            await processing_msg.edit_text(
                f"❌ Failed to shorten URL: {error}\n"
                "Please try again later."
            )
            
    except Exception as e:
        logger.error(f"URL shortening error: {e}")
        await processing_msg.edit_text(f"❌ An error occurred: {str(e)}")

# Handler setup
url_shortener_handlers = [
    CommandHandler('url', url_shortener_command),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_message),
]
