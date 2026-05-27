from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# القائمة الرئيسية (مع زر تشغيل محسّن)
def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("🚀 تشغيل البوت | بدء جديد")],  # زر تشغيل محسّن
        [KeyboardButton("🎵 تعديل الأغنية"), KeyboardButton("🎬 استخراج صوت من فيديو")],
        [KeyboardButton("🖼️ إنشاء أغنية كاملة (اسم + صورة + صوت)")],
        [KeyboardButton("📊 إحصائياتي"), KeyboardButton("🛠 لوحة التحكم")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# قائمة أغنيتي الداخلية (الخيارات المتكاملة)
def my_song_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 تعديل اسم وصورة أغنية", callback_data="mysong_edit")],
        [InlineKeyboardButton("🎬 استخراج صوت من فيديو + إضافة صورة", callback_data="mysong_extract")],
        [InlineKeyboardButton("🆕 رفع ملف صوتي جديد + صورة", callback_data="mysong_new")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(keyboard)

# قائمة اختيار الجودة للوضع العادي
def quality_keyboard(action_type):
    keyboard = [
        [
            InlineKeyboardButton("🎵 128kbps 📦 صغير", callback_data=f"q_128_{action_type}"),
            InlineKeyboardButton("🎵 192kbps ⚖️ متوسط", callback_data=f"q_192_{action_type}"),
        ],
        [
            InlineKeyboardButton("🎵 256kbps 📀 عالي", callback_data=f"q_256_{action_type}"),
            InlineKeyboardButton("🎵 320kbps 💿 فائق", callback_data=f"q_320_{action_type}"),
        ],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(keyboard)

# لوحة تحكم الإدارة
def admin_panel_keyboard(maintenance_status):
    m_icon = "🔴" if maintenance_status else "🟢"
    m_text = "إيقاف الصيانة" if maintenance_status else "تفعيل الصيانة"
    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats")],
        [InlineKeyboardButton(f"{m_icon} {m_text}", callback_data="toggle_maintenance")],
        [InlineKeyboardButton("📢 إذاعة (Broadcast)", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🗑 تنظيف الملفات المؤقتة", callback_data="admin_clean")],
        [InlineKeyboardButton("❌ إغلاق اللوحة", callback_data="close_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

# لوحة تأكيد للعمليات الحساسة
def confirm_keyboard(action):
    keyboard = [
        [
            InlineKeyboardButton("✅ نعم، أكمل", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ لا، إلغاء", callback_data="cancel_action"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# قائمة مساعدة سريعة
def help_keyboard():
    keyboard = [
        [InlineKeyboardButton("❓ كيفية الاستخدام", callback_data="help_usage")],
        [InlineKeyboardButton("📞 الدعم", callback_data="help_support")],
        [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# زر إلغاء سريع
def cancel_keyboard():
    keyboard = [[InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_action")]]
    return InlineKeyboardMarkup(keyboard)

# قائمة ترحيب سريعة (تظهر بعد الضغط على تشغيل البوت)
def welcome_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎵 تعديل أغنية", callback_data="quick_edit")],
        [InlineKeyboardButton("🎬 استخراج صوت", callback_data="quick_extract")],
        [InlineKeyboardButton("✨ أغنية كاملة", callback_data="quick_full")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
    ]
    return InlineKeyboardMarkup(keyboard)
