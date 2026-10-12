import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT,
    ep_number TEXT,
    title TEXT,
    file_id TEXT
)
''')

try:
    cursor.execute("ALTER TABLE episodes ADD COLUMN title TEXT")
    conn.commit()
except Exception:
    pass

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

default_links = {
    "telegram_1": "",
    "telegram_2": "",
    "whatsapp_1": "",
    "whatsapp_2": "",
    "facebook_1": "",
    "facebook_2": "",
    "youtube_1": "",
    "youtube_2": "",
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

def get_section_count(section_code):
    cursor.execute("SELECT COUNT(*) FROM episodes WHERE section = ?", (section_code,))
    row = cursor.fetchone()
    return row[0] if row else 0

def get_subscription_keyboard():
    keyboard = []
    link_mapping = [
        ("telegram_1", "📢 قناة التليجرام 1"),
        ("telegram_2", "📢 قناة التليجرام 2"),
        ("whatsapp_1", "💬 قناة الواتساب 1"),
        ("whatsapp_2", "💬 قناة الواتساب 2"),
        ("facebook_1", "🌐 جروب الفيسبوك 1"),
        ("facebook_2", "🌐 جروب الفيسبوك 2"),
        ("youtube_1", "📺 قناة اليوتيوب 1"),
        ("youtube_2", "📺 قناة اليوتيوب 2"),
    ]
    for key, text in link_mapping:
        link_val = get_setting(key)
        if link_val and link_val.strip() != "":
            keyboard.append([InlineKeyboardButton(text, url=link_val)])
    keyboard.append([InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    force_sub_status = get_setting("force_sub")
    
    if force_sub_status == "on" and user and not is_admin(user.id):
        reply_markup = get_subscription_keyboard()
        if len(reply_markup.inline_keyboard) == 1:
            await show_main_menu(update)
            return
        await update.message.reply_text(
            "أهلاً بك يا غالي! 😊\n"
            "للاستمرار واستخدام البوت، نرجو منك الانضمام إلى القنوات والروابط أولاً، ثم اضغط على زر (تحقق من الاشتراك):",
            reply_markup=reply_markup
        )
        return
    await show_main_menu(update)

async def show_main_menu(update: Update):
    c_classic = get_section_count("db_classic")
    c_kai1 = get_section_count("db_kai1")
    c_kai2 = get_section_count("db_kai2")
    c_super = get_section_count("db_super")
    c_gt = get_section_count("db_gt")
    c_daima = get_section_count("db_daima")
    c_heroes = get_section_count("db_heroes")
    c_super_remake = get_section_count("db_super_remake")
    c_specials = get_section_count("db_specials")
    c_movies = get_section_count("db_movies")

    keyboard = [
        [InlineKeyboardButton(f"🐉 الكلاسيكي ({c_classic})", callback_data="db_classic"), InlineKeyboardButton(f"⚡ كاي الأول ({c_kai1})", callback_data="db_kai1")],
        [InlineKeyboardButton(f"⚔️ زد كاي 2 ({c_kai2})", callback_data="db_kai2"), InlineKeyboardButton(f"🔥 سوبر ({c_super})", callback_data="db_super")],
        [InlineKeyboardButton(f"🌀 جي تي ({c_gt})", callback_data="db_gt"), InlineKeyboardButton(f"✨ دايما ({c_daima})", callback_data="db_daima")],
        [InlineKeyboardButton(f"💫 هيروز ({c_heroes})", callback_data="db_heroes"), InlineKeyboardButton(f"✨ سوبر ريمك ({c_super_remake})", callback_data="db_super_remake")],
        [InlineKeyboardButton(f"⭐ الحلقات الخاصة ({c_specials})", callback_data="db_specials"), InlineKeyboardButton(f"🎬 الأفلام ({c_movies})", callback_data="db_movies")],
        [InlineKeyboardButton("📖 معلومات الأقسام والحلقات المتوفرة", callback_data="bot_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        "مرحباً بك في بوت أنمي دراغون بول الرسمي! 🌟\n"
        "اختر القسم المطلوب من الأزرار بالأسفل لتصفح الحلقات بكل سهولة:"
    )
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup)

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
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    admin_text = "🎛️ أهلاً بك في لوحة تحكم الأدمن المباشرة:\n\nاختر ما تريد فعله من الأزرار بالأسفل:"
    if update.message:
        await update.message.reply_text(admin_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(admin_text, reply_markup=reply_markup)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    user_id = user.id if user else 0

    if data == "toggle_sub":
        if not is_admin(user_id):
            return
        current_status = get_setting("force_sub")
        new_status = "off" if current_status == "on" else "on"
        update_setting("force_sub", new_status)
        status_txt = "🟢 مفعل" if new_status == "on" else "🔴 معطل"
        
        keyboard = [
            [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_txt}", callback_data="toggle_sub")],
            [InlineKeyboardButton("➕ إضافة حلقات جديدة (اختر القسم)", callback_data="admin_sections_menu")],
            [InlineKeyboardButton("✏️ تعديل وإدارة أرقام والحلقات", callback_data="edit_episodes_menu")],
            [InlineKeyboardButton("👤 إضافة مطور / متحكم جديد", callback_data="add_admin_prompt")],
            [InlineKeyboardButton("🔗 إضافة وتعديل الروابط للمنصات", callback_data="admin_links_menu")],
            [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.message.reply_text(f"تم تغيير حالة الاشتراك الإجباري لتصبح: {status_txt} 👍")
        return

    elif data == "bot_info":
        sections = [
            ("db_classic", "الكلاسيكي"),
            ("db_kai1", "دراغون بول كاي - الجزء الأول"),
            ("db_kai2", "دراغون بول زد كاي - الجزء الثاني"),
            ("db_super", "دراغون بول سوبر"),
            ("db_gt", "دراغون بول جي تي"),
            ("db_daima", "دراغون بول دايما"),
            ("db_heroes", "سوبر دراغون بول هيروز"),
            ("db_super_remake", "سوبر ريمك"),
            ("db_specials", "الحلقات الخاصة"),
            ("db_movies", "الأفلام السينمائية")
        ]
        info_msg = "معلومات الأقسام وحالة الحلقات المتوفرة في البوت:\n\n"
        for code, name in sections:
            cnt = get_section_count(code)
            info_msg += f"• {name}: تم رفع {cnt} حلقة متوفرة ✅\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_main")]]
        await query.message.edit_text(info_msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data == "back_to_main":
        await show_main_menu(update)
        return

    elif data == "add_admin_prompt":
        if not is_admin(user_id):
            return
        context.user_data['waiting_for_new_admin'] = True
        await query.message.reply_text(
            "👤 **إضافة مطور أو متحكم جديد:**\n\n"
            "أرسل الآن (آي دي / ID) الشخص المراد إضافته كأدمن في رسالة جديدة:"
        )
        return

    elif data == "edit_episodes_menu":
        if not is_admin(user_id):
            return
        keyboard = [
            [InlineKeyboardButton("🗑️ حذف حلقة محددة", callback_data="delete_ep_prompt")],
            [InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")]
        ]
        await query.message.reply_text(
            "✏️ **تعديل وإدارة الحلقات:**\n\n"
            "اختر الإجراء المطلوب:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    elif data == "delete_ep_prompt":
        if not is_admin(user_id):
            return
        context.user_data['waiting_for_delete_ep'] = True
        await query.message.reply_text(
            "🗑️ **حذف حلقة:**\n\n"
            "أرسل اسم القسم ورقم الحلقة هكذا مثال:\n`db_super 5`\nأو رقم الحلقة مباشرة إذا كنت قد حددت القسم مسبقاً."
        )
        return

    elif data == "admin_sections_menu":
        if not is_admin(user_id):
            return
        c_classic = get_section_count("db_classic")
        c_kai1 = get_section_count("db_kai1")
        c_kai2 = get_section_count("db_kai2")
        c_super = get_section_count("db_super")
        c_gt = get_section_count("db_gt")
        c_daima = get_section_count("db_daima")
        c_heroes = get_section_count("db_heroes")
        c_super_remake = get_section_count("db_super_remake")
        c_specials = get_section_count("db_specials")
        c_movies = get_section_count("db_movies")
        
        keyboard = [
            [InlineKeyboardButton(f"🐉 الكلاسيكي ({c_classic})", callback_data="upload_sec_db_classic"), InlineKeyboardButton(f"⚡ كاي 1 ({c_kai1})", callback_data="upload_sec_db_kai1")],
            [InlineKeyboardButton(f"⚔️ زد كاي 2 ({c_kai2})", callback_data="upload_sec_db_kai2"), InlineKeyboardButton(f"🔥 سوبر ({c_super})", callback_data="upload_sec_db_super")],
            [InlineKeyboardButton(f"🌀 جي تي ({c_gt})", callback_data="upload_sec_db_gt"), InlineKeyboardButton(f"✨ دايما ({c_daima})", callback_data="upload_sec_db_daima")],
            [InlineKeyboardButton(f"💫 هيروز ({c_heroes})", callback_data="upload_sec_db_heroes"), InlineKeyboardButton(f"✨ ريمك ({c_super_remake})", callback_data="upload_sec_db_super_remake")],
            [InlineKeyboardButton(f"⭐ الخاصة ({c_specials})", callback_data="upload_sec_db_specials"), InlineKeyboardButton(f"🎬 الأفلام ({c_movies})", callback_data="upload_sec_db_movies")],
            [InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")]
        ]
        await query.message.edit_text("📂 **اختر القسم الذي تريد إضافة حلقات إليه:**", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("upload_sec_"):
        if not is_admin(user_id):
            return
        section_code = data.replace("upload_sec_", "")
        context.bot_data[f'admin_sec_{user_id}'] = section_code
        await query.message.reply_text(
            "✅ تم اختيار القسم بنجاح.\n\n"
            "الآن **أرسل الحلقات مباشرة (كفيديوهات أو ملفات)** ومعها العنوان والرقم وسيقوم البوت بحفظها تلقائياً! 🚀"
        )
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
        await query.message.edit_text("🔗 **اختر الرابط الذي تريد تعديله:**", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("edit_link_"):
        if not is_admin(user_id):
            return
        link_type = data.replace("edit_link_", "")
        context.user_data['waiting_for_link'] = link_type
        await query.message.reply_text(f"أرسل الآن الرابط الجديد لـ ({link_type}) في رسالة:\n*(أرسل `حذف` لإزالته)*")
        return

    elif data == "back_to_admin":
        if not is_admin(user_id):
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
        ]
        await query.message.edit_text("🎛️ أهلاً بك في لوحة تحكم الأدمن المباشرة:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data == "list_episodes":
        if not is_admin(user_id):
            return
        cursor.execute("SELECT section, ep_number, title FROM episodes ORDER BY section, CAST(ep_number AS INTEGER)")
        rows = cursor.fetchall()
        if not rows:
            await query.message.reply_text("لا توجد أي حلقات مرفوعة حتى الآن يا غالي. 🌸")
            return
        result_msg = "📋 **قائمة الحلقات المحفوظة دائمًا:**\n\n"
        current_section = ""
        for section, ep_number, title in rows:
            if section != current_section:
                current_section = section
                result_msg += f"\n📂 **القسم: `{section}`**\n"
            t_str = f" - {title}" if title else ""
            result_msg += f"• حلقة {ep_number}{t_str}\n"
        if len(result_msg) > 4000:
            for i in range(0, len(result_msg), 4000):
                await query.message.reply_text(result_msg[i:i+4000], parse_mode="Markdown")
        else:
            await query.message.reply_text(result_msg, parse_mode="Markdown")
        return

    elif data == "check_sub":
        await show_main_menu(update)
        return

    section = data
    context.user_data['selected_section'] = section
    await query.message.reply_text("تم اختيار القسم بنجاح! 🎯\nالرجاء إرسال رقم الحلقة المطلوبة الآن (مثال: 1 أو 5):")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.effective_user
    user_id = user.id if user else 0

    if is_admin(user_id) and context.user_data.get('waiting_for_new_admin') and update.message.text:
        text = update.message.text.strip()
        context.user_data.pop('waiting_for_new_admin', None)
        if text.isdigit():
            new_admin_id = int(text)
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (new_admin_id,))
            conn.commit()
            await update.message.reply_text(f"✅ تم إضافة الآي دي ({new_admin_id}) كمطور/متحكم جديد بنجاح! 🚀")
        else:
            await update.message.reply_text("⚠️ يرجى إرسال رقم الآي دي صحيحاً ومكوناً من أرقام فقط.")
        return

    if is_admin(user_id) and context.user_data.get('waiting_for_delete_ep') and update.message.text:
        text = update.message.text.strip()
        context.user_data.pop('waiting_for_delete_ep', None)
        parts = text.split()
        if len(parts) == 2:
            sec, ep = parts[0], parts[1]
            cursor.execute("DELETE FROM episodes WHERE section = ? AND ep_number = ?", (sec, ep))
            conn.commit()
            await update.message.reply_text(f"🗑️ تم حذف الحلقة ({ep}) من القسم ({sec}) بنجاح.")
        else:
            await update.message.reply_text("⚠️ الصيغة غير صحيحة. أرسل هكذا مثلاً: `db_super 5`")
        return

    if is_admin(user_id) and 'waiting_for_link' in context.user_data and update.message.text:
        text = update.message.text.strip()
        link_type = context.user_data.pop('waiting_for_link')
        new_link = "" if text.lower() in ["حذف", "empty", "none", "-"] else text
        update_setting(link_type, new_link)
        await update.message.reply_text(f"تم تحديث رابط ({link_type}) بنجاح! 🚀")
        return

    if is_admin(user_id) and f'admin_sec_{user_id}' in context.bot_data:
        media_file = update.message.video or update.message.document
        if media_file:
            section = context.bot_data[f'admin_sec_{user_id}']
            file_id = media_file.file_id
            caption = update.message.caption or media_file.file_name or ""
            
            numbers = re.findall(r'\d+', caption)
            if numbers:
                ep_number = numbers[0]
                raw_title = caption
                for num in numbers:
                    raw_title = raw_title.replace(num, "")
                title = raw_title.replace(".mp4", "").replace(".mkv", "").replace("-", "").replace("_", " ").strip()
                
                cursor.execute("SELECT id FROM episodes WHERE section = ? AND ep_number = ?", (section, ep_number))
                row = cursor.fetchone()
                if not row:
                    cursor.execute("INSERT INTO episodes (section, ep_number, title, file_id) VALUES (?, ?, ?, ?)", (section, ep_number, title, file_id))
                    conn.commit()
                    await update.message.reply_text(f"✅ تم حفظ الحلقة ({ep_number}) بالعنوان ({title if title else 'بدون عنوان'}) تلقائياً!")
                else:
                    cursor.execute("UPDATE episodes SET title = ?, file_id = ? WHERE section = ? AND ep_number = ?", (title, file_id, section, ep_number))
                    conn.commit()
                    await update.message.reply_text(f"🔄 تم تحديث الحلقة ({ep_number}) وعنوانها بنجاح!")
            else:
                await update.message.reply_text("⚠️ لم يتم العثور على رقم في اسم أو وصف الملف لكي يتم استخراجه وحفظه تلقائياً.")
            return

    if not update.message.text:
        return
        
    text = update.message.text.strip()
    force_sub_status = get_setting("force_sub")
    
    if force_sub_status == "on" and not is_admin(user_id):
        reply_markup = get_subscription_keyboard()
        if len(reply_markup.inline_keyboard) == 1:
            await show_main_menu(update)
            return
        await update.message.reply_text(
            "أهلاً بك يا غالي! 😊\n"
            "للاستمرار واستخدام البوت، نرجو منك الانضمام إلى القنوات والروابط أولاً، ثم اضغط على زر (تحقق من الاشتراك):",
            reply_markup=reply_markup
        )
        return
    
    if 'selected_section' in context.user_data:
        section = context.user_data['selected_section']
        cursor.execute("SELECT file_id, title FROM episodes WHERE section = ? AND ep_number = ?", (section, text))
        row = cursor.fetchone()
        if row:
            file_id, title = row[0], row[1]
            title_str = f" - {title}" if title else ""
            await update.message.reply_video(video=file_id, caption=f"🎬 الحلقة رقم ({text}){title_str} - متوفرة ✅")
        else:
            await update.message.reply_text(f"عذراً، الحلقة رقم ({text}) غير متوفرة في هذا القسم حالياً ❌. 🌸")
    else:
        if update.effective_chat.type in ["group", "supergroup"]:
            return
        await update.message.reply_text("أهلاً بك! يرجى استخدام الأمر /start للبدء واختيار القسم المناسب. 😊")

def main():
    TOKEN = "8911756458:AAEADtUnJ5pYSv5SshjjXuMUd4GA9TnAMYY"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))

    print("Telegram bot is running smoothly...")
    app.run_polling()

if __name__ == '__main__':
    main()
          
