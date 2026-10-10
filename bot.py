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

# إعداد الروابط الافتراضية وحالة الاشتراك (رابط التليجرام الخاص بك)
default_links = {
    "telegram": "https://t.me/+v0b4FUPcNRpjNzFk",
    "wa_channel": "",
    "wa_group": "",
    "fb_group": "",
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

# دالة لإنشاء أزرار الاشتراك بناءً على الروابط المتاحة
def get_subscription_keyboard():
    keyboard = []
    
    link_mapping = [
        ("telegram", "📢 قناة التليجرام"),
        ("wa_channel", "💬 قناة الواتساب"),
        ("wa_group", "👥 جروب الواتساب"),
        ("fb_group", "🌐 جروب الفيسبوك")
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
            "للاستمرار واستخدام البوت، نرجو منك الانضمام إلى قناتنا أولاً، ثم اضغط على زر (تحقق من الاشتراك):",
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
        [InlineKeyboardButton("🔗 تعديل الروابط", callback_data="admin_links_menu")],
        [InlineKeyboardButton("➕ إضافة حلقات جديدة", callback_data="admin_add_ep_guide")],
        [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_text = (
        "🎛️ أهلاً بك في لوحة تحكم الأدمن:\n\n"
        "يمكنك التحكم في الروابط، الحالة، والحلقات بكل مرونة من الأزرار أدناه:"
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
        
        keyboard = [
            [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
            [InlineKeyboardButton("🔗 تعديل الروابط", callback_data="admin_links_menu")],
            [InlineKeyboardButton("➕ إضافة حلقات جديدة", callback_data="admin_add_ep_guide")],
            [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.message.reply_text(f"تم تغيير حالة الاشتراك الإجباري لتصبح: {status_text} 👍")
        return

    elif data == "admin_links_menu":
        if not is_admin(user_id):
            return
        keyboard = [
            [InlineKeyboardButton("📢 تعديل رابط التليجرام", callback_data="edit_link_telegram")],
            [InlineKeyboardButton("💬 تعديل قناة الواتساب", callback_data="edit_link_wa_channel")],
            [InlineKeyboardButton("👥 تعديل جروب الواتساب", callback_data="edit_link_wa_group")],
            [InlineKeyboardButton("🌐 تعديل جروب الفيسبوك", callback_data="edit_link_fb_group")],
            [InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")]
        ]
        await query.message.edit_text("🔗 **اختر المنصة التي تريد وضع رابطها الخارجي:**", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("edit_link_"):
        if not is_admin(user_id):
            return
        link_type = data.replace("edit_link_", "")
        context.user_data['waiting_for_link'] = link_type
        
        await query.message.reply_text(
            "أرسل الآن الرابط الخارجي الجديد في رسالة:\n"
            "*(ملاحظة: إذا أردت حذف الرابط وعدم إظهار الزر نهائياً، أرسل كلمة `حذف`)*"
        )
        return

    elif data == "admin_add_ep_guide":
        if not is_admin(user_id):
            return
        guide_text = (
            "➕ **طريقة إضافة حلقات جديدة بكل سهولة:**\n\n"
            "فقط قم بكتابة هذا الأمر مع اسم القسم:\n"
            "`/upload [اسم_القسم]`\n"
            "ثم **قم بالرد على فيديو الحلقة** مباشرة وسيتم حفظها بشكل دائم ولن تُحذف أبداً.\n\n"
            "📁 **أسماء الأقسام:**\n"
            "`db_classic`, `db_z`, `db_kai`, `db_super`, `db_super2`, `db_daima`, `db_heroes`, `db_gt`, `db_specials`, `db_movies`"
        )
        await query.message.reply_text(guide_text, parse_mode="Markdown")
        return

    elif data == "back_to_admin":
        if not is_admin(user_id):
            return
        force_sub_status = get_setting("force_sub")
        status_text = "🟢 مفعل" if force_sub_status == "on" else "🔴 معطل"
        
        keyboard = [
            [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
            [InlineKeyboardButton("🔗 تعديل الروابط", callback_data="admin_links_menu")],
            [InlineKeyboardButton("➕ إضافة حلقات جديدة", callback_data="admin_add_ep_guide")],
            [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
        ]
        await query.message.edit_text("🎛️ أهلاً بك في لوحة تحكم الأدمن:", reply_markup=InlineKeyboardMarkup(keyboard))
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

async def upload_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط. 🌸")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text("الاستخدام الصحيح:\nأرسل الأمر هكذا: `/upload db_z` ثم رد على الفيديو المراد حفظه بشكل دائم.")
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
                await update.message.reply_text(f"تم حفظ الحلقة رقم ({ep_number}) في القسم ({section}) بشكل دائم ولن تُحذف أبدًا! ✨")
            else:
                await update.message.reply_text("عذراً، لم أتمكن من العثور على رقم الحلقة في اسم الفيديو أو الوصف. تأكد من وجود رقمه في الوصف. 🌸")
        else:
            await update.message.reply_text("الرسالة التي رددت عليها ليست فيديو يا غالي. ⚠️")
    else:
        await update.message.reply_text("الرجاء الرد على رسالة الفيديو بالأمر الصحيح `/upload [اسم_القسم]` لحفظه بشكل دائم.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # استقبال الرابط الخارجي الجديد من الأدمن
    if is_admin(user_id) and 'waiting_for_link' in context.user_data:
        link_type = context.user_data.pop('waiting_for_link')
        
        if text.lower() in ["حذف", "empty", "none", "-"]:
            new_link = ""
            msg = "تم إزالة الرابط وإخفاء الزر بنجاح! ✨"
        else:
            new_link = text
            msg = f"تم حفظ الرابط الخارجي الجديد بنجاح! 🚀"
            
        update_setting(link_type, new_link)
        await update.message.reply_text(msg)
        return

    force_sub_status = get_setting("force_sub")
    
    if force_sub_status == "on" and not is_admin(user_id):
        reply_markup = get_subscription_keyboard()
        await update.message.reply_text(
            "أهلاً بك يا غالي! 😊\n"
            "للاستمرار واستخدام البوت، نرجو منك الانضمام إلى قناتنا أولاً، ثم اضغط على زر (تحقق من الاشتراك):",
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
    app.add_handler(CommandHandler("upload", upload_episode))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Telegram bot is running smoothly...")
    app.run_polling()

if __name__ == '__main__':
    main()
