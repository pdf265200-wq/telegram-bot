"""
Admin panel handler with full functionality
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CommandHandler, 
    CallbackQueryHandler, 
    ConversationHandler, 
    MessageHandler, 
    filters
)
from telegram.constants import ParseMode
from bot.database.db_manager import DatabaseManager
from bot.database.models import User
from bot.config import Config
import logging

logger = logging.getLogger(__name__)
db = DatabaseManager()

# Conversation states
BROADCAST_MESSAGE = 1
BAN_USER = 2
UNBAN_USER = 3
ADD_ADMIN = 4
REMOVE_ADMIN = 5

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel main menu"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMIN_IDS:
        await update.message.reply_text("⛔ Unauthorized access. This incident will be reported.")
        logger.warning(f"Unauthorized admin access attempt by user {user_id}")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Statistics", callback_data='admin_stats'),
            InlineKeyboardButton("📢 Broadcast", callback_data='admin_broadcast')
        ],
        [
            InlineKeyboardButton("👥 Users List", callback_data='admin_users'),
            InlineKeyboardButton("🔍 User Info", callback_data='admin_user_info')
        ],
        [
            InlineKeyboardButton("🚫 Ban User", callback_data='admin_ban'),
            InlineKeyboardButton("✅ Unban User", callback_data='admin_unban')
        ],
        [
            InlineKeyboardButton("👑 Add Admin", callback_data='admin_add_admin'),
            InlineKeyboardButton("⬇️ Remove Admin", callback_data='admin_remove_admin')
        ],
        [
            InlineKeyboardButton("🔧 Maintenance Mode", callback_data='admin_maintenance'),
            InlineKeyboardButton("🔄 Restart Bot", callback_data='admin_restart')
        ],
        [
            InlineKeyboardButton("📝 View Logs", callback_data='admin_logs'),
            InlineKeyboardButton("🗄 Database Info", callback_data='admin_db_info')
        ],
        [
            InlineKeyboardButton("❌ Close Panel", callback_data='admin_close')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 *Admin Control Panel*\n\n"
        f"Welcome, {update.effective_user.first_name}!\n"
        f"Bot Version: {Config.BOT_VERSION}\n"
        f"Select an option below:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Verify admin access
    if user_id not in Config.ADMIN_IDS:
        await query.edit_message_text("⛔ Unauthorized access.")
        return ConversationHandler.END
    
    # Route to appropriate handler
    if query.data == 'admin_stats':
        await show_statistics(query)
        return ConversationHandler.END
    elif query.data == 'admin_broadcast':
        await query.edit_message_text(
            "📢 *Broadcast Message*\n\n"
            "Send me the message you want to broadcast to all users.\n"
            "You can use:\n"
            "• Markdown formatting\n"
            "• Emojis\n\n"
            "Send /cancel to abort.",
            parse_mode=ParseMode.MARKDOWN
        )
        return BROADCAST_MESSAGE
    elif query.data == 'admin_users':
        await show_users(query)
        return ConversationHandler.END
    elif query.data == 'admin_user_info':
        await query.edit_message_text(
            "🔍 *User Information*\n\n"
            "Send me the user ID to get detailed information.\n\n"
            "Send /cancel to abort.",
            parse_mode=ParseMode.MARKDOWN
        )
        return ADD_ADMIN  # Using ADD_ADMIN state for user info
    elif query.data == 'admin_ban':
        await query.edit_message_text(
            "🚫 *Ban User*\n\n"
            "Send me the user ID to ban.\n"
            "You can ban multiple users by sending IDs separated by commas.\n\n"
            "Send /cancel to abort.",
            parse_mode=ParseMode.MARKDOWN
        )
        return BAN_USER
    elif query.data == 'admin_unban':
        await query.edit_message_text(
            "✅ *Unban User*\n\n"
            "Send me the user ID to unban.\n"
            "You can unban multiple users by sending IDs separated by commas.\n\n"
            "Send /cancel to abort.",
            parse_mode=ParseMode.MARKDOWN
        )
        return UNBAN_USER
    elif query.data == 'admin_add_admin':
        await query.edit_message_text(
            "👑 *Add Admin*\n\n"
            "Send me the user ID to add as admin.\n\n"
            "Send /cancel to abort.",
            parse_mode=ParseMode.MARKDOWN
        )
        return ADD_ADMIN
    elif query.data == 'admin_remove_admin':
        await query.edit_message_text(
            "⬇️ *Remove Admin*\n\n"
            "Send me the user ID to remove from admins.\n\n"
            "Send /cancel to abort.",
            parse_mode=ParseMode.MARKDOWN
        )
        return REMOVE_ADMIN
    elif query.data == 'admin_maintenance':
        await toggle_maintenance(query)
        return ConversationHandler.END
    elif query.data == 'admin_restart':
        await restart_bot(query)
        return ConversationHandler.END
    elif query.data == 'admin_logs':
        await view_logs(query)
        return ConversationHandler.END
    elif query.data == 'admin_db_info':
        await database_info(query)
        return ConversationHandler.END
    elif query.data == 'admin_close':
        await query.delete_message()
        return ConversationHandler.END
    
    return ConversationHandler.END

async def show_statistics(query):
    """Show bot statistics"""
    try:
        total_users = db.get_total_users()
        active_today = db.get_active_users_today()
        daily_stats = db.get_daily_stats()
        command_stats = db.get_command_stats()
        
        stats_text = "📊 *Bot Statistics*\n\n"
        stats_text += f"👥 *Total Users:* {total_users}\n"
        stats_text += f"📈 *Active Today:* {active_today}\n"
        stats_text += f"🕐 *Last Updated:* {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        stats_text += "*Daily Usage (Last 7 days):*\n"
        for date, count in daily_stats.items():
            stats_text += f"• {date}: {count} requests\n"
        
        stats_text += "\n*Command Usage:*\n"
        if command_stats:
            for command, count in command_stats:
                stats_text += f"• {command}: {count} times\n"
        else:
            stats_text += "No commands used yet.\n"
        
        await query.edit_message_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error showing statistics: {e}")
        await query.edit_message_text(f"❌ Error loading statistics: {str(e)}")

async def show_users(query, page=1):
    """Show user list with pagination"""
    try:
        users = db.get_all_users()
        users_per_page = 10
        total_pages = max(1, (len(users) + users_per_page - 1) // users_per_page)
        
        start_idx = (page - 1) * users_per_page
        end_idx = min(start_idx + users_per_page, len(users))
        
        users_text = f"👥 *Users List* (Page {page}/{total_pages})\n"
        users_text += f"Total Users: {len(users)}\n\n"
        
        for i, user in enumerate(users[start_idx:end_idx], start_idx + 1):
            status = "🚫" if user.is_banned else "✅"
            admin_star = "⭐" if user.user_id in Config.ADMIN_IDS else ""
            username = user.username or "No username"
            users_text += f"{i}. {status}{admin_star} {user.first_name or 'N/A'} "
            users_text += f"(`{user.user_id}`)\n"
            users_text += f"   @{username} | Requests: {user.total_requests}\n"
        
        # Add navigation buttons
        keyboard = []
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f'users_page_{page-1}'))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f'users_page_{page+1}'))
        if nav_row:
            keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin_back')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(users_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error showing users: {e}")
        await query.edit_message_text(f"❌ Error loading users: {str(e)}")

async def toggle_maintenance(query):
    """Toggle maintenance mode"""
    try:
        current_mode = Config.MAINTENANCE_MODE
        Config.MAINTENANCE_MODE = not current_mode
        
        status = "🟢 ENABLED" if Config.MAINTENANCE_MODE else "🔴 DISABLED"
        mode_text = "Maintenance mode" if Config.MAINTENANCE_MODE else "Normal mode"
        
        await query.edit_message_text(
            f"🔧 *{mode_text}*\n\n"
            f"Status: {status}\n\n"
            f"{'Users cannot use the bot now.' if Config.MAINTENANCE_MODE else 'Bot is operating normally.'}",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Maintenance mode {'enabled' if Config.MAINTENANCE_MODE else 'disabled'} by admin {query.from_user.id}")
    except Exception as e:
        logger.error(f"Error toggling maintenance mode: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}")

async def restart_bot(query):
    """Restart the bot"""
    await query.edit_message_text(
        "🔄 *Restarting Bot...*\n\n"
        "The bot will restart in a few seconds.\n"
        "This may take 10-30 seconds.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Log restart
    logger.warning(f"Bot restart initiated by admin {query.from_user.id}")
    
    # Exit the process (Railway will restart it)
    import os
    import sys
    
    # Give time for message to be sent
    import asyncio
    await asyncio.sleep(2)
    
    os._exit(0)

async def view_logs(query):
    """View recent logs"""
    try:
        log_file = 'logs/bot.log'
        if not __import__('os').path.exists(log_file):
            await query.edit_message_text("📝 No logs found.")
            return
        
        with open(log_file, 'r') as f:
            # Get last 50 lines
            lines = f.readlines()[-50:]
            logs_text = "📝 *Recent Logs (Last 50 lines):*\n\n```\n"
            logs_text += ''.join(lines)
            logs_text += "```"
            
            if len(logs_text) > 4096:
                logs_text = logs_text[:4000] + "\n... (truncated) ...\n```"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(logs_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error viewing logs: {e}")
        await query.edit_message_text(f"❌ Error loading logs: {str(e)}")

async def database_info(query):
    """Show database information"""
    try:
        from bot.database.models import Session, User, UsageStat, BroadcastMessage
        import os
        
        db_path = 'data/bot.db'
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        session = Session()
        
        total_users = session.query(User).count()
        total_stats = session.query(UsageStat).count()
        total_broadcasts = session.query(BroadcastMessage).count()
        banned_users = session.query(User).filter(User.is_banned == True).count()
        
        db_info = "🗄 *Database Information*\n\n"
        db_info += f"📁 *Size:* {db_size / 1024:.2f} KB\n"
        db_info += f"👥 *Users:* {total_users}\n"
        db_info += f"🚫 *Banned Users:* {banned_users}\n"
        db_info += f"📊 *Usage Records:* {total_stats}\n"
        db_info += f"📢 *Broadcasts:* {total_broadcasts}\n"
        
        session.close()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(db_info, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error showing database info: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}")

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message"""
    user_id = update.effective_user.id
    
    # Verify admin
    if user_id not in Config.ADMIN_IDS:
        await update.message.reply_text("⛔ Unauthorized.")
        return ConversationHandler.END
    
    message_text = update.message.text
    
    # Check for cancel
    if message_text == '/cancel':
        await update.message.reply_text("❌ Broadcast cancelled.")
        return ConversationHandler.END
    
    users = db.get_all_users()
    success_count = 0
    fail_count = 0
    blocked_count = 0
    
    status_msg = await update.message.reply_text(f"📢 Sending broadcast to {len(users)} users...")
    
    for i, user in enumerate(users):
        try:
            # Skip banned users
            if user.is_banned:
                continue
                
            await context.bot.send_message(
                chat_id=user.user_id,
                text=f"📢 *Broadcast Message:*\n\n{message_text}",
                parse_mode=ParseMode.MARKDOWN
            )
            success_count += 1
        except Exception as e:
            if "Forbidden" in str(e) or "blocked" in str(e).lower():
                blocked_count += 1
            else:
                fail_count += 1
                logger.error(f"Failed to send broadcast to {user.user_id}: {e}")
        
        # Update progress every 10 users
        if (i + 1) % 10 == 0:
            await status_msg.edit_text(
                f"📢 Sending broadcast... ({i + 1}/{len(users)})"
            )
        
        # Small delay to avoid rate limiting
        if i % 30 == 0 and i > 0:
            import asyncio
            await asyncio.sleep(1)
    
    # Log broadcast
    db.add_broadcast(user_id, message_text, success_count)
    
    await status_msg.edit_text(
        f"✅ *Broadcast Complete!*\n\n"
        f"📊 *Results:*\n"
        f"✅ Sent: {success_count}\n"
        f"🚫 Blocked: {blocked_count}\n"
        f"❌ Failed: {fail_count}\n"
        f"📝 Total users: {len(users)}",
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ConversationHandler.END

async def handle_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ban user"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    text = update.message.text
    if text == '/cancel':
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    try:
        # Handle multiple user IDs
        user_ids = [int(id.strip()) for id in text.split(',')]
        banned_count = 0
        
        for target_id in user_ids:
            if target_id in Config.ADMIN_IDS:
                await update.message.reply_text(f"⚠️ Cannot ban admin (ID: {target_id})")
                continue
                
            if db.ban_user(target_id):
                banned_count += 1
                # Notify banned user
                try:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text="🚫 *You have been banned*\n\n"
                             "You can no longer use this bot.\n"
                             "Contact the administrator if you think this is a mistake.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    pass
        
        await update.message.reply_text(
            f"✅ *Ban Operation Complete*\n\n"
            f"Banned {banned_count} user(s) successfully.",
            parse_mode=ParseMode.MARKDOWN
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID format. Please send numeric IDs.")
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    return ConversationHandler.END

async def handle_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unban user"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    text = update.message.text
    if text == '/cancel':
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    try:
        user_ids = [int(id.strip()) for id in text.split(',')]
        unbanned_count = 0
        
        for target_id in user_ids:
            if db.unban_user(target_id):
                unbanned_count += 1
                # Notify unbanned user
                try:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text="✅ *You have been unbanned*\n\n"
                             "You can now use the bot again.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    pass
        
        await update.message.reply_text(
            f"✅ *Unban Operation Complete*\n\n"
            f"Unbanned {unbanned_count} user(s) successfully.",
            parse_mode=ParseMode.MARKDOWN
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID format. Please send numeric IDs.")
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    return ConversationHandler.END

async def handle_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add admin"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    text = update.message.text
    if text == '/cancel':
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    try:
        new_admin_id = int(text.strip())
        
        if new_admin_id in Config.ADMIN_IDS:
            await update.message.reply_text("⚠️ This user is already an admin.")
            return ConversationHandler.END
        
        Config.ADMIN_IDS.append(new_admin_id)
        await update.message.reply_text(
            f"✅ *Admin Added*\n\n"
            f"User `{new_admin_id}` is now an admin.\n\n"
            f"⚠️ *Note:* This change is temporary and will reset on bot restart.\n"
            f"To make permanent, add the ID to .env file.",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Admin {user_id} added new admin: {new_admin_id}")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID format.")
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    return ConversationHandler.END

async def handle_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle remove admin"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    text = update.message.text
    if text == '/cancel':
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    try:
        remove_admin_id = int(text.strip())
        
        if remove_admin_id == user_id:
            await update.message.reply_text("⚠️ You cannot remove yourself from admins.")
            return ConversationHandler.END
        
        if remove_admin_id not in Config.ADMIN_IDS:
            await update.message.reply_text("⚠️ This user is not an admin.")
            return ConversationHandler.END
        
        Config.ADMIN_IDS.remove(remove_admin_id)
        await update.message.reply_text(
            f"✅ *Admin Removed*\n\n"
            f"User `{remove_admin_id}` is no longer an admin.",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Admin {user_id} removed admin: {remove_admin_id}")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID format.")
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    return ConversationHandler.END

async def handle_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user info request"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    text = update.message.text
    if text == '/cancel':
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    try:
        target_id = int(text.strip())
        user = db.get_or_create_user(user_id=target_id)
        
        if not user:
            await update.message.reply_text("❌ User not found in database.")
            return ConversationHandler.END
        
        user_info = f"🔍 *User Information*\n\n"
        user_info += f"🆔 *ID:* `{user.user_id}`\n"
        user_info += f"👤 *Name:* {user.first_name or 'N/A'} {user.last_name or ''}\n"
        user_info += f"📝 *Username:* @{user.username or 'N/A'}\n"
        user_info += f"📅 *Joined:* {user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else 'N/A'}\n"
        user_info += f"🕐 *Last Active:* {user.last_activity.strftime('%Y-%m-%d %H:%M') if user.last_activity else 'N/A'}\n"
        user_info += f"📊 *Total Requests:* {user.total_requests}\n"
        user_info += f"🚫 *Banned:* {'Yes' if user.is_banned else 'No'}\n"
        user_info += f"⭐ *Admin:* {'Yes' if user.user_id in Config.ADMIN_IDS else 'No'}\n"
        
        await update.message.reply_text(user_info, parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID format.")
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    return ConversationHandler.END

async def admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to admin panel button"""
    query = update.callback_query
    await query.answer()
    await admin_panel(update, context)

async def users_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle users pagination"""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.split('_')[-1])
    await show_users(query, page)

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

# Admin conversation handler
admin_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_callback, pattern='^admin_')],
    states={
        BROADCAST_MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)
        ],
        BAN_USER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ban_user)
        ],
        UNBAN_USER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unban_user)
        ],
        ADD_ADMIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_admin)
        ],
        REMOVE_ADMIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_remove_admin)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel_operation)],
    per_message=False,  # This fixes the PTBUserWarning
    per_chat=True,
    per_user=True
)

# All admin handlers
admin_handlers = [
    CommandHandler('admin', admin_panel),
    admin_conv_handler,
    CallbackQueryHandler(admin_back_callback, pattern='^admin_back$'),
    CallbackQueryHandler(users_page_callback, pattern='^users_page_'),
]
