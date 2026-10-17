import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS animes (
    id TEXT PRIMARY KEY,
    name_ar TEXT,
    name_en TEXT,
    image_id TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS sections (
    id TEXT PRIMARY KEY,
    anime_id TEXT,
    name_ar TEXT,
    name_en TEXT,
    image_id TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id TEXT,
    ep_number TEXT,
    file_id TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS episode_ranges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id TEXT,
    start_ep INTEGER,
    end_ep INTEGER,
    image_id TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
''')
conn.commit()

DEFAULT_ADMIN = 7080361795
cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (DEFAULT_ADMIN,))
conn.commit()

cursor.execute("INSERT OR IGNORE INTO animes (id, name_ar, name_en) VALUES (?, ?, ?)", 
               ("dragon_ball", "دراغون بول", "Dragon Ball"))
conn.commit()

default_sections = [
    ("db_classic", "dragon_ball", "الكلاسيكي", "Classic"),
    ("db_kai1", "dragon_ball", "كاي الأول", "Kai 1"),
    ("db_kai2", "dragon_ball", "زد كاي 2", "Z Kai 2"),
    ("db_super", "dragon_ball", "سوبر", "Super"),
    ("db_gt", "dragon_ball", "جي تي", "GT"),
    ("db_daima", "dragon_ball", "دايما", "Daima"),
    ("db_heroes", "dragon_ball", "هيروز", "Heroes"),
    ("db_super_remake", "dragon_ball", "سوبر ريمك", "Super Remake"),
    ("db_specials", "dragon_ball", "الحلقات الخاصة", "Specials"),
    ("db_movies", "dragon_ball", "الأفلام", "Movies")
]
for sec in default_sections:
    cursor.execute("INSERT OR IGNORE INTO sections (id, anime_id, name_ar, name_en) VALUES (?, ?, ?, ?)", sec)
conn.commit()

default_links = {
    "telegram_1": "", "telegram_2": "",
    "whatsapp_1": "", "whatsapp_2": "",
    "facebook_1": "", "facebook_2": "",
    "youtube_1": "", "youtube_2": "",
    "force_sub": "on"
}
for key, val in default_links.items():
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
conn.commit()

def get_setting(key):
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else ""

def update_setting(key, value):
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()

def is_admin(user_id):
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def get_section_count(section_id):
    cursor.execute("SELECT COUNT(*) FROM episodes WHERE section_id = ?", (section_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

def get_subscription_keyboard(lang="ar"):
    keyboard = []
    link_mapping = [
        ("telegram_1", "📢 Telegram Channel 1" if lang == "en" else "📢 قناة التليجرام 1"),
        ("telegram_2", "📢 Telegram Channel 2" if lang == "en" else "📢 قناة التليجرام 2"),
        ("whatsapp_1", "💬 WhatsApp Channel 1" if lang == "en" else "💬 قناة الواتساب 1"),
        ("whatsapp_2", "💬 WhatsApp Channel 2" if lang == "en" else "💬 قناة الواتساب 2"),
        ("facebook_1", "🌐 Facebook Group 1" if lang == "en" else "🌐 جروب الفيسبوك 1"),
        ("facebook_2", "🌐 Facebook Group 2" if lang == "en" else "🌐 جروب الفيسبوك 2"),
        ("youtube_1", "📺 YouTube Channel 1" if lang == "en" else "📺 قناة اليوتيوب 1"),
        ("youtube_2", "📺 YouTube Channel 2" if lang == "en" else "📺 قناة اليوتيوب 2"),
    ]
    for key, text in link_mapping:
        link_val = get_setting(key)
        if link_val and link_val.strip() != "":
            keyboard.append([InlineKeyboardButton(text, url=link_val)])
    check_text = "🔄 Check Subscription" if lang == "en" else "🔄 تحقق من الاشتراك"
    keyboard.append([InlineKeyboardButton(check_text, callback_data="check_sub")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    force_sub_status = get_setting("force_sub")
    
    if force_sub_status == "on" and user and not is_admin(user.id):
        lang = context.user_data.get('lang', 'ar')
        reply_markup = get_subscription_keyboard(lang)
        if len(reply_markup.inline_keyboard) == 1:
            await show_language_selection(update)
            return
        msg = ("Welcome! 😊\nPlease join the channels/links first, then click (Check Subscription):" 
               if lang == "en" else 
               "أهلاً بك يا غالي! 😊\nللاستمرار واستخدام البوت، نرجو منك الانضمام إلى القنوات والروابط أولاً، ثم اضغط على زر (تحقق من الاشتراك):")
        if update.message:
            await update.message.reply_text(msg, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text(msg, reply_markup=reply_markup)
        return
    await show_language_selection(update)

async def show_language_selection(update: Update):
    keyboard = [
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"), InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "اختر لغتك المفضلة / Please choose your preferred language:"
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

async def show_anime_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ar')
    cursor.execute("SELECT id, name_ar, name_en FROM animes")
    animes = cursor.fetchall()
    
    keyboard = []
    for anime in animes:
        a_id, n_ar, n_en = anime
        name = n_en if lang == "en" else n_ar
        keyboard.append([InlineKeyboardButton(f"🎬 {name}", callback_data=f"anime_{a_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Select the Anime:" if lang == "en" else "اختر الأنمي المطلوبة:"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

async def show_sections_menu(update: Update, anime_id: str, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = context.user_data.get('lang', 'ar')
    
    cursor.execute("SELECT id, name_ar, name_en FROM sections WHERE anime_id = ?", (anime_id,))
    sections = cursor.fetchall()
    
    keyboard = []
    row = []
    for sec in sections:
        s_id, s_ar, s_en = sec
        cnt = get_section_count(s_id)
        name = s_en if lang == "en" else s_ar
        row.append(InlineKeyboardButton(f"{name} ({cnt})", callback_data=f"sec_{s_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back" if lang == "en" else "🔙 رجوع", callback_data="back_to_animes")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Select the section:" if lang == "en" else "اختر القسم المطلوب:"
    
    try:
        await query.message.delete()
    except Exception:
        pass
    await query.message.reply_text(text, reply_markup=reply_markup)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        if update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط. 🌸")
        return

    force_sub_status = get_setting("force_sub")
    status_text = "🟢 مفعل" if force_sub_status == "on" else "🔴 معطل"
    
    keyboard = [
        [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
        [InlineKeyboardButton("➕ إضافة حلقات جديدة (اختر القسم)", callback_data="admin_sections_menu")],
        [InlineKeyboardButton("✏️ تعديل وإدارة أرقام والحلقات", callback_data="edit_episodes_menu")],
        [InlineKeyboardButton("👤 إضافة مطور / متحكم جديد", callback_data="add_admin_prompt")],
        [InlineKeyboardButton("🔗 إضافة وتعديل الروابط للمنصات", callback_data="admin_links_menu")],
        [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
        [InlineKeyboardButton("🎬 إضافة أنمي جديد", callback_data="add_anime_prompt")],
        [InlineKeyboardButton("📂 إضافة قسم جديد", callback_data="add_section_anime_choice")],
        [InlineKeyboardButton("✏️ تعديل اسم قسم", callback_data="edit_section_anime_choice")],
        [InlineKeyboardButton("🖼️ إضافة صورة لقسم أو لنطاق حلقات", callback_data="add_image_prompt")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🎛️ أهلاً بك في لوحة تحكم الأدمن المباشرة:\n\nاختر ما تريد فعله من الأزرار بالأسفل:"
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    user_id = user.id if user else 0

    if data.startswith("lang_"):
        lang = data.replace("lang_", "")
        context.user_data['lang'] = lang
        await show_anime_selection(update, context)
        return

    elif data == "back_to_animes":
        await show_anime_selection(update, context)
        return

    elif data.startswith("anime_"):
        anime_id = data.replace("anime_", "")
        context.user_data['selected_anime'] = anime_id
        await show_sections_menu(update, anime_id, context)
        return

    elif data.startswith("sec_"):
        section_id = data.replace("sec_", "")
        context.user_data['selected_section'] = section_id
        lang = context.user_data.get('lang', 'ar')
        
        cursor.execute("SELECT image_id FROM sections WHERE id = ?", (section_id,))
        row = cursor.fetchone()
        if row and row[0]:
            await query.message.reply_photo(photo=row[0], caption="📂 صورة القسم" if lang == "ar" else "📂 Section Image")
            
        await query.message.reply_text("الرجاء إرسال رقم الحلقة المطلوبة:" if lang == "ar" else "Please send the required episode number:")
        return

    elif data == "check_sub":
        await show_anime_selection(update, context)
        return

    elif data == "toggle_sub":
        if not is_admin(user_id):
            return
        current_status = get_setting("force_sub")
        new_status = "off" if current_status == "on" else "on"
        update_setting("force_sub", new_status)
        await admin_panel(update, context)
        return

    elif data == "admin_sections_menu":
        if not is_admin(user_id):
            return
        cursor.execute("SELECT id, name_ar FROM sections")
        sections = cursor.fetchall()
        keyboard = []
        for s_id, s_name in sections:
            cnt = get_section_count(s_id)
            keyboard.append([InlineKeyboardButton(f"{s_name} ({cnt})", callback_data=f"upload_sec_{s_id}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")])
        await query.message.edit_text("اختر القسم لرفع الحلقات:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("upload_sec_"):
        if not is_admin(user_id):
            return
        sec_id = data.replace("upload_sec_", "")
        context.bot_data[f'admin_sec_{user_id}'] = sec_id
        await query.message.reply_text("✅ تم اختيار القسم. أرسل الحلقات الآن (فيديو أو ملف) وسيتم استخراج رقمها تلقائياً بدون عنوان!")
        return

    elif data == "edit_episodes_menu":
        if not is_admin(user_id):
            return
        keyboard = [
            [InlineKeyboardButton("🗑️ حذف حلقة محددة", callback_data="delete_ep_prompt")],
            [InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")]
        ]
        await query.message.edit_text("✏️ **إدارة الحلقات:**", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data == "delete_ep_prompt":
        if not is_admin(user_id):
            return
        context.user_data['waiting_for_delete'] = True
        await query.message.reply_text("🗑️ أرسل معرف القسم ورقم الحلقة هكذا:\n`معرف_القسم رقم_الحلقة`")
        return

    elif data == "add_admin_prompt":
        if not is_admin(user_id):
            return
        context.user_data['waiting_for_new_admin'] = True
        await query.message.reply_text("👤 أرسل الآي دي (ID) الخاص بالمطور الجديد:")
        return

    elif data == "admin_links_menu":
        if not is_admin(user_id):
            return
        keyboard = [
            [InlineKeyboardButton("📢 تليجرام 1", callback_data="edit_link_telegram_1"), InlineKeyboardButton("📢 تليجرام 2", callback_data="edit_link_telegram_2")],
            [InlineKeyboardButton("💬 واتساب 1", callback_data="edit_link_whatsapp_1"), InlineKeyboardButton("💬 واتساب 2", callback_data="edit_link_whatsapp_2")],
            [InlineKeyboardButton("🌐 فيسبوك 1", callback_data="edit_link_facebook_1"), InlineKeyboardButton("🌐 فيسبوك 2", callback_data="edit_link_facebook_2")],
            [InlineKeyboardButton("📺 يوتيوب 1", callback_data="edit_link_youtube_1"), InlineKeyboardButton("📺 يوتيوب 2", callback_data="edit_link_youtube_2")],
            [InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")]
        ]
        await query.message.edit_text("🔗 اختر الرابط لتعديله:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("edit_link_"):
        if not is_admin(user_id):
            return
        link_type = data.replace("edit_link_", "")
        context.user_data['waiting_for_link'] = link_type
        await query.message.reply_text(f"أرسل الرابط الجديد لـ ({link_type}):\n*(أرسل `حذف` لإزالته)*")
        return

    elif data == "list_episodes":
        if not is_admin(user_id):
            return
        cursor.execute("SELECT section_id, ep_number FROM episodes ORDER BY section_id, CAST(ep_number AS INTEGER)")
        rows = cursor.fetchall()
        if not rows:
            await query.message.reply_text("لا توجد أي حلقات مرفوعة حتى الآن.")
            return
        result_msg = "📋 **قائمة الحلقات المحفوظة:**\n\n"
        curr_sec = ""
        for sec, ep in rows:
            if sec != curr_sec:
                curr_sec = sec
                result_msg += f"\n📂 **القسم: `{sec}`**\n"
            result_msg += f"• حلقة {ep}\n"
        await query.message.reply_text(result_msg[:4000], parse_mode="Markdown")
        return

    elif data == "add_anime_prompt":
        context.user_data['waiting_for_anime'] = True
        await query.message.reply_text("🎬 أرسل بيانات الأنمي الجديد:\n`معرف_الأنمي | الاسم بالعربي | الاسم بالانجلش`")
        return

    elif data == "add_section_anime_choice":
        if not is_admin(user_id):
            return
        cursor.execute("SELECT id, name_ar FROM animes")
        animes = cursor.fetchall()
        keyboard = []
        for a_id, a_name in animes:
            keyboard.append([InlineKeyboardButton(f"🎬 {a_name}", callback_data=f"add_sec_anime_{a_id}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")])
        await query.message.edit_text("📂 اختر الأنمي لإضافة القسم له:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("add_sec_anime_"):
        if not is_admin(user_id):
            return
        anime_id = data.replace("add_sec_anime_", "")
        context.user_data['target_anime_for_section'] = anime_id
        context.user_data['waiting_for_section_data'] = True
        await query.message.reply_text("أرسل بيانات القسم الجديد بالهيئة التالية:\n`معرف_القسم | الاسم بالعربي | الاسم بالانجلش`\n*(مثال: `db_name | اسم القسم | Section Name`)*")
        return

    elif data == "edit_section_anime_choice":
        if not is_admin(user_id):
            return
        cursor.execute("SELECT id, name_ar FROM animes")
        animes = cursor.fetchall()
        keyboard = []
        for a_id, a_name in animes:
            keyboard.append([InlineKeyboardButton(f"🎬 {a_name}", callback_data=f"edit_sec_anime_{a_id}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin")])
        await query.message.edit_text("✏️ اختر الأنمي لعرض أقسامه وتعديلها:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("edit_sec_anime_"):
        if not is_admin(user_id):
            return
        anime_id = data.replace("edit_sec_anime_", "")
        cursor.execute("SELECT id, name_ar FROM sections WHERE anime_id = ?", (anime_id,))
        sections = cursor.fetchall()
        keyboard = []
        for s_id, s_name in sections:
            keyboard.append([InlineKeyboardButton(f"📂 {s_name}", callback_data=f"edit_this_sec_{s_id}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="edit_section_anime_choice")])
        await query.message.edit_text("اختر القسم المراد تعديل اسمه:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("edit_this_sec_"):
        if not is_admin(user_id):
            return
        sec_id = data.replace("edit_this_sec_", "")
        context.user_data['target_section_to_edit'] = sec_id
        context.user_data['waiting_for_new_section_name'] = True
        await query.message.reply_text("✏️ أرسل الاسم الجديد للقسم بالهيئة التالية:\n`الاسم الجديد بالعربي | الاسم الجديد بالانجلش`")
        return

    elif data == "add_image_prompt":
        context.user_data['waiting_for_image_type'] = True
        await query.message.reply_text("🖼️ أرسل نوع الصورة:\nللقسم: `section | معرف_القسم`\nلنطاق حلقات: `range | معرف_القسم | من_رقم | إلى_رقم`")
        return

    elif data == "back_to_admin":
        if not is_admin(user_id):
            return
        await admin_panel(update, context)
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.effective_user
    user_id = user.id if user else 0
    text = update.message.text.strip() if update.message.text else ""

    if is_admin(user_id) and context.user_data.get('waiting_for_new_admin'):
        context.user_data.pop('waiting_for_new_admin', None)
        if text.isdigit():
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (int(text),))
            conn.commit()
            await update.message.reply_text("✅ تمت إضافة المطور الجديد بنجاح!")
        else:
            await update.message.reply_text("⚠️ يرجى إرسال أرقام صحيحة للآي دي.")
        return

    if is_admin(user_id) and 'waiting_for_link' in context.user_data:
        link_type = context.user_data.pop('waiting_for_link')
        new_l = "" if text.lower() in ["حذف", "empty", "none", "-"] else text
        update_setting(link_type, new_l)
        await update.message.reply_text("✅ تم تحديث الرابط بنجاح!")
        return

    if is_admin(user_id) and context.user_data.get('waiting_for_anime'):
        context.user_data.pop('waiting_for_anime', None)
        parts = [p.strip() for p in text.split('|')]
        if len(parts) == 3:
            cursor.execute("INSERT OR REPLACE INTO animes (id, name_ar, name_en) VALUES (?, ?, ?)", (parts[0], parts[1], parts[2]))
            conn.commit()
            await update.message.reply_text("✅ تم إضافة الأنمي بنجاح!")
        else:
            await update.message.reply_text("⚠️ صيغة غير صحيحة.")
        return

    if is_admin(user_id) and context.user_data.get('waiting_for_section_data'):
        anime_id = context.user_data.pop('target_anime_for_section', None)
        context.user_data.pop('waiting_for_section_data', None)
        parts = [p.strip() for p in text.split('|')]
        if len(parts) == 3 and anime_id:
            cursor.execute("INSERT OR REPLACE INTO sections (id, anime_id, name_ar, name_en) VALUES (?, ?, ?, ?)", (parts[0], anime_id, parts[1], parts[2]))
            conn.commit()
            await update.message.reply_text("✅ تم إضافة القسم بنجاح للأنمي المحدد!")
        else:
            await update.message.reply_text("⚠️ صيغة غير صحيحة.")
        return

    if is_admin(user_id) and context.user_data.get('waiting_for_new_section_name'):
        sec_id = context.user_data.pop('target_section_to_edit', None)
        context.user_data.pop('waiting_for_new_section_name', None)
        parts = [p.strip() for p in text.split('|')]
        if len(parts) == 2 and sec_id:
            cursor.execute("UPDATE sections SET name_ar = ?, name_en = ? WHERE id = ?", (parts[0], parts[1], sec_id))
            conn.commit()
            await update.message.reply_text("✅ تم تعديل اسم القسم بنجاح!")
        else:
            await update.message.reply_text("⚠️ صيغة غير صحيحة.")
        return

    if is_admin(user_id) and context.user_data.get('waiting_for_image_type'):
        context.user_data.pop('waiting_for_image_type', None)
        parts = [p.strip() for p in text.split('|')]
        context.user_data['image_target'] = parts
        await update.message.reply_text("📸 الآن أرسل الصورة المراد ربطها:")
        return

    if is_admin(user_id) and 'image_target' in context.user_data:
        photo = update.message.photo
        if photo:
            file_id = photo[-1].file_id
            target = context.user_data.pop('image_target')
            if target[0] == 'section':
                cursor.execute("UPDATE sections SET image_id = ? WHERE id = ?", (file_id, target[1]))
                conn.commit()
                await update.message.reply_text("✅ تمت إضافة صورة القسم بنجاح!")
            elif target[0] == 'range':
                cursor.execute("INSERT INTO episode_ranges (section_id, start_ep, end_ep, image_id) VALUES (?, ?, ?, ?)", 
                               (target[1], int(target[2]), int(target[3]), file_id))
                conn.commit()
                await update.message.reply_text("✅ تمت إضافة صورة نطاق الحلقات بنجاح!")
        return

    if is_admin(user_id) and context.user_data.get('waiting_for_delete'):
        context.user_data.pop('waiting_for_delete', None)
        parts = text.split()
        if len(parts) == 2:
            cursor.execute("DELETE FROM episodes WHERE section_id = ? AND ep_number = ?", (parts[0], parts[1]))
            conn.commit()
            await update.message.reply_text("🗑️ تم حذف الحلقة بنجاح.")
        else:
            await update.message.reply_text("⚠️ صيغة غير صحيحة.")
        return

    if is_admin(user_id) and f'admin_sec_{user_id}' in context.bot_data:
        media = update.message.video or update.message.document
        if media:
            sec_id = context.bot_data[f'admin_sec_{user_id}']
            file_id = media.file_id
            caption = update.message.caption or media.file_name or ""
            numbers = re.findall(r'\d+', caption)
            if numbers:
                ep_number = numbers[0]
                cursor.execute("INSERT OR REPLACE INTO episodes (section_id, ep_number, file_id) VALUES (?, ?, ?)", (sec_id, ep_number, file_id))
                conn.commit()
                await update.message.reply_text(f"✅ تم حفظ الحلقة رقم ({ep_number}) بنجاح بدون عنوان!")
            else:
                await update.message.reply_text("⚠️ لم يتم العثور على رقم الحلقة في الوصف أو الاسم.")
            return

    if 'selected_section' in context.user_data:
        sec_id = context.user_data['selected_section']
        cursor.execute("SELECT file_id FROM episodes WHERE section_id = ? AND ep_number = ?", (sec_id, text))
        row = cursor.fetchone()
        if row:
            file_id = row[0]
            ep_num_int = int(text) if text.isdigit() else 0
            cursor.execute("SELECT image_id FROM episode_ranges WHERE section_id = ? AND start_ep <= ? AND end_ep >= ?", (sec_id, ep_num_int, ep_num_int))
            range_row = cursor.fetchone()
            if range_row and range_row[0]:
                await update.message.reply_photo(photo=range_row[0], caption=f"🎬 الحلقة رقم ({text})")
            await update.message.reply_video(video=file_id, caption=f"🎬 الحلقة رقم ({text}) - متوفرة ✅")
        else:
            await update.message.reply_text(f"عذراً، الحلقة رقم ({text}) غير متوفرة حالياً ❌.")

def main():
    TOKEN = "8911756458:AAEADtUnJ5pYSv5SshjjXuMUd4GA9TnAMYY"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))

    print("Complete bot (old + new features) is running smoothly...")
    app.run_polling()

if __name__ == '__main__':
    main()
      
