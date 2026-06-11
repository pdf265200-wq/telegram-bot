"""
OCR (Optical Character Recognition) handler
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from bot.services.ocr_service import OCRService
from bot.middleware.anti_spam import AntiSpamMiddleware
from bot.database.db_manager import DatabaseManager
import os
import tempfile
import logging

logger = logging.getLogger(__name__)
ocr_service = OCRService()
anti_spam = AntiSpamMiddleware()
db = DatabaseManager()

async def ocr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ocr command"""
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data='ocr_lang_en'),
            InlineKeyboardButton("🇸🇦 Arabic", callback_data='ocr_lang_ar'),
            InlineKeyboardButton("🌍 Both", callback_data='ocr_lang_both')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📸 *Image to Text (OCR)*\n\n"
        "Send me an image and I'll extract text from it.\n\n"
        "• Supports Arabic and English text\n"
        "• Works with photos and documents\n"
        "• Select language for better results\n\n"
        "Just send or forward any image!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ocr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OCR language selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('ocr_lang_'):
        lang = query.data.replace('ocr_lang_', '')
        lang_map = {
            'en': 'English',
            'ar': 'Arabic',
            'both': 'Arabic + English'
        }
        context.user_data['ocr_lang'] = lang
        await query.edit_message_text(
            f"✅ OCR Language set to: *{lang_map.get(lang, 'Both')}*",
            parse_mode='Markdown'
        )

async def handle_image_for_ocr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image messages for OCR"""
    user_id = update.effective_user.id
    
    # Check anti-spam
    allowed, message = await anti_spam.check_user(user_id)
    if not allowed:
        await update.message.reply_text(message)
        return
    
    processing_msg = await update.message.reply_text("📸 Extracting text from image...")
    
    try:
        # Get the image file
        if update.message.photo:
            # Get the highest resolution photo
            file = await update.message.photo[-1].get_file()
        elif update.message.document:
            file = await update.message.document.get_file()
        else:
            await processing_msg.edit_text("❌ Please send an image file.")
            return
        
        # Download file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            await file.download_to_drive(tmp_file.name)
            tmp_path = tmp_file.name
        
        # Get language preference
        lang = context.user_data.get('ocr_lang', 'both')
        lang_code = 'en+ar' if lang == 'both' else 'en' if lang == 'en' else 'ar'
        
        # Extract text
        text, error = await ocr_service.extract_text(tmp_path, lang_code)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if error:
            await processing_msg.edit_text(f"❌ Error: {error}")
            return
        
        if not text.strip():
            await processing_msg.edit_text("❌ No text found in the image.")
            return
        
        # Log usage
        db.log_usage(user_id, 'ocr')
        
        # Send extracted text
        if len(text) > 4096:
            # Split long text into multiple messages
            for i in range(0, len(text), 4096):
                chunk = text[i:i+4096]
                if i == 0:
                    await processing_msg.edit_text(
                        f"📝 *Extracted Text:*\n\n{chunk}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        f"📝 *Continued...*\n\n{chunk}",
                        parse_mode='Markdown'
                    )
        else:
            await processing_msg.edit_text(
                f"📝 *Extracted Text:*\n\n{text}",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        await processing_msg.edit_text(f"❌ An error occurred: {str(e)}")

# Handler setup
ocr_handlers = [
    CommandHandler('ocr', ocr_command),
    CallbackQueryHandler(ocr_callback, pattern='^ocr_lang_'),
    MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image_for_ocr),
]
