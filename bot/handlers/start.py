"""
Start command handler and main menu
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from bot.database.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)
db = DatabaseManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued"""
    user = update.effective_user
    
    # Register/update user in database
    db.get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = f"""
🌟 *مرحباً {user.first_name}! / Welcome {user.first_name}!*

أنا بوت متعدد الوظائف يمكنني مساعدتك في:
I'm a multifunctional bot that can help you with:

🎤 *تحويل الصوت إلى نص*
   Voice to Text - /v2t

🔊 *تحويل النص إلى صوت*
   Text to Speech - /t2s

📱 *إنشاء رمز QR*
   QR Code Generator - /qr

🔗 *تقصير الروابط*
   URL Shortener - /url

📄 *معلومات الملفات*
   File Information - /fileinfo

📸 *استخراج النص من الصور*
   Image to Text (OCR) - /ocr

📑 *أدوات PDF*
   PDF Tools - /pdf

📊 *الإحصائيات*
   Statistics - /stats

📋 *للمشرفين*
   Admin Panel - /admin

استخدم الأوامر أعلاه أو أرسل ملفاً للبدء!
Use the commands above or send a file to start!
    """
    
    keyboard = [
        [
            InlineKeyboardButton("🎤 Voice to Text", callback_data='menu_v2t'),
            InlineKeyboardButton("🔊 Text to Speech", callback_data='menu_t2s')
        ],
        [
            InlineKeyboardButton("📱 QR Code", callback_data='menu_qr'),
            InlineKeyboardButton("🔗 URL Shortener", callback_data='menu_url')
        ],
        [
            InlineKeyboardButton("📄 File Info", callback_data='menu_file'),
            InlineKeyboardButton("📸 OCR", callback_data='menu_ocr')
        ],
        [
            InlineKeyboardButton("📑 PDF Tools", callback_data='menu_pdf')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu button callbacks"""
    query = update.callback_query
    await query.answer()
    
    menu_responses = {
        'menu_v2t': "🎤 *Voice to Text*\n\nSend me a voice message or use /v2t for options.",
        'menu_t2s': "🔊 *Text to Speech*\n\nSend me text or use /t2s for options.",
        'menu_qr': "📱 *QR Code Generator*\n\nSend me text/URL or use /qr text",
        'menu_url': "🔗 *URL Shortener*\n\nSend me a URL or use /url your_link",
        'menu_file': "📄 *File Information*\n\nSend me any file to get its details.",
        'menu_ocr': "📸 *Image to Text (OCR)*\n\nSend me an image to extract text.",
        'menu_pdf': "📑 *PDF Tools*\n\nUse /pdf to see available options."
    }
    
    response = menu_responses.get(query.data, "Please select a valid option.")
    await query.edit_message_text(response, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's personal statistics"""
    user = update.effective_user
    user_data = db.get_or_create_user(user_id=user.id)
    
    stats_text = f"""
📊 *إحصائياتك / Your Statistics*

👤 *المستخدم / User:* {user.first_name}
🆔 *ID:* {user.id}
📅 *تاريخ التسجيل / Joined:* {user_data.created_at.strftime('%Y-%m-%d')}
🕐 *آخر نشاط / Last Active:* {user_data.last_activity.strftime('%Y-%m-%d %H:%M')}
📈 *إجمالي الطلبات / Total Requests:* {user_data.total_requests}
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# Define handlers
start_handler = CommandHandler('start', start)
stats_handler = CommandHandler('stats', stats)
menu_callback_handler = CallbackQueryHandler(menu_callback, pattern='^menu_')

start_handlers = [start_handler, stats_handler, menu_callback_handler]
