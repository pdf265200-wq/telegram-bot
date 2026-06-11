"""
QR Code generation handler
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from bot.services.qr_service import QRService
from bot.middleware.anti_spam import AntiSpamMiddleware
from bot.database.db_manager import DatabaseManager
import logging
import io

logger = logging.getLogger(__name__)
qr_service = QRService()
anti_spam = AntiSpamMiddleware()
db = DatabaseManager()

async def qr_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /qr command"""
    user_id = update.effective_user.id
    
    # Check anti-spam
    allowed, message = await anti_spam.check_user(user_id)
    if not allowed:
        await update.message.reply_text(message)
        return
    
    if not context.args:
        await update.message.reply_text(
            "📱 *QR Code Generator*\n\n"
            "Send me any text or URL to generate a QR code.\n\n"
            "Usage:\n"
            "• `/qr your_text_or_url`\n"
            "• Or simply send a URL and I'll generate a QR code\n\n"
            "Examples:\n"
            "• `/qr https://example.com`\n"
            "• `/qr Hello World`",
            parse_mode='Markdown'
        )
        return
    
    # Get text from command arguments
    text = ' '.join(context.args)
    await generate_qr_code(update, context, text)

async def handle_url_for_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URL messages for QR code generation"""
    user_id = update.effective_user.id
    
    # Check if message contains URL
    if update.message.text and ('http://' in update.message.text or 'https://' in update.message.text):
        # Check if user wants auto QR generation
        if context.user_data.get('auto_qr', False):
            await generate_qr_code(update, context, update.message.text)

async def generate_qr_code(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Generate and send QR code"""
    user_id = update.effective_user.id
    
    processing_msg = await update.message.reply_text("📱 Generating QR code...")
    
    try:
        # Generate QR code
        qr_image, error = qr_service.generate_qr(text)
        
        if error:
            await processing_msg.edit_text(f"❌ Error: {error}")
            return
        
        # Create BytesIO object
        qr_bytes = io.BytesIO(qr_image)
        qr_bytes.name = 'qrcode.png'
        
        # Send QR code
        await update.message.reply_photo(
            photo=qr_bytes,
            caption=f"📱 *QR Code*\nContent: `{text[:100]}`",
            parse_mode='Markdown'
        )
        
        # Log usage
        db.log_usage(user_id, 'qr_code')
        
        # Delete processing message
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"QR code generation error: {e}")
        await processing_msg.edit_text(f"❌ An error occurred: {str(e)}")

async def toggle_auto_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle automatic QR code generation for URLs"""
    auto_qr = context.user_data.get('auto_qr', False)
    context.user_data['auto_qr'] = not auto_qr
    status = 'enabled' if not auto_qr else 'disabled'
    
    await update.message.reply_text(
        f"🔄 Automatic QR code generation is now *{status}*.\n"
        f"{'URLs will automatically generate QR codes.' if not auto_qr else 'Use /qr command to generate QR codes.'}",
        parse_mode='Markdown'
    )

# Handler setup
qr_code_handlers = [
    CommandHandler('qr', qr_code_command),
    CommandHandler('auto_qr', toggle_auto_qr),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_for_qr),
]
