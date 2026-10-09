import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجدول إذا لم يكن موجوداً
cursor.execute('''
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT,
    ep_number TEXT,
    file_id TEXT
)
''')
conn.commit()

# أرقام المشرفين المسموح لهم بالرفع وإدارة البوت
ADMIN_IDS = [7080361795]

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🐉 دراغون بول الكلاسيكي", callback_data="db_classic")],
        [InlineKeyboardButton("⚡ دراغون بول زد", callback_data="db_z")],
        [InlineKeyboardButton("⚔️ دراغون بول زد كاي", callback_data="db_kai")],
        [InlineKeyboardButton("🔥 دراغون بول سوبر", callback_data="db_super")],
        [InlineKeyboardButton("🔥 دراغون بول سوبر 2 (الإصدار الجديد)", callback_data="db_super2")],
        [InlineKeyboardButton("✨ دراغون بول دايما", callback_data="db_daima")],
        [InlineKeyboardButton("💫 سوبر دراغون بول هيروز", callback_data="db_heroes")],
        [InlineKeyboardButton("🌀 دراغون بول جي تي", callback_data="db_gt")],
        [InlineKeyboardButton("⭐ الحلقات الخاصة", callback_data="db_specials")],
        [InlineKeyboardButton("🎬 قائمة الأفلام", callback_data="db_movies")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"مرحباً بك يا {user.first_name} في بوت أنمي دراغون بول!\n"
        "اختر القسم الذي ترغب في تصفحه من الأزرار بالأسفل، ثم أرسل رقم الحلقة لعرضها:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرفين فقط.")
        return

    admin_text = (
        "🎛️ لوحة تحكم المشرف (الأدمن):\n\n"
        "طريقة الرفع الجماعي واستخراج رقم الحلقة تلقائياً:\n"
        "1. اكتب أمر القسم المطلوب مع كلمة upload مثل:\n"
        "`/upload db_z`\n"
        "2. قم بالرد على الفيديو (أو مجموعة الفيديوهات) التي تحتوي في اسمها أو وصفها على رقم الحلقة، وسيتم إضافتها وحفظها تلقائياً بالرقم المستخرج!\n\n"
        "أقسام الرفع المتاحة:\n"
        "• `db_classic` (الكلاسيكي)\n"
        "• `db_z` (زد)\n"
        "• `db_kai` (زد كاي)\n"
        "• `db_super` (سوبر)\n"
        "• `db_super2` (سوبر 2)\n"
        "• `db_daima` (دايما)\n"
        "• `db_heroes` (هيروز)\n"
        "• `db_gt` (جي تي)\n"
        "• `db_specials` (الحلقات الخاصة)\n"
        "• `db_movies` (الأفلام)"
    )
    await update.message.reply_text(admin_text)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    section = query.data
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
        await update.message.reply_text("الاستخدام الصحيح:\nأرسل الأمر مع اسم القسم هكذا: `/upload db_z` ثم رد على الفيديوهات.")
        return
    
    section = args[0]
    
    if update.message.reply_to_message:
        replied = update.message.reply_to_message
        
        if replied.video:
            file_id = replied.video.file_id
            caption = replied.caption or replied.video.file_name or ""
            
            # استخراج أول رقم يظهر في اسم أو وصف الفيديو تلقائياً
            numbers = re.findall(r'\d+', caption)
            if numbers:
                ep_number = numbers[0]
                cursor.execute("INSERT INTO episodes (section, ep_number, file_id) VALUES (?, ?, ?)", (section, ep_number, file_id))
                conn.commit()
                await update.message.reply_text(f"✨ تم حفظ الحلقة برقم ({ep_number}) في القسم ({section}) بنجاح!")
            else:
                await update.message.reply_text("⚠️ لم يتم العثور على رقم في اسم أو وصف الفيديو. تأكد من أن اسم الفيديو يحتوي على رقمه لتتم إضافته تلقائياً.")
        else:
            await update.message.reply_text("⚠️ الرسالة التي ردرت عليها ليست فيديو.")
    else:
        await update.message.reply_text("الرجاء الرد على رسالة الفيديو بالأمر الصحيح `/upload [اسم_القسم]` لحفظه في قاعدة البيانات.")

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
        if update.effective_chat.type in ["group", "supergroup"]:
            return
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
