from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from bot.services.speech_service import SpeechService
from bot.middleware.anti_spam import AntiSpamMiddleware
from bot.database.db_manager import DatabaseManager
import os
import tempfile
import logging

logger = logging.getLogger(__name__)
speech_service = SpeechService()
anti_spam = AntiSpamMiddleware()
db = DatabaseManager()

async def voice_to_text_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /v2t command"""
    await update.message.reply_text(
        "🎤 *Voice to Text*\n\n"
        "Send me a voice message or audio file (.ogg, .mp3, .wav, .m4a)\n"
        "I'll convert it to text automatically.\n\n"
        "Supported languages: Arabic and English\n\n"
        "Use /v2t_lang [ar/en] to specify language\n"
        "Example: `/v2t_lang ar`",
        parse_mode='Markdown'
    )

async def voice_to_text_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set language preference for voice recognition"""
    if not context.args:
        await update.message.reply_text("Please specify language: /v2t_lang ar or /v2t_lang en")
        return
    
    lang = context.args[0].lower()
    if lang in ['ar', 'en']:
        context.user_data['v2t_lang'] = lang
        await update.message.reply_text(f"✅ Language set to: {'Arabic' if lang == 'ar' else 'English'}")
    else:
        await update.message.reply_text("❌ Invalid language. Use 'ar' for Arabic or 'en' for English")

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice/audio messages"""
    user_id = update.effective_user.id
    
    # Check anti-spam
    allowed, message = await anti_spam.check_user(user_id)
    if not allowed:
        await update.message.reply_text(message)
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text("🎯 Processing your audio... Please wait.")
    
    try:
        # Download the file
        if update.message.voice:
            file = await update.message.voice.get_file()
        elif update.message.audio:
            file = await update.message.audio.get_file()
        else:
            await processing_msg.edit_text("❌ Unsupported audio format")
            return
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp_file:
            await file.download_to_drive(tmp_file.name)
            tmp_path = tmp_file.name
        
        # Get language preference
        language = context.user_data.get('v2t_lang', None)
        
        # Convert to text
        text, lang = await speech_service.voice_to_text(tmp_path, language)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if text:
            # Log usage
            db.log_usage(user_id, 'voice_to_text')
            
            await processing_msg.edit_text(
                f"✅ *Transcription Complete* ({'Arabic' if lang == 'ar' else 'English'}):\n\n"
                f"{text}",
                parse_mode='Markdown'
            )
        else:
            await processing_msg.edit_text(
                f"❌ *Error:* {lang if isinstance(lang, str) else 'Could not process audio'}\n"
                "Please try again with clearer audio.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Voice message handling error: {e}")
        await processing_msg.edit_text(f"❌ An error occurred: {str(e)}")

# Handler setup
voice_to_text_handlers = [
    CommandHandler('v2t', voice_to_text_start),
    CommandHandler('v2t_lang', voice_to_text_lang),
    MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_message),
]
