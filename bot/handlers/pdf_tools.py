"""
PDF Tools handler
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from bot.services.pdf_service import PDFService
from bot.middleware.anti_spam import AntiSpamMiddleware
from bot.database.db_manager import DatabaseManager
from bot.utils.helpers import create_temp_file
import os
import tempfile
import logging

logger = logging.getLogger(__name__)
pdf_service = PDFService()
anti_spam = AntiSpamMiddleware()
db = DatabaseManager()

# Conversation states
WAITING_FOR_PDFS = 1
WAITING_FOR_IMAGES = 2

async def pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pdf command"""
    keyboard = [
        [
            InlineKeyboardButton("🖼 Images to PDF", callback_data='pdf_images_to_pdf'),
            InlineKeyboardButton("📑 Merge PDFs", callback_data='pdf_merge')
        ],
        [
            InlineKeyboardButton("📝 Extract Text", callback_data='pdf_extract_text'),
            InlineKeyboardButton("ℹ️ PDF Info", callback_data='pdf_info')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📑 *PDF Tools*\n\n"
        "Select an operation:\n\n"
        "• Images to PDF - Convert multiple images to PDF\n"
        "• Merge PDFs - Combine multiple PDFs\n"
        "• Extract Text - Get text from PDF\n"
        "• PDF Info - Get PDF details\n\n"
        "Or send PDF files directly for info.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def pdf_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF menu callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'pdf_images_to_pdf':
        context.user_data['pdf_action'] = 'images_to_pdf'
        await query.edit_message_text(
            "🖼 *Images to PDF*\n\n"
            "Send me 2 or more images to convert to PDF.\n"
            "Send /done when finished.\n"
            "Send /cancel to abort.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_IMAGES
    
    elif query.data == 'pdf_merge':
        context.user_data['pdf_action'] = 'merge'
        await query.edit_message_text(
            "📑 *Merge PDFs*\n\n"
            "Send me 2 or more PDF files to merge.\n"
            "Send /done when finished.\n"
            "Send /cancel to abort.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_PDFS
    
    elif query.data == 'pdf_extract_text':
        context.user_data['pdf_action'] = 'extract_text'
        await query.edit_message_text(
            "📝 *Extract Text from PDF*\n\n"
            "Send me a PDF file to extract text.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    elif query.data == 'pdf_info':
        context.user_data['pdf_action'] = 'info'
        await query.edit_message_text(
            "ℹ️ *PDF Information*\n\n"
            "Send me a PDF file to get details.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def receive_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive files for PDF operations"""
    user_id = update.effective_user.id
    
    # Check anti-spam
    allowed, message = await anti_spam.check_user(user_id)
    if not allowed:
        await update.message.reply_text(message)
        return ConversationHandler.END
    
    action = context.user_data.get('pdf_action')
    
    if action == 'merge':
        return await handle_merge_pdf_files(update, context)
    elif action == 'images_to_pdf':
        return await handle_images_to_pdf_files(update, context)

async def handle_merge_pdf_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF merge files"""
    if update.message.document and update.message.document.mime_type == 'application/pdf':
        if 'pdf_files' not in context.user_data:
            context.user_data['pdf_files'] = []
        
        # Download PDF file
        file = await update.message.document.get_file()
        tmp_path = create_temp_file('.pdf')
        await file.download_to_drive(tmp_path)
        
        context.user_data['pdf_files'].append(tmp_path)
        
        file_count = len(context.user_data['pdf_files'])
        await update.message.reply_text(
            f"✅ PDF file received! ({file_count} so far)\n"
            "Send more PDFs or send /done to merge."
        )
        return WAITING_FOR_PDFS
    else:
        await update.message.reply_text("❌ Please send a PDF file.")
        return WAITING_FOR_PDFS

async def handle_images_to_pdf_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image files for PDF conversion"""
    if update.message.photo or (update.message.document and update.message.document.mime_type.startswith('image/')):
        if 'image_files' not in context.user_data:
            context.user_data['image_files'] = []
        
        # Download image file
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
        else:
            file = await update.message.document.get_file()
        
        tmp_path = create_temp_file('.jpg')
        await file.download_to_drive(tmp_path)
        
        context.user_data['image_files'].append(tmp_path)
        
        file_count = len(context.user_data['image_files'])
        await update.message.reply_text(
            f"✅ Image received! ({file_count} so far)\n"
            "Send more images or send /done to convert."
        )
        return WAITING_FOR_IMAGES
    else:
        await update.message.reply_text("❌ Please send an image file.")
        return WAITING_FOR_IMAGES

async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process collected files"""
    user_id = update.effective_user.id
    action = context.user_data.get('pdf_action')
    
    if action == 'merge':
        files = context.user_data.get('pdf_files', [])
        if len(files) < 2:
            await update.message.reply_text("❌ Please send at least 2 PDF files.")
            return ConversationHandler.END
        
        processing_msg = await update.message.reply_text("📑 Merging PDFs...")
        
        try:
            result, error = await pdf_service.merge_pdfs(files)
            
            # Clean up temp files
            for f in files:
                os.unlink(f)
            context.user_data['pdf_files'] = []
            
            if error:
                await processing_msg.edit_text(f"❌ Error: {error}")
            else:
                # Send merged PDF
                await update.message.reply_document(
                    document=result,
                    filename="merged.pdf",
                    caption="✅ *PDFs Merged Successfully!*",
                    parse_mode='Markdown'
                )
                await processing_msg.delete()
                
                # Log usage
                db.log_usage(user_id, 'pdf_merge')
                
        except Exception as e:
            logger.error(f"PDF merge error: {e}")
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    elif action == 'images_to_pdf':
        files = context.user_data.get('image_files', [])
        if len(files) < 2:
            await update.message.reply_text("❌ Please send at least 2 images.")
            return ConversationHandler.END
        
        processing_msg = await update.message.reply_text("🖼 Converting images to PDF...")
        
        try:
            result, error = await pdf_service.images_to_pdf(files)
            
            # Clean up temp files
            for f in files:
                os.unlink(f)
            context.user_data['image_files'] = []
            
            if error:
                await processing_msg.edit_text(f"❌ Error: {error}")
            else:
                await update.message.reply_document(
                    document=result,
                    filename="converted.pdf",
                    caption="✅ *Images Converted to PDF!*",
                    parse_mode='Markdown'
                )
                await processing_msg.delete()
                
                # Log usage
                db.log_usage(user_id, 'pdf_images_to_pdf')
                
        except Exception as e:
            logger.error(f"Images to PDF error: {e}")
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    return ConversationHandler.END

async def handle_pdf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle single PDF file for info or text extraction"""
    user_id = update.effective_user.id
    action = context.user_data.get('pdf_action', 'info')
    
    if update.message.document and update.message.document.mime_type == 'application/pdf':
        processing_msg = await update.message.reply_text("📄 Processing PDF...")
        
        try:
            # Download PDF file
            file = await update.message.document.get_file()
            tmp_path = create_temp_file('.pdf')
            await file.download_to_drive(tmp_path)
            
            if action == 'info':
                info, error = await pdf_service.get_pdf_info(tmp_path)
                
                if error:
                    await processing_msg.edit_text(f"❌ Error: {error}")
                else:
                    info_text = f"""
📄 *PDF Information*

📝 *Pages:* {info['pages']}
🔒 *Encrypted:* {'Yes' if info['encrypted'] else 'No'}

*Metadata:*
• Title: {info['metadata'].get('title', 'N/A')}
• Author: {info['metadata'].get('author', 'N/A')}
• Creator: {info['metadata'].get('creator', 'N/A')}
• Subject: {info['metadata'].get('subject', 'N/A')}
"""
                    await processing_msg.edit_text(info_text, parse_mode='Markdown')
                    db.log_usage(user_id, 'pdf_info')
            
            elif action == 'extract_text':
                text, error = await pdf_service.extract_text_from_pdf(tmp_path)
                
                if error:
                    await processing_msg.edit_text(f"❌ Error: {error}")
                else:
                    # Send extracted text (may need to split if too long)
                    if len(text) > 4096:
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
                    db.log_usage(user_id, 'pdf_extract_text')
            
            # Clean up
            os.unlink(tmp_path)
            
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
    else:
        await update.message.reply_text("❌ Please send a PDF file.")

# PDF conversation handler
pdf_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(pdf_callback, pattern='^pdf_')],
    states={
        WAITING_FOR_PDFS: [
            MessageHandler(filters.Document.PDF, handle_merge_pdf_files),
            CommandHandler('done', done_command)
        ],
        WAITING_FOR_IMAGES: [
            MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_images_to_pdf_files),
            CommandHandler('done', done_command)
        ],
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)],
)

# Handler setup
pdf_tools_handlers = [
    CommandHandler('pdf', pdf_command),
    pdf_conv_handler,
    MessageHandler(filters.Document.PDF, handle_pdf_file),
]
