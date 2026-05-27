# ============================================
# دالة البداية
# ============================================
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): 
        return
    
    from keyboards import main_menu_keyboard
    
    user = update.effective_user
    if not await check_subscription(user.id, context):
        await update.message.reply_text(
            "⚠️ **أنت غير مشترك في القناة!**\n\n"
            "يجب الاشتراك أولاً في القناة التالية:\n"
            f"👉 @BEXO50\n\n"
            "بعد الاشتراك، ارسل /start مرة أخرى."
        )
        return

    add_user(user.id, user.first_name)

    await update.message.reply_text(
        f"🚀 **أهلاً بك {user.first_name} في بوت الخدمات الصوتية!**\n\n"
        "إختر ما تريد فعله من الأزرار أدناه:",
        reply_markup=main_menu_keyboard()
    )

# ============================================
# معالج الكولباك (الأزرار)
# ============================================
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    await query.answer()
    
    # ===== أزرار وضع "أغنيتي" المتكاملة =====
    if data == "mysong_edit":
        context.user_data.clear()
        context.user_data['mode'] = 'mysong_edit'
        context.user_data['step'] = 'waiting_for_audio'
        await query.edit_message_text(
            "🎵 **تعديل أغنية موجودة**\n\n"
            "📤 أرسل لي الآن الملف الصوتي (MP3) الذي تريد تعديل اسمه وإضافة صورة له.\n\n"
            "⚠️ الحد الأقصى للحجم: 70MB"
        )
    
    elif data == "mysong_extract":
        context.user_data.clear()
        context.user_data['mode'] = 'mysong_extract'
        context.user_data['step'] = 'waiting_for_video'
        await query.edit_message_text(
            "🎬 **استخراج صوت من فيديو + إضافة صورة**\n\n"
            "📤 أرسل لي الآن ملف الفيديو (MP4) لاستخراج الصوت منه، ثم سنضيف الاسم والصورة.\n\n"
            "⚠️ الحد الأقصى للحجم: 70MB"
        )
    
    elif data == "mysong_new":
        context.user_data.clear()
        context.user_data['mode'] = 'mysong_new'
        context.user_data['step'] = 'waiting_for_audio'
        await query.edit_message_text(
            "🆕 **رفع ملف صوتي جديد + صورة**\n\n"
            "📤 أرسل لي الآن الملف الصوتي (MP3) وسأطلب منك الاسم والفنان والصورة.\n\n"
            "⚠️ الحد الأقصى للحجم: 70MB"
        )
    
    # ===== أزرار اختيار الجودة (للوضع العادي) =====
    elif data.startswith("q_"):
        parts = data.split("_")
        quality = parts[1] + "k"
        action = parts[2]
        context.user_data['selected_quality'] = quality
        context.user_data['action_type'] = action
        
        if action == "edit":
            msg = "🎵 أرسل الآن الملف الصوتي (MP3) لتعديله:"
        else:
            msg = "🎬 أرسل الآن ملف الفيديو (MP4) لاستخراج الصوت منه:"
        
        await query.edit_message_text(f"✅ تم اختيار جودة {quality}.\n\n{msg}")
    
    elif data == "cancel_action":
        context.user_data.clear()
        await query.edit_message_text("❌ تم إلغاء العملية.")
    
    # ===== أزرار الإحصائيات =====
    elif data == "my_stats":
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        files_count = conn.execute(
            "SELECT COUNT(*) FROM files WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        conn.close()
        
        await query.edit_message_text(
            f"📊 **إحصائياتك الشخصية**\n\n"
            f"✅ عدد الأغاني التي قمت بمعالجتها: {files_count}\n"
            f"📅 تاريخ الانضمام: {context.user_data.get('join_date', 'غير معروف')}"
        )

# ============================================
# معالج الملفات (الصوت والفيديو) - لوضع mysong
# ============================================
async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): 
        return
    
    user_id = update.effective_user.id
    mode = context.user_data.get('mode')
    step = context.user_data.get('step')
    
    # ===== إذا كنا في وضع mysong =====
    if mode and step:
        # استقبال الملف الصوتي
        if step == 'waiting_for_audio' and mode in ['mysong_edit', 'mysong_new']:
            file_obj = None
            if update.message.audio:
                file_obj = update.message.audio
            elif update.message.document:
                doc = update.message.document
                if doc.mime_type == 'audio/mpeg' or doc.file_name.endswith('.mp3'):
                    file_obj = doc
            
            if not file_obj:
                await update.message.reply_text("❌ من فضلك أرسل ملف صوتي بصيغة MP3")
                return
            
            if file_obj.file_size > MAX_FILE_SIZE:
                await update.message.reply_text(f"❌ حجم الملف كبير جداً (الحد الأقصى 70MB). حجم ملفك: {file_obj.file_size // (1024*1024)}MB")
                return
            
            wait_msg = await update.message.reply_text("⏳ جاري تحميل الملف الصوتي...")
            tg_file = await file_obj.get_file()
            audio_path = f"audio_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
            await tg_file.download_to_drive(audio_path)
            
            context.user_data['audio_path'] = audio_path
            context.user_data['step'] = 'waiting_for_title'
            await wait_msg.edit_text("📝 أرسل الآن **اسم الأغنية**:")
            return
        
        # استقبال ملف الفيديو واستخراج الصوت
        elif step == 'waiting_for_video' and mode == 'mysong_extract':
            if not update.message.video:
                await update.message.reply_text("❌ من فضلك أرسل ملف فيديو (MP4)")
                return
            
            file_obj = update.message.video
            if file_obj.file_size > MAX_FILE_SIZE:
                await update.message.reply_text(f"❌ حجم الملف كبير جداً (الحد الأقصى 70MB)")
                return
            
            wait_msg = await update.message.reply_text("⏳ جاري تحميل الفيديو واستخراج الصوت...")
            tg_file = await file_obj.get_file()
            video_path = f"video_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
            await tg_file.download_to_drive(video_path)
            
            # استخراج الصوت بجودة 192k افتراضياً لوضع mysong
            audio_path = f"extracted_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
            
            cmd = [
                "ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame",
                "-ac", "2", "-b:a", "192k", audio_path, "-y"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.wait()
            
            # حذف الفيديو بعد الاستخراج
            if os.path.exists(video_path):
                os.remove(video_path)
            
            if process.returncode != 0:
                await wait_msg.edit_text("❌ حدث خطأ أثناء استخراج الصوت. تأكد من أن الملف فيديو صالح.")
                return
            
            context.user_data['audio_path'] = audio_path
            context.user_data['step'] = 'waiting_for_title'
            await wait_msg.edit_text("✅ تم استخراج الصوت بنجاح!\n\n📝 أرسل الآن **اسم الأغنية**:")
            return
        
        else:
            # المستخدم أرسل شيئاً لا ننتظره
            return
    
    # ===== الوضع العادي (للتعديل السريع بدون صورة مخصصة) =====
    action_type = context.user_data.get('action_type')
    quality = context.user_data.get('selected_quality', '192k')
    
    if not action_type:
        # ليس في أي وضع - تجاهل
        return
    
    # التحقق من نوع الملف
    file_obj = None
    if action_type == "edit":
        if update.message.audio:
            file_obj = update.message.audio
        elif update.message.document and update.message.document.mime_type == 'audio/mpeg':
            file_obj = update.message.document
    elif action_type == "extract" and update.message.video:
        file_obj = update.message.video
    
    if not file_obj:
        await update.message.reply_text("❌ الملف المرسل لا يتوافق مع العملية المختارة.")
        return
    
    if file_obj.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("❌ حجم الملف كبير جداً (الحد الأقصى 70MB).")
        return
    
    wait_msg = await update.message.reply_text("⏳ جاري التحميل والمعالجة...")
    
    tg_file = await file_obj.get_file()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    input_path = f"input_{user_id}_{timestamp}"
    output_path = f"output_{user_id}_{timestamp}.mp3"
    
    await tg_file.download_to_drive(input_path)
    
    # تشغيل FFmpeg لتحويل MP3
    cmd = [
        "ffmpeg", "-i", input_path, "-vn", "-acodec", "libmp3lame",
        "-ac", "2", "-b:a", quality, output_path, "-y"
    ]
    
    process = subprocess.run(cmd, capture_output=True)
    
    if os.path.exists(input_path):
        os.remove(input_path)
    
    if process.returncode != 0:
        await wait_msg.edit_text("❌ حدث خطأ أثناء المعالجة.")
        context.user_data.clear()
        return
    
    context.user_data["file_path"] = output_path
    context.user_data["step"] = "title"
    await wait_msg.edit_text("📝 تمت المعالجة! الآن أرسل **اسم الأغنية**:")

# ============================================
# معالج الصور (للأغاني المخصصة)
# ============================================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_maintenance(update, context): 
        return
    
    user_id = update.effective_user.id
    
    # التحقق من أننا في وضع mysong وننتظر صورة
    if context.user_data.get('mode') and context.user_data.get('step') == 'waiting_for_cover':
        
        wait_msg = await update.message.reply_text("🖼️ جاري معالجة الصورة ودمجها مع الأغنية...")
        
        # تحميل الصورة
        cover_path = f"cover_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # معالجة الصورة المرسلة كـ Photo
        if update.message.photo:
            photo = update.message.photo[-1]  # أفضل جودة
            tg_photo = await photo.get_file()
            cover_path += ".jpg"
            await tg_photo.download_to_drive(cover_path)
        
        # معالجة الصورة المرسلة كـ Document
        elif update.message.document:
            document = update.message.document
            mime_type = document.mime_type or ""
            file_name = document.file_name or ""
            
            if not (mime_type.startswith('image/') or file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))):
                await wait_msg.edit_text("❌ الملف المرسل ليس صورة. أرسل صورة بصيغة JPG أو PNG.")
                return
            
            tg_doc = await document.get_file()
            
            if file_name.lower().endswith('.png') or 'png' in mime_type:
                cover_path += ".png"
            elif file_name.lower().endswith('.webp') or 'webp' in mime_type:
                cover_path += ".webp"
            else:
                cover_path += ".jpg"
            
            await tg_doc.download_to_drive(cover_path)
        
        else:
            await wait_msg.edit_text("❌ لم ترسل صورة. أرسل صورة من فضلك.")
            return
        
        # الحصول على بيانات الأغنية
        audio_path = context.user_data.get('audio_path')
        title = context.user_data.get('title', 'غير معروف')
        artist = context.user_data.get('artist', 'غير معروف')
        
        if not audio_path or not os.path.exists(audio_path):
            await wait_msg.edit_text("❌ حدث خطأ: الملف الصوتي غير موجود")
            if os.path.exists(cover_path):
                os.remove(cover_path)
            context.user_data.clear()
            return
        
        try:
            # إضافة العلامات ID3
            try:
                audio = ID3(audio_path)
            except MutagenError:
                audio = ID3()
            
            audio["TIT2"] = TIT2(encoding=3, text=title)
            audio["TPE1"] = TPE1(encoding=3, text=artist)
            
            # تحديد نوع MIME
            if cover_path.endswith('.png'):
                mime_type = "image/png"
            elif cover_path.endswith('.webp'):
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"
            
            # إضافة الصورة
            with open(cover_path, "rb") as img:
                if "APIC" in audio:
                    del audio["APIC"]
                audio["APIC"] = APIC(
                    encoding=3, 
                    mime=mime_type, 
                    type=3, 
                    desc="Cover", 
                    data=img.read()
                )
            
            audio.save(audio_path, v2_version=3)
            
            # إرسال الملف النهائي
            with open(audio_path, "rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    title=title,
                    performer=artist,
                    caption="✅ تم إنشاء الأغنية بنجاح!"
                )
            
            # تسجيل في قاعدة البيانات
            add_file_record(user_id, title, artist)
            
            await wait_msg.delete()
            
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
        
        # تنظيف الملفات المؤقتة
        for file in [audio_path, cover_path]:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass
        
        context.user_data.clear()
        return
    
    else:
        await update.message.reply_text("❌ لست في وضع إضافة صورة حالياً. اختر '🖼️ إنشاء أغنية كاملة' أولاً.")

# ============================================
# معالج النصوص (معدل مع زر تشغيل البوت)
# ============================================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id

    # ===== الإذاعة للأدمن =====
    if context.user_data.get('admin_step') == 'broadcasting':
        if user_id != OWNER_ID:
            context.user_data['admin_step'] = None
            return
        
        conn = sqlite3.connect(DB_FILE)
        users = conn.execute("SELECT user_id FROM users").fetchall()
        conn.close()
        
        success_count = 0
        for u in users:
            try: 
                await context.bot.send_message(chat_id=u[0], text=user_text)
                success_count += 1
            except: 
                pass
        
        context.user_data['admin_step'] = None
        await update.message.reply_text(f"✅ تمت الإذاعة بنجاح لـ {success_count} مستخدم.")
        return

    # ===== أزرار القائمة الرئيسية (معدلة مع زر تشغيل البوت) =====
    
    # زر تشغيل البوت
    if user_text == "▶️ تشغيل البوت":
        await start_handler(update, context)
        return
    
    # زر تعديل الأغاني
    elif user_text == "🎵 تعديل الأغنية":
        from keyboards import quality_keyboard
        await update.message.reply_text("اختر الجودة المطلوبة للتعديل:", reply_markup=quality_keyboard("edit"))
        return
    
    # زر استخراج من الفيديو
    elif user_text == "🎬 استخراج صوت من فيديو":
        from keyboards import quality_keyboard
        await update.message.reply_text("اختر الجودة المطلوبة للاستخراج:", reply_markup=quality_keyboard("extract"))
        return
    
    # زر أغنيتي (القائمة المتكاملة)
    elif user_text == "🖼️ إنشاء أغنية كاملة (اسم + صورة + صوت)":
        from keyboards import my_song_menu_keyboard
        await update.message.reply_text(
            "🖼️ **قائمة أغنيتي المتكاملة**\n\n"
            "اختر ما تريد فعله:",
            reply_markup=my_song_menu_keyboard()
        )
        return
    
    # زر الإحصائيات
    elif user_text == "📊 إحصائياتي":
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        files_count = conn.execute(
            "SELECT COUNT(*) FROM files WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        conn.close()
        
        await update.message.reply_text(
            f"📊 **إحصائياتك الشخصية**\n\n"
            f"✅ عدد الأغاني التي تمت معالجتها: {files_count}\n\n"
            f"💡 استخدم البوت لمعالجة المزيد من الأغاني!"
        )
        return
    
    # زر لوحة التحكم
    elif user_text == "🛠 لوحة التحكم":
        if user_id == OWNER_ID:
            from admin_panel import panel_handler
            await panel_handler(update, context)
        else:
            await update.message.reply_text("❌ هذه الخاصية متاحة للمطور فقط.")
        return

    # ===== معالج وضع أغنيتي (إدخال النصوص) =====
    if context.user_data.get('mode'):
        step = context.user_data.get('step')
        
        # استقبال اسم الأغنية
        if step == 'waiting_for_title':
            if len(user_text) > 100:
                await update.message.reply_text("❌ اسم الأغنية طويل جداً (الحد الأقصى 100 حرف).")
                return
            context.user_data['title'] = user_text
            context.user_data['step'] = 'waiting_for_artist'
            await update.message.reply_text("🎤 أرسل الآن **اسم الفنان**:")
            return
        
        # استقبال اسم الفنان
        elif step == 'waiting_for_artist':
            if len(user_text) > 100:
                await update.message.reply_text("❌ اسم الفنان طويل جداً (الحد الأقصى 100 حرف).")
                return
            context.user_data['artist'] = user_text
            context.user_data['step'] = 'waiting_for_cover'
            await update.message.reply_text(
                "🖼️ **أرسل الآن الصورة** التي تريد استخدامها كغلاف للأغنية\n"
                "(JPG أو PNG)"
            )
            return
        
        # إذا كان ينتظر صورة وأرسل نص
        elif step == 'waiting_for_cover':
            await update.message.reply_text("❌ أنا في انتظار صورة وليس نص. أرسل صورة من فضلك.")
            return

    # ===== إكمال عملية التعديل القديمة =====
    if "file_path" in context.user_data:
        step = context.user_data.get("step")
        file_path = context.user_data["file_path"]

        if step == "title":
            context.user_data["title"] = user_text
            context.user_data["step"] = "artist"
            await update.message.reply_text("🎤 الآن أرسل (اسم الفنان):")
        
        elif step == "artist":
            title = context.user_data["title"]
            artist = user_text
            
            try:
                audio = ID3(file_path)
            except:
                audio = ID3()
            
            audio["TIT2"] = TIT2(encoding=3, text=title)
            audio["TPE1"] = TPE1(encoding=3, text=artist)
            
            cover = await get_channel_cover(context)
            if cover:
                with open(cover, "rb") as img:
                    audio["APIC"] = APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=img.read())
            audio.save(file_path)

            with open(file_path, "rb") as f:
                await update.message.reply_audio(audio=f, title=title, performer=artist)

            # تسجيل العملية
            conn = sqlite3.connect(DB_FILE)
            conn.execute(
                "INSERT INTO files (user_id, title, artist, date) VALUES (?, ?, ?, ?)",
                (user_id, title, artist, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            conn.close()

            if os.path.exists(file_path): os.remove(file_path)
            context.user_data.clear()
