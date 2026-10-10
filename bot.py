import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# الاتصال بقاعدة البيانات وحفظها بشكل دائم
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء جداول الحلقات والإعدادات إذا لم تكن موجودة
cursor.execute('''
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT,
    ep_number TEXT,
    file_id TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
''')
conn.commit()

# إعداد الروابط الافتراضية لجميع المنصات (قسمين لكل منصة) وحالة الاشتراك
default_links = {
    "telegram_1": "https://t.me/+v0b4FUPcNRpjNzFk",
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

# أرقام المشرفين المسموح لهم بإدارة البوت
ADMIN_IDS = [7080361795]

def is_admin(user_id):
    return user_id in ADMIN_IDS

# دالة لحساب عدد الحلقات في كل قسم
def get_section_count(section_code):
    cursor.execute("SELECT COUNT(*) FROM episodes WHERE section = ?", (section_code,))
    row = cursor.fetchone()
    return row[0] if row else 0

# دالة لإنشاء أزرار الاشتراك بناءً على الروابط المتاحة
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
    
    if force_sub_status == "on" and not is_admin(user.id):
        reply_markup = get_subscription_keyboard()
        await update.message.reply_text(
            "أهلاً بك يا غالي! 😊\n"
            "للاستمرار واستخدام البوت، نرجو منك الانضمام إلى القنوات والروابط أولاً، ثم اضغط على زر (تحقق من الاشتراك):",
            reply_markup=reply_markup
        )
        return

    await show_main_menu(update)

async def show_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("🐉 الكلاسيكي", callback_data="db_classic"), InlineKeyboardButton("⚡ دراغون بول زد", callback_data="db_z")],
        [InlineKeyboardButton("⚔️ زد كاي", callback_data="db_kai"), InlineKeyboardButton("🔥 سوبر", callback_data="db_super")],
        [InlineKeyboardButton("🔥 سوبر 2", callback_data="db_super2"), InlineKeyboardButton("✨ دايما", callback_data="db_daima")],
        [InlineKeyboardButton("💫 هيروز", callback_data="db_heroes"), InlineKeyboardButton("🌀 جي تي", callback_data="db_gt")],
        [InlineKeyboardButton("⭐ الحلقات الخاصة", callback_data="db_specials"), InlineKeyboardButton("🎬 الأفلام", callback_data="db_movies")]
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
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط. 🌸")
        return

    force_sub_status = get_setting("force_sub")
    status_text = "🟢 مفعل" if force_sub_status == "on" else "🔴 معطل"
    
    keyboard = [
        [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
        [InlineKeyboardButton("➕ إضافة حلقات جديدة (اختر القسم)", callback_data="admin_sections_menu")],
        [InlineKeyboardButton("🔗 إضافة وتعديل الروابط للمنصات", callback_data="admin_links_menu")],
        [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_text = (
        "🎛️ أهلاً بك في لوحة تحكم الأدمن المباشرة:\n\n"
        "اختر ما تريد فعله من الأزرار بالأسفل:"
    )
    await update.message.reply_text(admin_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "toggle_sub":
        if not is_admin(user_id):
            return
        current_status = get_setting("force_sub")
        new_status = "off" if current_status == "on" else "on"
        update_setting("force_sub", new_status)
        
        status_text = "🟢 مفعل" if new_status == "on" else "🔴 معطل"
        
        force_sub_status = get_setting("force_sub")
        status_txt = "🟢 مفعل" if force_sub_status == "on" else "🔴 معطل"
        
        keyboard = [
            [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_txt}", callback_data="toggle_sub")],
            [InlineKeyboardButton("➕ إضافة حلقات جديدة (اختر القسم)", callback_data="admin_sections_menu")],
            [InlineKeyboardButton("🔗 إضافة وتعديل الروابط للمنصات", callback_data="admin_links_menu")],
            [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.message.reply_text(f"تم تغيير حالة الاشتراك الإجباري لتصبح: {status_text} 👍")
        return

    elif data == "admin_sections_menu":
        if not is_admin(user_id):
            return
        
        c_classic = get_section_count("db_classic")
        c_z = get_section_count("db_z")
        c_kai = get_section_count("db_kai")
        c_super = get_section_count("db_super")
        c_super2 = get_section_count("db_super2")
        c_daima = get_section_count("db_daima")
        c_heroes = get_section_count("db_heroes")
        c_gt = get_section_count("db_gt")
        c_specials = get_section_count("db_specials")
        c_movies = get_section_count("db_movies")
        
        keyboard = [
            [InlineKeyboardButton(f"🐉 الكلاسيكي ({c_classic})", callback_data="upload_sec_db_classic"), InlineKeyboardButton(f"⚡ زد ({c_z})", callback_data="upload_sec_db_z")],
            [InlineKeyboardButton(f"⚔️ زد كاي ({c_kai})", callback_data="upload_sec_db_kai"), InlineKeyboardButton(f"🔥 سوبر ({c_super})", callback_data="upload_sec_db_super")],
            [InlineKeyboardButton(f"🔥 سوبر 2 ({c_super2})", callback_data="upload_sec_db_super2"), InlineKeyboardButton(f"✨ دايما ({c_daima})", callback_data="upload_sec_db_daima")],
            [InlineKeyboardButton(f"💫 هيروز ({c_heroes})", callback_data="upload_sec_db_heroes"), InlineKeyboardButton(f"🌀 جي تي ({c_gt})", callback_data="upload_sec_db_gt")],
            [InlineKeyboardButton(f"⭐ الحلقات الخاصة ({c_specials})", callback_data="upload_sec_db_specials"), InlineKeyboardButton(f"🎬 الأفلام ({c_movies})", callback_data="upload_sec_db_movies")],
            [InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")]
        ]
        await query.message.edit_text("📂 **اختر القسم الذي تريد إضافة حلقات إليه (يظهر عدد الحلقات بجانبه):**", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("upload_sec_"):
        if not is_admin(user_id):
            return
        section_code = data.replace("upload_sec_", "")
        context.user_data['admin_upload_section'] = section_code
        
        await query.message.reply_text(
            f"✅ تم اختيار القسم بنجاح.\n\n"
            "الآن **قم بالرد على رسالة الفيديو** في الشات لرفع وحفظ الحلقة في هذا القسم بشكل دائم ولن تُحذف أبدًا! ✨"
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
        await query.message.edit_text("🔗 **اختر الرابط الذي تريد تعديله أو إضافته:**", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("edit_link_"):
        if not is_admin(user_id):
            return
        link_type = data.replace("edit_link_", "")
        context.user_data['waiting_for_link'] = link_type
        
        await query.message.reply_text(
            f"أرسل الآن الرابط الجديد لـ ({link_type}) في رسالة:\n"
            "*(ملاحظة: إذا أردت حذف الرابط وإخفاء الزر، أرسل كلمة `حذف`)*"
        )
        return

    elif data == "back_to_admin":
        if not is_admin(user_id):
            return
        force_sub_status = get_setting("force_sub")
        status_text = "🟢 مفعل" if force_sub_status == "on" else "🔴 معطل"
        
        keyboard = [
            [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
            [InlineKeyboardButton("➕ إضافة حلقات جديدة (اختر القسم)", callback_data="admin_sections_menu")],
            [InlineKeyboardButton("🔗 إضافة وتعديل الروابط للمنصات", callback_data="admin_links_menu")],
            [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
        ]
        await query.message.edit_text("🎛️ أهلاً بك في لوحة تحكم الأدمن المباشرة:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data == "list_episodes":
        if not is_admin(user_id):
            return
        cursor.execute("SELECT section, ep_number FROM episodes ORDER BY section, CAST(ep_number AS INTEGER)")
        rows = cursor.fetchall()
        
        if not rows:
            await query.message.reply_text("لا توجد أي حلقات مرفوعة حتى الآن يا غالي. 🌸")
            return
            
        result_msg = "📋 **قائمة الحلقات المحفوظة دائمًا:**\n\n"
        current_section = ""
        for section, ep_number in rows:
            if section != current_section:
                current_section = section
                result_msg += f"\n📂 **القسم: `{section}`**\n"
            result_msg += f"• الحلقة: `{ep_number}`\n"
            
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
    
    await query.message.reply_text(
        "تم اختيار القسم بنجاح! 🎯\n"
        "الرجاء إرسال رقم الحلقة المطلوبة الآن (مثال: 1 أو 5):"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    user_id = update.effective_user.id

    # 1. إذا كان الأدمن يرسل رابطاً جديداً للمنصات
    if is_admin(user_id) and 'waiting_for_link' in context.user_data and update.message.text:
        text = update.message.text.strip()
        link_type = context.user_data.pop('waiting_for_link')
        
        if text.lower() in ["حذف", "empty", "none", "-"]:
            new_link = ""
            msg = f"تم إزالة رابط ({link_type}) وإخفاء زره بنجاح! ✨"
        else:
            new_link = text
            msg = f"تم حفظ رابط ({link_type}) بنجاح! 🚀"
            
        update_setting(link_type, new_link)
        await update.message.reply_text(msg)
        return

    # 2. إذا كان الأدمن يرفع حلقة بعد اختيار القسم من الأزرار ورد على فيديو
    if is_admin(user_id) and 'admin_upload_section' in context.user_data:
        section = context.user_data.pop('admin_upload_section')
        
        if update.message.reply_to_message and update.message.reply_to_message.video:
            replied = update.message.reply_to_message
            file_id = replied.video.file_id
            caption = replied.caption or replied.video.file_name or ""
            
            numbers = re.findall(r'\d+', caption)
            if numbers:
                ep_number = numbers[0]
                cursor.execute("INSERT INTO episodes (section, ep_number, file_id) VALUES (?, ?, ?)", (section, ep_number, file_id))
                conn.commit()
                await update.message.reply_text(f"تم حفظ الحلقة رقم ({ep_number}) في القسم ({section}) بشكل دائم ولن تُحذف أبدًا! ✨")
            else:
                await update.message.reply_text("عذراً، لم أتمكن من العثور على رقم الحلقة في اسم الفيديو أو الوصف. تأكد من وجود رقمه في الوصف. 🌸")
        else:
            await update.message.reply_text("⚠️ يجب عليك الرد على رسالة فيديو لكي يتم حفظه في القسم المحدد.")
        return

    if not update.message.text:
        return
        
    text = update.message.text.strip()
    force_sub_status = get_setting("force_sub")
    
    if force_sub_status == "on" and not is_admin(user_id):
        reply_markup = get_subscription_keyboard()
        await update.message.reply_text(
            "أهلاً بك يا غالي! 😊\n"
            "للاستمرار واستخدام البوت، نرجو منك الانضمام إلى القنوات والروابط أولاً، ثم اضغط على زر (تحقق من الاشتراك):",
            reply_markup=reply_markup
        )
        return
    
    if 'selected_section' in context.user_data:
        section = context.user_data['selected_section']
        
        cursor.execute("SELECT file_id FROM episodes WHERE section = ? AND ep_number = ?", (section, text))
        row = cursor.fetchone()
        
        if row:
            file_id = row[0]
            await update.message.reply_video(video=file_id, caption=f"🎬 الحلقة رقم ({text})")
        else:
            await update.message.reply_text(f"عذراً، الحلقة رقم ({text}) غير متوفرة في هذا القسم حالياً. 🌸")
    else:
        if update.effective_chat.type in ["group", "supergroup"]:
            return
        await update.message.reply_text("أهلاً بك! يرجى استخدام الأمر /start للبدء واختيار القسم المناسب. 😊")

def main():
    TOKEN = "8911756458:AAE0fgUD-kxKI5Q34yuFG-NRBXd7icJn32c"
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))

    print("Telegram bot is running smoothly...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
