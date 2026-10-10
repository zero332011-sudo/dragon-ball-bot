import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# الاتصال بقاعدة البيانات الخارجية database.db
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

# التأكد من وجود الجداول المطلوبة
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

# الروابط الافتراضية
default_links = {
    "telegram": "https://t.me/+v0b4FUPcNRpjNzFk",
    "wa_channel": "https://whatsapp.com/channel/0029VbEK4Yl7DAWqW7ixlW03",
    "wa_group": "https://chat.whatsapp.com/DzsReO7OkJ9HoMJ2nZRkn5?s=cl&p=a&mlu=4&ilr=4",
    "fb_group": "https://www.facebook.com/share/g/1CKJ1y9rxS/",
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

ADMIN_IDS = [7080361795]

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    force_sub_status = get_setting("force_sub")
    
    if force_sub_status == "on" and not is_admin(user.id):
        t_link = get_setting("telegram")
        wa_c_link = get_setting("wa_channel")
        wa_g_link = get_setting("wa_group")
        fb_g_link = get_setting("fb_group")
        
        keyboard = [
            [InlineKeyboardButton("📢 قناة التليجرام", url=t_link)],
            [InlineKeyboardButton("💬 قناة الواتساب", url=wa_c_link)],
            [InlineKeyboardButton("👥 جروب الواتساب", url=wa_g_link)],
            [InlineKeyboardButton("🌐 جروب الفيسبوك", url=fb_g_link)],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ عذراً، يجب عليك الانضمام إلى قنواتنا وجروباتنا أولاً لتتمكن من استخدام البوت:\n\n"
            "بعد الانضمام، اضغط على زر (تحقق من الاشتراك):",
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
        "مرحباً بك في بوت أنمي دراغون بول الرسمي!\n"
        "اختر القسم المطلوب من الأزرار بالأسفل لتصفح الحلقات:"
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
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرفين فقط.")
        return

    force_sub_status = get_setting("force_sub")
    status_text = "🟢 مفعل" if force_sub_status == "on" else "🔴 معطل"
    
    keyboard = [
        [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
        [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_text = (
        "🎛️ لوحة تحكم المطور والأدمن:\n\n"
        "• يمكنك تفعيل أو إيقاف الاشتراك الإجباري من الأزرار أدناه.\n"
        "• يمكنك عرض الحلقات ونسخها للنشر.\n\n"
        "🔗 **تحديث الروابط من داخل البوت:**\n"
        "• لتحديث تليجرام: `/set_link telegram [الرابط]`\n"
        "• لتحديث قناة واتساب: `/set_link wa_channel [الرابط]`\n"
        "• لتحديث جروب واتساب: `/set_link wa_group [الرابط]`\n"
        "• لتحديث فيسبوك: `/set_link fb_group [الرابط]`\n\n"
        "طريقة رفع الحلقات:\n"
        "`/upload [اسم_القسم]` ثم الرد على الفيديو."
    )
    await update.message.reply_text(admin_text, reply_markup=reply_markup)

async def set_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرفين فقط.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ الاستخدام الصحيح:\n"
            "/set_link telegram [الرابط]\n"
            "/set_link wa_channel [الرابط]\n"
            "/set_link wa_group [الرابط]\n"
            "/set_link fb_group [الرابط]"
        )
        return

    link_type = args[0]
    new_link = args[1]

    valid_types = ["telegram", "wa_channel", "wa_group", "fb_group"]
    if link_type not in valid_types:
        await update.message.reply_text("⚠️ نوع الرابط غير صحيح. الأنواع المتاحة: telegram, wa_channel, wa_group, fb_group")
        return

    update_setting(link_type, new_link)
    await update.message.reply_text(f"✅ تم تحديث رابط ({link_type}) بنجاح إلى:\n{new_link}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "toggle_sub":
        current_status = get_setting("force_sub")
        new_status = "off" if current_status == "on" else "on"
        update_setting("force_sub", new_status)
        
        status_text = "🟢 مفعل" if new_status == "on" else "🔴 معطل"
        
        keyboard = [
            [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
            [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.message.reply_text(f"⚙️ تم تغيير حالة الاشتراك الإجباري لتصبح: {status_text}")
        return

    elif data == "list_episodes":
        cursor.execute("SELECT section, ep_number FROM episodes ORDER BY section, CAST(ep_number AS INTEGER)")
        rows = cursor.fetchall()
        
        if not rows:
            await query.message.reply_text("⚠️ لا توجد أي حلقات مرفوعة حتى الآن في قاعدة البيانات.")
            return
            
        result_msg = "📋 **قائمة الحلقات المضافة (قابلة للنسخ والنشر):**\n\n"
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
        "✅ تم اختيار القسم بنجاح.\n"
        "الرجاء إرسال رقم الحلقة المطلوبة الآن (مثال: 1 أو 5):"
)
async def upload_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرفين فقط.")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text("الاستخدام الصحيح:\nأرسل الأمر مع اسم القسم هكذا: `/upload db_z` ثم رد على الفيديو.")
        return
    
    section = args[0]
    
    if update.message.reply_to_message:
        replied = update.message.reply_to_message
        
        if replied.video:
            file_id = replied.video.file_id
            caption = replied.caption or replied.video.file_name or ""
            
            numbers = re.findall(r'\d+', caption)
            if numbers:
                ep_number = numbers[0]
                cursor.execute("INSERT INTO episodes (section, ep_number, file_id) VALUES (?, ?, ?)", (section, ep_number, file_id))
                conn.commit()
                await update.message.reply_text(f"✨ تم حفظ الحلقة برقم ({ep_number}) في القسم ({section}) بشكل دائم بنجاح!")
            else:
                await update.message.reply_text("⚠️ لم يتم العثور على رقم في اسم أو وصف الفيديو. تأكد من أن اسم الفيديو يحتوي على رقمه.")
        else:
            await update.message.reply_text("⚠️ الرسالة التي رددت عليها ليست فيديو.")
    else:
        await update.message.reply_text("الرجاء الرد على رسالة الفيديو بالأمر الصحيح `/upload [اسم_القسم]` لحفظه.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user_id = update.effective_user.id
    force_sub_status = get_setting("force_sub")
    
    if force_sub_status == "on" and not is_admin(user_id):
        t_link = get_setting("telegram")
        wa_c_link = get_setting("wa_channel")
        wa_g_link = get_setting("wa_group")
        fb_g_link = get_setting("fb_group")
        
        keyboard = [
            [InlineKeyboardButton("📢 قناة التليجرام", url=t_link)],
            [InlineKeyboardButton("💬 قناة الواتساب", url=wa_c_link)],
            [InlineKeyboardButton("👥 جروب الواتساب", url=wa_g_link)],
            [InlineKeyboardButton("🌐 جروب الفيسبوك", url=fb_g_link)],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ يجب عليك الانضمام إلى قنواتنا وجروباتنا أولاً لاستخدام البوت:\n\n"
            "بعد الانضمام، اضغط على زر (تحقق من الاشتراك):",
            reply_markup=reply_markup
        )
        return

    text = update.message.text.strip()
    
    if 'selected_section' in context.user_data:
        section = context.user_data['selected_section']
        
        cursor.execute("SELECT file_id FROM episodes WHERE section = ? AND ep_number = ?", (section, text))
        row = cursor.fetchone()
        
        if row:
            file_id = row[0]
            await update.message.reply_video(video=file_id, caption=f"🎬 الحلقة رقم ({text})")
        else:
            await update.message.reply_text(f"⚠️ عذراً، الحلقة رقم ({text}) غير متوفرة في هذا القسم حالياً.")
    else:
        if update.effective_chat.type in ["group", "supergroup"]:
            return
        await update.message.reply_text("الرجاء استخدام الأمر /start للبدء واختيار القسم أولاً.")

def main():
    TOKEN = "8911756458:AAE0fgUD-kxKI5Q34yuFG-NRBXd7icJn32c"
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("set_link", set_link))
    app.add_handler(CommandHandler("upload", upload_episode))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Telegram bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
      
