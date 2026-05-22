import sqlite3
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import utils
from utils import DB_FILE, OWNER_ID, MAINTENANCE_MODE, auto_clear_cache, auto_backup_db, logger

# ============================================
# الدوال المساعدة
# ============================================

def get_total_users() -> int:
    """الحصول على عدد المستخدمين"""
    try:
        conn = sqlite3.connect(DB_FILE)
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"خطأ في جلب عدد المستخدمين: {e}")
        return 0

def get_total_files() -> int:
    """الحصول على عدد الملفات"""
    try:
        conn = sqlite3.connect(DB_FILE)
        count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"خطأ في جلب عدد الملفات: {e}")
        return 0

def get_active_today() -> int:
    """الحصول على عدد المستخدمين النشطين اليوم"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_FILE)
        count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE last_active LIKE ?", 
            (f"{today}%",)
        ).fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"خطأ في جلب النشطين اليوم: {e}")
        return 0

def get_total_size() -> int:
    """الحصول على إجمالي حجم الملفات"""
    try:
        conn = sqlite3.connect(DB_FILE)
        total = conn.execute("SELECT SUM(file_size) FROM files").fetchone()[0] or 0
        conn.close()
        return total
    except Exception as e:
        logger.error(f"خطأ في جلب الحجم الكلي: {e}")
        return 0

def get_top_users(limit: int = 5):
    """الحصول على أكثر المستخدمين نشاطاً"""
    try:
        conn = sqlite3.connect(DB_FILE)
        users = conn.execute(
            "SELECT user_id, first_name, total_operations FROM users ORDER BY total_operations DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return users
    except Exception as e:
        logger.error(f"خطأ في جلب المستخدمين النشطين: {e}")
        return []

# ============================================
# المعالج الرئيسي للوحة التحكم
# ============================================

async def panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فتح لوحة تحكم المطور"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 غير مصرح لك!")
        return

    from keyboards import admin_panel_keyboard
    
    # إحصائيات سريعة
    total_users = get_total_users()
    total_files = get_total_files()
    active_today = get_active_today()
    
    await update.message.reply_text(
        f"🛠 **لوحة تحكم المطور**\n\n"
        f"📊 **الإحصائيات السريعة:**\n"
        f"👤 إجمالي المستخدمين: {total_users}\n"
        f"📁 إجمالي العمليات: {total_files}\n"
        f"🟢 نشط اليوم: {active_today}\n"
        f"🔧 وضع الصيانة: {'🟢 مفعل' if utils.MAINTENANCE_MODE else '🔴 معطل'}\n\n"
        f"يمكنك التحكم في البوت من هنا:",
        reply_markup=admin_panel_keyboard(utils.MAINTENANCE_MODE)
    )

# ============================================
# معالج الأزرار
# ============================================

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المعالجة الخاصة بأزرار لوحة التحكم"""
    query = update.callback_query
    
    # التحقق من الصلاحية
    if query.from_user.id != OWNER_ID:
        await query.answer("🚫 غير مصرح لك!", show_alert=True)
        return

    from keyboards import admin_panel_keyboard
    
    # ===== إحصائيات شاملة =====
    if query.data == "admin_stats":
        users_count = get_total_users()
        files_count = get_total_files()
        active_today = get_active_today()
        total_size = get_total_size()
        top_users = get_top_users(5)
        
        stats_text = (
            f"📊 **إحصائيات البوت الشاملة:**\n\n"
            f"👤 **المستخدمين:**\n"
            f"• إجمالي المشتركين: {users_count}\n"
            f"• نشط اليوم: {active_today}\n\n"
            f"📁 **العمليات:**\n"
            f"• العمليات الناجحة: {files_count}\n"
            f"• إجمالي حجم الملفات: {total_size // (1024*1024)} MB\n\n"
            f"🏆 **أكثر المستخدمين نشاطاً:**\n"
        )
        
        if top_users:
            for i, (user_id, name, ops) in enumerate(top_users, 1):
                stats_text += f"{i}. {name} - {ops} عملية\n"
        else:
            stats_text += "لا توجد بيانات كافية\n"
        
        await query.edit_message_text(
            stats_text,
            reply_markup=admin_panel_keyboard(utils.MAINTENANCE_MODE)
        )
        await query.answer()
        return

    # ===== إحصائيات متقدمة =====
    elif query.data == "admin_advanced_stats":
        conn = sqlite3.connect(DB_FILE)
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_ops = conn.execute(
            "SELECT COUNT(*) FROM files WHERE date LIKE ?", (f"{today}%",)
        ).fetchone()[0] or 0
        
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_ops = conn.execute(
            "SELECT COUNT(*) FROM files WHERE date >= ?", (week_ago,)
        ).fetchone()[0] or 0
        
        broadcasts = conn.execute(
            "SELECT COUNT(*) FROM broadcast_history"
        ).fetchone()[0] if 'broadcast_history' in [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else 0
        
        conn.close()
        
        await query.edit_message_text(
            f"📈 **إحصائيات متقدمة:**\n\n"
            f"📅 عمليات اليوم: {today_ops}\n"
            f"📆 عمليات الأسبوع: {week_ops}\n"
            f"📢 عدد الإذاعات: {broadcasts}\n"
            f"⚙️ وضع الصيانة: {'🟢 مفعل' if utils.MAINTENANCE_MODE else '🔴 معطل'}\n\n"
            f"💡 استخدم الأزرار الأخرى للتحكم بالبوت",
            reply_markup=admin_panel_keyboard(utils.MAINTENANCE_MODE)
        )
        await query.answer()
        return

    # ===== تبديل وضع الصيانة =====
    elif query.data == "toggle_maintenance":
        utils.MAINTENANCE_MODE = not utils.MAINTENANCE_MODE
        status_text = "🟢 تفعيل" if utils.MAINTENANCE_MODE else "🔴 إيقاف"
        
        await query.answer(f"✅ تم {status_text} وضع الصيانة")
        await query.edit_message_reply_markup(reply_markup=admin_panel_keyboard(utils.MAINTENANCE_MODE))
        return

    # ===== الإذاعة =====
    elif query.data == "admin_broadcast":
        context.user_data['admin_step'] = 'broadcasting'
        await query.edit_message_text(
            "📢 **إرسال إذاعة للمستخدمين**\n\n"
            "أرسل الآن الرسالة (نص فقط) ليتم عمل إذاعة لجميع المستخدمين.\n\n"
            "⚠️ ملاحظة: يمكنك استخدام الإيموجي والتنسيق العادي.\n\n"
            "لإلغاء الإذاعة اكتب /cancel"
        )
        await query.answer()
        return

    # ===== نسخ احتياطي =====
    elif query.data == "admin_backup":
        await query.answer("⏳ جاري عمل نسخة احتياطية...")
        success = await auto_backup_db()
        if success:
            await query.edit_message_text(
                "✅ **تم عمل نسخة احتياطية بنجاح!**\n\n"
                "تم حفظ النسخة في مجلد 'backups'",
                reply_markup=admin_panel_keyboard(utils.MAINTENANCE_MODE)
            )
        else:
            await query.edit_message_text(
                "❌ فشل في عمل نسخة احتياطية",
                reply_markup=admin_panel_keyboard(utils.MAINTENANCE_MODE)
            )
        return

    # ===== تنظيف الملفات المؤقتة =====
    elif query.data == "admin_cleanup":
        await query.answer("⏳ جاري التنظيف...")
        await auto_clear_cache()
        await query.edit_message_text(
            "🧹 **تم تنظيف جميع الملفات المؤقتة بنجاح!**\n\n"
            "تم حذف جميع الملفات غير الضرورية.",
            reply_markup=admin_panel_keyboard(utils.MAINTENANCE_MODE)
        )
        return

    # ===== إغلاق اللوحة =====
    elif query.data == "close_admin":
        await query.message.delete()
        await query.answer()
        return

    # ===== رجوع للوحة الرئيسية =====
    elif query.data == "back_to_admin_panel":
        await panel_handler(update, context)
        await query.answer()
        return

    # ===== أي أمر آخر =====
    else:
        await query.answer("⚠️ أمر غير معروف", show_alert=True)

# ============================================
# دالة عرض لوحة التحكم (مساعدة)
# ============================================

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض لوحة التحكم (دالة مساعدة)"""
    from keyboards import admin_panel_keyboard
    
    total_users = get_total_users()
    total_files = get_total_files()
    
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(
            f"🛠 **لوحة تحكم المطور**\n\n"
            f"📊 الإحصائيات:\n"
            f"👤 المستخدمين: {total_users}\n"
            f"📁 العمليات: {total_files}\n\n"
            f"اختر الإجراء المناسب:",
            reply_markup=admin_panel_keyboard(utils.MAINTENANCE_MODE)
        )
    else:
        await update.message.reply_text(
            f"🛠 **لوحة تحكم المطور**\n\n"
            f"📊 الإحصائيات:\n"
            f"👤 المستخدمين: {total_users}\n"
            f"📁 العمليات: {total_files}\n\n"
            f"اختر الإجراء المناسب:",
            reply_markup=admin_panel_keyboard(utils.MAINTENANCE_MODE)
        )
