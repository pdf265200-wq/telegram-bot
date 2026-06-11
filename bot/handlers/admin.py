from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from bot.database.db_manager import DatabaseManager
from bot.config import Config
import logging

logger = logging.getLogger(__name__)
db = DatabaseManager()

# Conversation states
BROADCAST_MESSAGE = 1
BAN_USER = 2
UNBAN_USER = 3

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel main menu"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        await update.message.reply_text("⛔ Unauthorized access.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data='admin_stats')],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data='admin_broadcast')],
        [InlineKeyboardButton("👥 User Management", callback_data='admin_users')],
        [InlineKeyboardButton("🚫 Ban User", callback_data='admin_ban')],
        [InlineKeyboardButton("✅ Unban User", callback_data='admin_unban')],
        [InlineKeyboardButton("🔧 Maintenance Mode", callback_data='admin_maintenance')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 *Admin Panel*\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id not in Config.ADMIN_IDS:
        await query.edit_message_text("⛔ Unauthorized access.")
        return ConversationHandler.END
    
    if query.data == 'admin_stats':
        await show_statistics(query)
    elif query.data == 'admin_broadcast':
        await query.edit_message_text("📢 *Broadcast Message*\n\nSend me the message you want to broadcast to all users.\n\nSend /cancel to abort.", parse_mode='Markdown')
        return BROADCAST_MESSAGE
    elif query.data == 'admin_users':
        await show_users(query)
    elif query.data == 'admin_ban':
        await query.edit_message_text("🚫 *Ban User*\n\nSend me the user ID to ban.\n\nSend /cancel to abort.", parse_mode='Markdown')
        return BAN_USER
    elif query.data == 'admin_unban':
        await query.edit_message_text("✅ *Unban User*\n\nSend me the user ID to unban.\n\nSend /cancel to abort.", parse_mode='Markdown')
        return UNBAN_USER
    elif query.data == 'admin_maintenance':
        await toggle_maintenance(query)
    
    return ConversationHandler.END

async def show_statistics(query):
    """Show bot statistics"""
    total_users = db.get_total_users()
    active_today = db.get_active_users_today()
    daily_stats = db.get_daily_stats()
    command_stats = db.get_command_stats()
    
    stats_text = f"📊 *Bot Statistics*\n\n"
    stats_text += f"👥 Total Users: {total_users}\n"
    stats_text += f"📈 Active Today: {active_today}\n\n"
    stats_text += "*Daily Usage (Last 7 days):*\n"
    
    for date, count in daily_stats.items():
        stats_text += f"• {date}: {count} requests\n"
    
    stats_text += "\n*Command Usage:*\n"
    for command, count in command_stats:
        stats_text += f"• {command}: {count} times\n"
    
    await query.edit_message_text(stats_text, parse_mode='Markdown')

async def show_users(query):
    """Show user list"""
    users = db.get_all_users()
    users_text = f"👥 *Users List* ({len(users)} total)\n\n"
    
    for i, user in enumerate(users[:10], 1):  # Show first 10
        status = "🚫" if user.is_banned else "✅"
        users_text += f"{i}. {status} {user.first_name or 'N/A'} (ID: {user.user_id})\n"
    
    if len(users) > 10:
        users_text += f"\n... and {len(users) - 10} more users"
    
    await query.edit_message_text(users_text, parse_mode='Markdown')

async def toggle_maintenance(query):
    """Toggle maintenance mode"""
    Config.MAINTENANCE_MODE = not Config.MAINTENANCE_MODE
    status = "enabled" if Config.MAINTENANCE_MODE else "disabled"
    await query.edit_message_text(f"🔧 Maintenance mode {status}.")

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message"""
    user_id = update.effective_user.id
    if user_id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    message_text = update.message.text
    if message_text == '/cancel':
        await update.message.reply_text("❌ Broadcast cancelled.")
        return ConversationHandler.END
    
    users = db.get_all_users()
    success_count = 0
    fail_count = 0
    
    await update.message.reply_text(f"📢 Sending broadcast to {len(users)} users...")
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.user_id,
                text=f"📢 *Broadcast from Admin:*\n\n{message_text}",
                parse_mode='Markdown'
            )
            success_count += 1
        except Exception as e:
            fail_count += 1
            logger.error(f"Failed to send broadcast to {user.user_id}: {e}")
    
    # Log broadcast
    db.add_broadcast(user_id, message_text, success_count)
    
    await update.message.reply_text(
        f"✅ Broadcast complete!\n\n"
        f"✅ Sent: {success_count}\n"
        f"❌ Failed: {fail_count}"
    )
    
    return ConversationHandler.END

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user"""
    user_id = update.effective_user.id
    if user_id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    try:
        target_id = int(update.message.text)
        if db.ban_user(target_id):
            await update.message.reply_text(f"✅ User {target_id} has been banned.")
        else:
            await update.message.reply_text(f"❌ User {target_id} not found.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
    
    return ConversationHandler.END

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    user_id = update.effective_user.id
    if user_id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    try:
        target_id = int(update.message.text)
        if db.unban_user(target_id):
            await update.message.reply_text(f"✅ User {target_id} has been unbanned.")
        else:
            await update.message.reply_text(f"❌ User {target_id} not found.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
    
    return ConversationHandler.END

# Admin conversation handler
admin_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_callback, pattern='^admin_')],
    states={
        BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
        BAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ban_user)],
        UNBAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, unban_user)],
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)],
)

admin_handlers = [
    CommandHandler('admin', admin_panel),
    admin_conv_handler,
]
