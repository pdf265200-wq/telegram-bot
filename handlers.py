import os
import subprocess
import sqlite3
import asyncio
import shutil
from datetime import datetime
from collections import deque
from telegram import Update
from telegram.ext import ContextTypes
from mutagen.id3 import ID3, TIT2, TPE1, APIC, error as MutagenError
from PIL import Image

from utils import (check_subscription, is_maintenance, DB_FILE, OWNER_ID, 
                   MAX_FILE_SIZE, get_channel_cover, add_to_history, 
                   undo_last_operation, update_user_stats, log_operation,
                   auto_backup_db)

# متغيرات متطورة للطابور
processing_tasks = {}  # {user_id: task_info}
task_queue = deque()
MAX_CONCURRENT = 3

async def process_next_task(context: ContextTypes.DEFAULT_TYPE):
    """معالجة المهمة التالية في الطابور"""
    global processing_tasks
    
    while task_queue and len(processing_tasks) < MAX_CONCURRENT:
        task = task_queue.popleft()
        user_id, update, context_copy = task
        processing_tasks[user_id] = task
        asyncio.create_task(process_media_task(user_id, update, context_copy))

async def process_media_task(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ملف الوسائط بشكل غير متزامن"""
    try:
        # معالجة الملف هنا
        pass
    finally:
        if user_id in processing_tasks:
            del processing_tasks[user_id]
        await process_next_task(context)

# ============================================
# دالة البداية المحسنة
# ============================================
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): return
    from keyboards import main_menu_keyboard
    
    user = update.effective_user
    if not await check_subscription(user.id, context):
        await update.message.reply_text("⚠️ اشترك بالقناة أولاً: @THTOMI")
        return

    conn = sqlite3.connect(DB_FILE)
    # تحديث أو إضافة المستخدم مع معلومات إضافية
    conn.execute("INSERT OR IGNORE INTO users(user_id, first_name, username, joined_date, last_active) VALUES (?, ?, ?, ?, ?)",
                (user.id, user.first_name, user.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.execute("UPDATE users SET last_active = ? WHERE user_id = ?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user.id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"🚀 أهلاً بك {user.first_name} في بوت الخدمات الصوتية.\n"
        f"📊 عدد عملياتك السابقة: {get_user_files_count(user.id)}\n\n"
        f"إختر ماذا تريد أن تفعل الآن:",
        reply_markup=main_menu_keyboard()
    )

def get_user_files_count(user_id: int) -> int:
    """الحصول على عدد ملفات المستخدم"""
    conn = sqlite3.connect(DB_FILE)
    count = conn.execute("SELECT COUNT(*) FROM files WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()
    return count

# ============================================
# معالج الكولباك المحسن
# ============================================
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # ===== زر التراجع الجديد =====
    if data == "undo_last":
        success, message = await undo_last_operation(user_id, context)
        await query.answer(message, show_alert=True)
        if success:
            await query.edit_message_text(
                f"✅ {message}\n\nيمكنك متابعة استخدام البوت.",
                reply_markup=await get_back_keyboard()
            )
        return
    
    # ===== أزرار أغنيتي الجديدة =====
    if data == "mysong_edit":
        context.user_data.clear()
        context.user_data['mysong_mode'] = 'edit'
        context.user_data['step'] = 'waiting_for_audio'
        await query.edit_message_text(
            "🎵 **تعديل أغنية موجودة**\n\n"
            "📝 **الخطوات:**\n"
            "1️⃣ أرسل الملف الصوتي (MP3)\n"
            "2️⃣ أرسل اسم الأغنية\n"
            "3️⃣ أرسل اسم الفنان\n"
            "4️⃣ أرسل الصورة (اختياري)\n\n"
            "✨ **ميزة جديدة:** يمكنك الآن إرسال صورة أو الاستغناء عنها لاستخدام صورة القناة"
        )
    
    elif data == "mysong_extract":
        context.user_data.clear()
        context.user_data['mysong_mode'] = 'extract'
        context.user_data['step'] = 'waiting_for_video'
        await query.edit_message_text(
            "🎬 **استخراج صوت من فيديو + إضافة صورة**\n\n"
            "📝 **الخطوات:**\n"
            "1️⃣ أرسل ملف الفيديو\n"
            "2️⃣ أرسل اسم الأغنية\n"
            "3️⃣ أرسل اسم الفنان\n"
            "4️⃣ أرسل الصورة (اختياري)\n\n"
            "💡 **نصيحة:** استخدم فيديوهات بجودة عالية للحصول على صوت أفضل"
        )
    
    elif data == "mysong_new":
        context.user_data.clear()
        context.user_data['mysong_mode'] = 'new'
        context.user_data['step'] = 'waiting_for_audio'
        await query.edit_message_text(
            "🆕 **رفع ملف صوتي + صورة جديدة**\n\n"
            "✨ يمكنك الآن إضافة:\n"
            "• اسم الأغنية\n"
            "• اسم الفنان\n"
            "• صورة الغلاف (اختياري)\n\n"
            "أرسل الملف الصوتي للبدء..."
        )
    
    # ===== أزرار الجودة =====
    elif data.startswith("q_"):
        parts = data.split("_")
        quality = parts[1] + "k"
        action = parts[2]
        context.user_data['selected_quality'] = quality
        context.user_data['action_type'] = action
        
        msg = f"✅ تم اختيار جودة {quality}\n\n"
        if action == "edit":
            msg += "🎵 أرسل الآن الملف الصوتي (MP3) لتعديله:"
        else:
            msg += "🎬 أرسل الآن ملف الفيديو لاستخراج الصوت منه:"
        
        await query.edit_message_text(msg)
    
    elif data == "cancel_action":
        await query.edit_message_text("❌ تم إلغاء العملية.")
        context.user_data.clear()
    
    elif data == "my_stats":
        stats = await get_user_full_stats(user_id)
        await query.edit_message_text(stats, reply_markup=await get_back_keyboard())

async def get_user_full_stats(user_id: int) -> str:
    """إحصائيات مفصلة للمستخدم"""
    conn = sqlite3.connect(DB_FILE)
    
    # عدد الملفات
    files_count = conn.execute("SELECT COUNT(*) FROM files WHERE user_id = ?", (user_id,)).fetchone()[0]
    
    # آخر 5 ملفات
    last_files = conn.execute(
        "SELECT title, artist, date FROM files WHERE user_id = ? ORDER BY id DESC LIMIT 5",
        (user_id,)
    ).fetchall()
    
    # إجمالي حجم الملفات
    total_size = conn.execute("SELECT SUM(file_size) FROM files WHERE user_id = ?", (user_id,)).fetchone()[0] or 0
    
    # معلومات المستخدم
    user_info = conn.execute("SELECT joined_date, last_active, total_operations FROM users WHERE user_id = ?", (user_id,)).fetchone()
    
    conn.close()
    
    msg = f"📊 **إحصائياتك الشخصية**\n\n"
    msg += f"👤 تاريخ الانضمام: {user_info[0] if user_info else 'غير معروف'}\n"
    msg += f"📁 عدد العمليات الناجحة: {files_count}\n"
    msg += f"💾 إجمالي حجم الملفات: {total_size // (1024*1024)} MB\n"
    msg += f"⭐ إجمالي العمليات: {user_info[2] if user_info else 0}\n\n"
    
    if last_files:
        msg += "**🎵 آخر أعمالك:**\n"
        for title, artist, date in last_files:
            msg += f"• {title} - {artist}\n"
            msg += f"  📅 {date}\n"
    else:
        msg += "📭 لا توجد عمليات سابقة بعد\n"
    
    msg += "\n💡 **نصيحة:** استخدم زر التراجع إذا أردت استعادة آخر عملية"
    
    return msg

async def get_back_keyboard():
    """لوحة مفاتيح الرجوع"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# معالج الصور المحسن (يدعم عدم إرسال صورة)
# ============================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الصور المرسلة مع دعم عدم إرسال صورة"""
    if await is_maintenance(update, context): return
    
    user_id = update.effective_user.id
    
    # التحقق من أن المستخدم في وضع أغنيتي وينتظر صورة
    if context.user_data.get('mysong_mode') and context.user_data.get('step') == 'waiting_for_cover':
        
        wait_msg = await update.message.reply_text("⏳ جاري معالجة الصورة ودمجها مع الأغنية...")
        
        cover_path = await save_and_optimize_image(update, user_id)
        
        if not cover_path:
            await wait_msg.edit_text("❌ فشل في معالجة الصورة. سيتم استخدام صورة القناة كبديل.")
            cover_path = await get_channel_cover(context)
        
        # معالجة الأغنية
        await process_song_with_cover(update, context, user_id, cover_path, wait_msg)
        return
    
    else:
        await update.message.reply_text("❌ لست في وضع إضافة صورة حالياً. اختر '🖼️ أغنيتي' أولاً.")

async def save_and_optimize_image(update: Update, user_id: int) -> str:
    """حفظ وتحسين الصورة"""
    cover_path = f"temp_images/cover_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # إنشاء مجلد الصور المؤقتة
    os.makedirs("temp_images", exist_ok=True)
    
    # تحديد نوع الصورة
    if update.message.photo:
        photo = update.message.photo[-1]
        tg_photo = await photo.get_file()
        cover_path += ".jpg"
        await tg_photo.download_to_drive(cover_path)
        
    elif update.message.document:
        document = update.message.document
        mime_type = document.mime_type or ""
        file_name = document.file_name or ""
        
        is_image = (mime_type.startswith('image/') or 
                   file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')))
        
        if not is_image:
            return None
        
        tg_doc = await document.get_file()
        
        if file_name.lower().endswith('.png') or 'png' in mime_type:
            cover_path += ".png"
        elif file_name.lower().endswith('.gif') or 'gif' in mime_type:
            cover_path += ".gif"
        elif file_name.lower().endswith('.webp') or 'webp' in mime_type:
            cover_path += ".webp"
        else:
            cover_path += ".jpg"
        
        await tg_doc.download_to_drive(cover_path)
    else:
        return None
    
    # تحسين الصورة
    try:
        with Image.open(cover_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode == 'RGBA':
                    rgb_img.paste(img, mask=img.split()[-1])
                else:
                    rgb_img.paste(img)
                img = rgb_img
            
            if img.width > 500 or img.height > 500:
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            
            img.save(cover_path, 'JPEG', quality=85, optimize=True)
    except Exception as e:
        print(f"خطأ في تحسين الصورة: {e}")
    
    return cover_path

async def process_song_with_cover(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   user_id: int, cover_path: str, wait_msg):
    """معالجة الأغنية مع الصورة"""
    audio_path = context.user_data.get('audio_path')
    title = context.user_data.get('title', 'غير معروف')
    artist = context.user_data.get('artist', 'غير معروف')
    
    if not audio_path or not os.path.exists(audio_path):
        await wait_msg.edit_text("❌ حدث خطأ: الملف الصوتي غير موجود")
        if cover_path and os.path.exists(cover_path):
            os.remove(cover_path)
        return
    
    try:
        # إضافة العلامات للملف الصوتي
        audio = ID3(audio_path) if audio_path else ID3()
        
        audio["TIT2"] = TIT2(encoding=3, text=title)
        audio["TPE1"] = TPE1(encoding=3, text=artist)
        
        # إضافة الصورة إذا كانت موجودة
        if cover_path and os.path.exists(cover_path):
            with open(cover_path, "rb") as img:
                if "APIC" in audio:
                    del audio["APIC"]
                
                mime_type = "image/jpeg"
                if cover_path.endswith('.png'):
                    mime_type = "image/png"
                elif cover_path.endswith('.gif'):
                    mime_type = "image/gif"
                
                audio["APIC"] = APIC(encoding=3, mime=mime_type, type=3, desc="Cover", data=img.read())
        
        audio.save(audio_path, v2_version=3)
        
        # الحصول على حجم الملف
        file_size = os.path.getsize(audio_path)
        
        # إرسال الملف النهائي
        with open(audio_path, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                title=title,
                performer=artist,
                caption=f"🎵 {title} - {artist}\n✨ تم المعالجة بواسطة بوت الخدمات الصوتية"
            )
        
        # تسجيل العملية في قاعدة البيانات
        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            "INSERT INTO files (user_id, title, artist, file_size, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, artist, file_size, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.execute("UPDATE users SET total_operations = total_operations + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # إضافة للتاريخ للتراجع
        await add_to_history(user_id, audio_path, f"تعديل {title}")
        
        await wait_msg.delete()
        
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    finally:
        # تنظيف الملفات المؤقتة
        for file in [audio_path, cover_path]:
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass
        
        context.user_data.clear()

# ============================================
# معالج النصوص المحسن (مع دعم التراجع)
# ============================================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id

    # ===== الإذاعة =====
    if context.user_data.get('admin_step') == 'broadcasting':
        if user_id != OWNER_ID:
            context.user_data['admin_step'] = None
            return
        
        await send_broadcast(update, context, user_text)
        return

    # ===== أزرار القائمة الرئيسية المحسنة =====
    if user_text == "🎵 تعديل الأغاني":
        from keyboards import quality_keyboard
        await update.message.reply_text(
            "🎵 **تعديل الأغاني**\n\nاختر جودة الصوت المطلوبة:",
            reply_markup=quality_keyboard("edit")
        )
        return
    
    elif user_text == "🎬 استخراج من الفيديو":
        from keyboards import quality_keyboard
        await update.message.reply_text(
            "🎬 **استخراج من الفيديو**\n\nاختر جودة الصوت المطلوبة:",
            reply_markup=quality_keyboard("extract")
        )
        return
    
    elif user_text == "🖼️ أغنيتي (القائمة المتكاملة)":
        from keyboards import my_song_menu_keyboard
        await update.message.reply_text(
            "🖼️ **قائمة أغنيتي المتكاملة**\n\n"
            "✨ **المميزات الجديدة:**\n"
            "• إضافة صورة غلاف مخصصة\n"
            "• إمكانية الاستغناء عن الصورة (سيتم استخدام صورة القناة)\n"
            "• دعم جميع صيغ الصور\n"
            "• معالجة محسنة للجودة\n\n"
            "اختر ما تريد فعله:",
            reply_markup=my_song_menu_keyboard()
        )
        return
    
    elif user_text == "📊 إحصائياتي":
        stats = await get_user_full_stats(user_id)
        await update.message.reply_text(stats)
        return
    
    elif user_text == "↩️ التراجع عن آخر عملية":
        success, message = await undo_last_operation(user_id, context)
        await update.message.reply_text(message)
        return
    
    elif user_text == "▶️ تشغيل البوت":
        await start_handler(update, context)
        return
    
    elif user_text == "🔙 الرجوع إلى البداية":
        await start_handler(update, context)
        return

    # ===== معالج وضع أغنيتي =====
    if context.user_data.get('mysong_mode'):
        step = context.user_data.get('step')
        
        if step == 'waiting_for_title':
            context.user_data['title'] = user_text
            context.user_data['step'] = 'waiting_for_artist'
            await update.message.reply_text("🎤 أرسل الآن **اسم الفنان**:")
            return
        
        elif step == 'waiting_for_artist':
            context.user_data['artist'] = user_text
            context.user_data['step'] = 'waiting_for_cover'
            await update.message.reply_text(
                "🖼️ **أرسل الصورة (اختياري)**\n\n"
                "يمكنك:\n"
                "• إرسال صورة (JPG/PNG) لإضافتها كغلاف\n"
                "• كتابة 'تخطي' لاستخدام صورة القناة الافتراضية\n\n"
                "ملاحظة: يمكنك تخطي هذه الخطوة إذا كنت لا تريد إضافة صورة."
            )
            return
        
        elif step == 'waiting_for_cover':
            if user_text.lower() in ['تخطي', 'skip', 'تجاهل']:
                # تخطي الصورة واستخدام صورة القناة
                cover_path = await get_channel_cover(context)
                wait_msg = await update.message.reply_text("⏳ جاري معالجة الأغنية بدون صورة مخصصة...")
                await process_song_with_cover(update, context, user_id, cover_path, wait_msg)
            else:
                await update.message.reply_text("❌ أنا في انتظار صورة أو كتابة 'تخطي'. أرسل صورة من فضلك.")
            return
        
        return

    # ===== إكمال العملية القديمة =====
    if "file_path" in context.user_data:
        await process_legacy_workflow(update, context, user_id)

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """إرسال إذاعة لجميع المستخدمين"""
    conn = sqlite3.connect(DB_FILE)
    users = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    
    success_count = 0
    fail_count = 0
    
    status_msg = await update.message.reply_text("⏳ جاري إرسال الإذاعة...")
    
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=message)
            success_count += 1
            await asyncio.sleep(0.05)  # تجنب الـ rate limiting
        except Exception as e:
            fail_count += 1
    
    # تسجيل الإذاعة
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO broadcast_history (message, recipients, sent_date) VALUES (?, ?, ?)",
                (message[:200], success_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    
    context.user_data['admin_step'] = None
    await status_msg.edit_text(
        f"✅ **تمت الإذاعة بنجاح**\n\n"
        f"📨 تم الإرسال لـ: {success_count} مستخدم\n"
        f"❌ فشل الإرسال لـ: {fail_count} مستخدم"
    )

async def process_legacy_workflow(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """معالجة سير العمل القديم"""
    step = context.user_data.get("step")
    file_path = context.user_data["file_path"]

    if step == "title":
        context.user_data["title"] = update.message.text
        context.user_data["step"] = "artist"
        await update.message.reply_text("🎤 الآن أرسل (اسم الفنان):")
    
    elif step == "artist":
        title = context.user_data["title"]
        artist = update.message.text
        
        try:
            audio = ID3(file_path)
        except:
            audio = ID3()
        
        audio["TIT2"] = TIT2(encoding=3, text=title)
        audio["TPE1"] = TPE1(encoding=3, text=artist)
        
        cover = await get_channel_cover(context)
        if cover:
            with open(cover, "rb") as img:
                if "APIC" in audio:
                    del audio["APIC"]
                audio["APIC"] = APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=img.read())
        audio.save(file_path)

        # الحصول على حجم الملف
        file_size = os.path.getsize(file_path)
        
        with open(file_path, "rb") as f:
            await update.message.reply_audio(audio=f, title=title, performer=artist)

        # تسجيل العملية
        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            "INSERT INTO files (user_id, title, artist, file_size, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, artist, file_size, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.execute("UPDATE users SET total_operations = total_operations + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # إضافة للتاريخ
        await add_to_history(user_id, file_path, f"تعديل {title}")

        if os.path.exists(file_path):
            os.remove(file_path)
        context.user_data.clear()
