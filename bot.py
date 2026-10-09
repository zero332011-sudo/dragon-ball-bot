import sqlite3
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

# أرقام المطورين أو المشرفين المسموح لهم بالرفع
ADMIN_IDS = [201032219184, 123456789] # أضف الأيدي الخاص بك هنا

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # دعم العمل في المحادثات الخاصة والجماعية
    chat = update.effective_chat
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🐉 دراغون بول الكلاسيكي", callback_data="db_classic"),
         InlineKeyboardButton("🔥 دراغون بول Z", callback_data="db_z")],
        [InlineKeyboardButton("⚡ دراغون بول كاي", callback_data="db_kai"),
         InlineKeyboardButton("⭐ دراغون بول سوبر", callback_data="db_super")],
        [InlineKeyboardButton("🎬 الأفلام والحلقات الخاصة", callback_data="db_movies")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"مرحباً بك يا {user.first_name} في بوت أنمي دراغون بول!\n"
        "اختر القسم المطلوب من الأزرار بالأسفل، ثم أرسل رقم الحلقة لعرضها:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    section = query.data
    context.user_data['selected_section'] = section
    
    await query.message.reply_text(
        f"✅ تم اختيار القسم بنجاح.\n"
        f"الرجاء إرسال **رقم الحلقة** المطلوبة الآن (مثال: 1 أو 5):"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # إذا ارسل المستخدم رقم حلقة وكان قد اختار قسم مسبقاً
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
        # إذا أرسل رسالة عادية ولم يحدد قسم
        if update.effective_chat.type in ["group", "supergroup"]:
            # في المجموعات يمكننا تجاهل الرسائل العادية التي ليست أوامر لتجنب الإزعاج
            return
        await update.message.reply_text("الرجاء استخدام الأمر /start للبدء واختيار القسم أولاً.")

# أمر لرفع الحلقات (خاص بالمشرفين فقط)
async def upload_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرفين فقط.")
        return

    # الطريقة: /upload [القسم] [رقم الحلقة] ويجب أن يكون مرفقاً بفيديو
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("الاستخدام الصحيح:\n`/upload db_z 1` (مع إرفاق الفيديو أو الـ file_id)")
        return
    
    section = args[0]
    ep_number = args[1]
    
    if update.message.reply_to_message and update.message.reply_to_message.video:
        file_id = update.message.reply_to_message.video.file_id
        
        cursor.execute("INSERT INTO episodes (section, ep_number, file_id) VALUES (?, ?, ?)", (section, ep_number, file_id))
        conn.commit()
        
        await update.message.reply_text(f"✨ تم حفظ الحلقة ({ep_number}) في القسم ({section}) بنجاح!")
    else:
        await update.message.reply_text("الرجاء الرد على رسالة الفيديو بالأمر الصحيح لحفظه في قاعدة البيانات.")

def main():
    # ضع هنا توكن بوت التيليجرام الخاص بك
    TOKEN = "8911756458:AAHtom5VBOPb6rBCmejD59RDNgI7iwocIbg"
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload_episode))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Telegram bot is running...")
    app.run_polling()

if __name__ == '__main__
':
    main()
