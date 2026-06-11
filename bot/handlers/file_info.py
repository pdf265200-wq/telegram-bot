"""
File information handler
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from bot.middleware.anti_spam import AntiSpamMiddleware
from bot.database.db_manager import DatabaseManager
from bot.utils.helpers import format_file_size, get_file_extension, get_mime_type
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
anti_spam = AntiSpamMiddleware()
db = DatabaseManager()

async def file_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fileinfo command"""
    await update.message.reply_text(
        "📄 *File Information*\n\n"
        "Send me any file (document, image, video, audio) and I'll tell you:\n"
        "• File name\n"
        "• File size\n"
        "• File type\n"
        "• Extension\n"
        "• MIME type\n\n"
        "Just send or forward any file!",
        parse_mode='Markdown'
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file messages for info"""
    user_id = update.effective_user.id
    
    # Check anti-spam
    allowed, message = await anti_spam.check_user(user_id)
    if not allowed:
        await update.message.reply_text(message)
        return
    
    message = update.message
    
    # Determine file type and get file object
    file_obj = None
    file_type = "Unknown"
    
    if message.document:
        file_obj = message.document
        file_type = "Document"
    elif message.photo:
        file_obj = message.photo[-1]  # Get highest resolution
        file_type = "Photo"
    elif message.video:
        file_obj = message.video
        file_type = "Video"
    elif message.audio:
        file_obj = message.audio
        file_type = "Audio"
    elif message.voice:
        file_obj = message.voice
        file_type = "Voice Message"
    elif message.video_note:
        file_obj = message.video_note
        file_type = "Video Note"
    elif message.sticker:
        file_obj = message.sticker
        file_type = "Sticker"
    else:
        await update.message.reply_text("❌ Unsupported file type.")
        return
    
    if file_obj:
        await process_file_info(update, context, file_obj, file_type, message.caption)

async def process_file_info(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           file_obj, file_type: str, caption: str = None):
    """Process and display file information"""
    user_id = update.effective_user.id
    
    try:
        # Get file details
        file_name = getattr(file_obj, 'file_name', None)
        file_size = getattr(file_obj, 'file_size', 0)
        file_id = getattr(file_obj, 'file_id', None)
        mime_type = getattr(file_obj, 'mime_type', None)
        
        # Get file extension
        extension = get_file_extension(file_name) if file_name else "N/A"
        
        # Get additional info based on type
        extra_info = ""
        
        if hasattr(file_obj, 'width') and hasattr(file_obj, 'height'):
            extra_info += f"📐 *Dimensions:* {file_obj.width}x{file_obj.height}px\n"
        
        if hasattr(file_obj, 'duration'):
            extra_info += f"⏱ *Duration:* {file_obj.duration} seconds\n"
        
        # Format file info message
        info_text = f"""
📄 *File Information*

📁 *Type:* {file_type}
📝 *Name:* `{file_name or 'N/A'}`
📏 *Size:* {format_file_size(file_size)}
🔤 *Extension:* `{extension}`
🎯 *MIME Type:* `{mime_type or 'N/A'}`
🆔 *File ID:* `{file_id}`
{extra_info}
"""
        
        if caption:
            info_text += f"\n💬 *Caption:* {caption}"
        
        # Log usage
        db.log_usage(user_id, 'file_info')
        
        await update.message.reply_text(
            info_text,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"File info processing error: {e}")
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")

# Handler setup
file_info_handlers = [
    CommandHandler('fileinfo', file_info_command),
    MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VIDEO | 
        filters.AUDIO | filters.VOICE | filters.VIDEO_NOTE,
        handle_file
    ),
]
