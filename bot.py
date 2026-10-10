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
conn.commit()

# الروابط الرسمية المعتمدة فقط
WHATSAPP_GROUP = "https://chat.whatsapp.com/DzsReO7OkJ9HoMJ2nZRkn5?s=cl&p=a&mlu=4&ilr=4"
WHATSAPP_CHANNEL = "https://whatsapp.com/channel/0029VbEK4Yl7DAWqW7ixlW03"
TELEGRAM_CHANNEL = "https://t.me/+v0b4FUPcNRpjNzFk"
FACEBOOK_GROUP = "https://www.facebook.com/share/g/1CKJ1y9rxS/"

ADMIN_IDS = [7080361795]

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update)

async def show_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("🐉 الكلاسيكي", callback_data="db_classic"), InlineKeyboardButton("⚡ دراغون بول زد", callback_data="db_z")],
        [InlineKeyboardButton("⚔️ زد كاي", callback_data="db_kai"), InlineKeyboardButton("🔥 سوبر", callback_data="db_super")],
        [InlineKeyboardButton("🔥 سوبر 2", callback_data="db_super2"), InlineKeyboardButton("✨ دايما", callback_data="db_daima")],
        [InlineKeyboardButton("💫 هيروز", callback_data="db_heroes"), InlineKeyboardButton("🌀 جي تي", callback_data="db_gt")],
        [InlineKeyboardButton("⭐ الحلقات الخاصة", callback_data="db_specials"), InlineKeyboardButton("🎬 الأفلام", callback_data="db_movies")],
        [InlineKeyboardButton("💬 جروب الواتس", url=WHATSAPP_GROUP), InlineKeyboardButton("📢 قناة الواتس", url=WHATSAPP_CHANNEL)],
        [InlineKeyboardButton("📢 قناة التليجرام", url=TELEGRAM_CHANNEL), InlineKeyboardButton("🌐 جروب الفيسبوك", url=FACEBOOK_GROUP)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "مرحباً بك في بوت أنمي دراغون بول الرسمي!\n"
        "اختر القسم المطلوب لتصفح الحلقات، أو تواصل معنا عبر الروابط بالأسفل:"
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

    keyboard = [
        [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_text = (
        "🎛️ **لوحة تحكم الأدمن:**\n\n"
        "• لرفع حلقة: رد على الفيديو بـ `/upload [اسم_القسم]`"
    )
    await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "list_episodes":
        cursor.execute("SELECT section, ep_number FROM episodes ORDER BY section, CAST(ep_number AS INTEGER)")
        rows = cursor.fetchall()
        
        if not rows:
            await query.message.reply_text("⚠️ لا توجد أي حلقات مرفوعة حتى الآن.")
            return
            
        sections_dict = {}
        for section, ep_number in rows:
            if section not in sections_dict:
                sections_dict[section] = []
            sections_dict[section].append(ep_number)
            
        for section, eps in sections_dict.items():
            result_msg = f"📂 **القسم: `{section}`**\n" + " | ".join([f"الحلقة {ep}" for ep in eps])
            await query.message.reply_text(result_msg, parse_mode="Markdown")
        return

    if data.startswith("db_") or data in ["db_classic", "db_z", "db_kai", "db_super", "db_super2", "db_daima", "db_gt", "db_heroes", "db_movies", "db_specials"]:
        section = data
        context.user_data['selected_section'] = section
        
        await query.message.reply_text(
            "✅ تم اختيار القسم بنجاح.\n"
            "الرجاء إرسال رقم الحلقة المطلوبة الآن (مثال: 1 أو 5)
    :"
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
        if update.effective_chat.type == "private":
            await update.message.reply_text("الرجاء استخدام الأمر /start للبدء واختيار القسم أولاً.")

def main():
    TOKEN = "8911756458:AAE0fgUD-kxKI5Q34yuFG-NRBXd7icJn32c"
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("upload", upload_episode))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Telegram bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
        
