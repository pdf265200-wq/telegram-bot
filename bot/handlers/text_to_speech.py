"""
Text to Speech command handler
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from bot.services.speech_service import SpeechService
from bot.middleware.anti_spam import AntiSpamMiddleware
from bot.database.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)
speech_service = SpeechService()
anti_spam = AntiSpamMiddleware()
db = DatabaseManager()

async def text_to_speech_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /t2s command"""
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data='t2s_lang_en'),
            InlineKeyboardButton("🇸🇦 Arabic", callback_data='t2s_lang_ar')
        ],
        [
            InlineKeyboardButton("🐢 Slow Speed", callback_data='t2s_slow'),
            InlineKeyboardButton("🐇 Normal Speed", callback_data='t2s_normal')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔊 *Text to Speech*\n\n"
        "Send me any text and I'll convert it to speech.\n\n"
        "You can also:\n"
        "• Select language\n"
        "• Adjust speech speed\n\n"
        "Example: `/t2s Hello World` or send text directly",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def t2s_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle TTS option callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('t2s_lang_'):
        lang = query.data.replace('t2s_lang_', '')
        context.user_data['tts_lang'] = lang
        lang_name = 'Arabic' if lang == 'ar' else 'English'
        await query.edit_message_text(f"✅ Language set to: *{lang_name}*", parse_mode='Markdown')
    
    elif query.data in ['t2s_slow', 't2s_normal']:
        slow = query.data == 't2s_slow'
        context.user_data['tts_slow'] = slow
        speed = 'Slow' if slow else 'Normal'
        await query.edit_message_text(f"✅ Speed set to: *{speed}*", parse_mode='Markdown')

async def text_to_speech_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /t2s command with text"""
    user_id = update.effective_user.id
    
    # Check anti-spam
    allowed, message = await anti_spam.check_user(user_id)
    if not allowed:
        await update.message.reply_text(message)
        return
    
    # Get text from command arguments
    if context.args:
        text = ' '.join(context.args)
    else:
        await update.message.reply_text(
            "❌ Please provide text to convert.\n"
            "Example: `/t2s Hello World`",
            parse_mode='Markdown'
        )
        return
    
    await process_text_to_speech(update, context, text)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages for TTS"""
    user_id = update.effective_user.id
    
    # Only process if text message and not a command
    if update.message.text and not update.message.text.startswith('/'):
        # Check if user wants TTS conversion
        if context.user_data.get('auto_tts', False):
            await process_text_to_speech(update, context, update.message.text)

async def process_text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process text and convert to speech"""
    user_id = update.effective_user.id
    
    # Send processing message
    processing_msg = await update.message.reply_text("🔊 Converting text to speech...")
    
    try:
        # Get user preferences
        language = context.user_data.get('tts_lang', 'en')
        slow = context.user_data.get('tts_slow', False)
        
        # Convert to speech
        audio_buffer, error = await speech_service.text_to_speech(text, language, slow)
        
        if error:
            await processing_msg.edit_text(f"❌ Error: {error}")
            return
        
        # Send audio file
        await update.message.reply_voice(
            voice=audio_buffer,
            caption=f"🔊 *Text to Speech*\nLanguage: {'Arabic' if language == 'ar' else 'English'}",
            parse_mode='Markdown'
        )
        
        # Log usage
        db.log_usage(user_id, 'text_to_speech')
        
        # Delete processing message
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Text to speech error: {e}")
        await processing_msg.edit_text(f"❌ An error occurred: {str(e)}")

async def toggle_auto_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle automatic TTS conversion for text messages"""
    auto_tts = context.user_data.get('auto_tts', False)
    context.user_data['auto_tts'] = not auto_tts
    status = 'enabled' if not auto_tts else 'disabled'
    
    await update.message.reply_text(
        f"🔄 Automatic text-to-speech is now *{status}*.\n"
        f"{'All text messages will be converted to speech.' if not auto_tts else 'Use /t2s command to convert text.'}",
        parse_mode='Markdown'
    )

# Handler setup
text_to_speech_handlers = [
    CommandHandler('t2s', text_to_speech_command),
    CommandHandler('t2s_options', text_to_speech_start),
    CommandHandler('auto_tts', toggle_auto_tts),
    CallbackQueryHandler(t2s_callback, pattern='^t2s_'),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message),
]
