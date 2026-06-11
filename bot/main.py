"""
Main bot application file
"""

import asyncio
import logging
import sys
import os
import signal
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    Defaults
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, NetworkError, TimedOut

from bot.config import Config
from bot.database.db_manager import DatabaseManager
from bot.database.models import init_db
from bot.middleware.anti_spam import AntiSpamMiddleware
from bot.middleware.logging import LoggingMiddleware
from bot.middleware.rate_limiter import RateLimiter
from bot.utils.helpers import create_directories, cleanup_temp_files

# Import handlers
from bot.handlers import (
    start,
    voice_to_text,
    text_to_speech,
    qr_code,
    url_shortener,
    file_info,
    ocr,
    pdf_tools,
    admin
)

# Configure logging
create_directories()
logging.basicConfig(
    format=Config.LOG_FORMAT,
    level=getattr(logging, Config.LOG_LEVEL),
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize components
db = DatabaseManager()
anti_spam = AntiSpamMiddleware()
logging_middleware = LoggingMiddleware()

class Bot:
    """Main bot application class"""
    
    def __init__(self):
        self.application = None
        self.is_running = False
        
    async def setup(self) -> Application:
        """Setup bot application"""
        logger.info(f"Setting up {Config.BOT_NAME} v{Config.BOT_VERSION}")
        
        # Validate configuration
        if not Config.validate():
            logger.error("Invalid configuration. Exiting.")
            sys.exit(1)
        
        # Create application with defaults
        defaults = Defaults(
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            block=False
        )
        
        self.application = (
            Application.builder()
            .token(Config.BOT_TOKEN)
            .defaults(defaults)
            .concurrent_updates(True)
            .build()
        )
        
        # Register error handler
        self.application.add_error_handler(self.error_handler)
        
        # Register all handlers
        self.register_handlers()
        
        # Setup job queue for periodic tasks
        self.setup_jobs()
        
        logger.info("Bot setup completed")
        return self.application
    
    def register_handlers(self):
        """Register all command and message handlers"""
        logger.info("Registering handlers...")
        
        # Start handlers
        for handler in start.start_handlers:
            self.application.add_handler(handler)
        
        # Voice to text handlers
        for handler in voice_to_text.voice_to_text_handlers:
            self.application.add_handler(handler)
        
        # Text to speech handlers
        for handler in text_to_speech.text_to_speech_handlers:
            self.application.add_handler(handler)
        
        # QR Code handlers
        for handler in qr_code.qr_code_handlers:
            self.application.add_handler(handler)
        
        # URL Shortener handlers
        for handler in url_shortener.url_shortener_handlers:
            self.application.add_handler(handler)
        
        # File info handlers
        for handler in file_info.file_info_handlers:
            self.application.add_handler(handler)
        
        # OCR handlers
        for handler in ocr.ocr_handlers:
            self.application.add_handler(handler)
        
        # PDF tools handlers
        for handler in pdf_tools.pdf_tools_handlers:
            self.application.add_handler(handler)
        
        # Admin handlers
        for handler in admin.admin_handlers:
            self.application.add_handler(handler)
        
        # Maintenance mode handler (should be first to intercept all messages)
        self.application.add_handler(
            MessageHandler(filters.ALL, self.maintenance_check), group=-1
        )
        
        logger.info("All handlers registered")
    
    def setup_jobs(self):
        """Setup periodic jobs"""
        job_queue = self.application.job_queue
        
        if job_queue:
            # Clean temp files every hour
            job_queue.run_repeating(
                self.cleanup_job,
                interval=3600,
                first=10
            )
            
            # Backup database every 6 hours
            job_queue.run_repeating(
                self.backup_database_job,
                interval=21600,
                first=60
            )
            
            # Update statistics every 30 minutes
            job_queue.run_repeating(
                self.update_stats_job,
                interval=1800,
                first=30
            )
    
    async def maintenance_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check if bot is in maintenance mode"""
        if Config.MAINTENANCE_MODE and not Config.is_admin(update.effective_user.id):
            await update.message.reply_text(
                "🔧 *Bot Under Maintenance*\n\n"
                "The bot is currently undergoing maintenance.\n"
                "Please try again later.\n\n"
                "_We apologize for the inconvenience._"
            )
            return
        
        # Log activity
        await logging_middleware.log_message(update)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot"""
        try:
            # Log the error
            logger.error(
                f"Update {update.update_id if update else 'N/A'} "
                f"caused error: {context.error}",
                exc_info=context.error
            )
            
            # Log to file
            await logging_middleware.log_error(update, context.error)
            
            # Handle specific errors
            if isinstance(context.error, NetworkError):
                logger.warning("Network error occurred. Bot will retry automatically.")
                return
            
            if isinstance(context.error, TimedOut):
                logger.warning("Request timed out. This might be temporary.")
                return
            
            # Notify admin about critical errors
            if not isinstance(context.error, (NetworkError, TimedOut)):
                try:
                    error_message = (
                        f"⚠️ *Bot Error*\n\n"
                        f"*Error:* `{type(context.error).__name__}`\n"
                        f"*Message:* `{str(context.error)[:200]}`\n"
                        f"*Update ID:* `{update.update_id if update else 'N/A'}`"
                    )
                    
                    for admin_id in Config.ADMIN_IDS:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=error_message
                        )
                except Exception as e:
                    logger.error(f"Failed to notify admin: {e}")
            
            # Inform user
            if update and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        "❌ *An error occurred*\n\n"
                        "The error has been logged and will be investigated.\n"
                        "Please try again later."
                    )
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    async def cleanup_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Periodic cleanup job"""
        try:
            cleanup_temp_files(Config.TEMP_DIR)
            logger.debug("Temporary files cleaned up")
        except Exception as e:
            logger.error(f"Cleanup job error: {e}")
    
    async def backup_database_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Database backup job"""
        try:
            import shutil
            from datetime import datetime
            
            source = Config.DATA_DIR / 'bot.db'
            if source.exists():
                backup_name = f"bot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_path = Config.DATA_DIR / 'backups' / backup_name
                backup_path.parent.mkdir(exist_ok=True)
                
                shutil.copy2(source, backup_path)
                logger.info(f"Database backed up to {backup_path}")
        except Exception as e:
            logger.error(f"Backup job error: {e}")
    
    async def update_stats_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Update statistics job"""
        try:
            # This could update cached statistics
            logger.debug("Statistics updated")
        except Exception as e:
            logger.error(f"Stats update job error: {e}")
    
    async def start(self):
        """Start the bot"""
        try:
            logger.info("Starting bot...")
            
            # Setup application
            await self.setup()
            
            # Start the bot
            if Config.WEBHOOK_URL:
                # Production mode with webhook
                await self.application.run_webhook(
                    listen=Config.WEBHOOK_LISTEN,
                    port=Config.WEBHOOK_PORT,
                    url_path=Config.BOT_TOKEN,
                    webhook_url=f"{Config.WEBHOOK_URL}/{Config.BOT_TOKEN}"
                )
                logger.info(f"Bot started with webhook on {Config.WEBHOOK_URL}")
            else:
                # Development mode with polling
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                logger.info("Bot started with polling")
            
            self.is_running = True
            
            # Keep the bot running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot gracefully"""
        if self.application and self.is_running:
            logger.info("Stopping bot...")
            
            try:
                if self.application.updater:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
            
            self.is_running = False
            logger.info("Bot stopped")

async def main():
    """Main entry point"""
    bot = Bot()
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}. Shutting down...")
        bot.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Failed to run bot: {e}")
        sys.exit(1)
