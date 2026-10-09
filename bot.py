import os
import logging
import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7080361795"))

user_sections = {}
user_upload_state = {}  # لتتبع حالة رفع الأدمن (القسم ورقم الحلقة)

# تهيئة قاعدة البيانات SQLite
async def init_db():
    async with aiosqlite.connect("database.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                section TEXT,
                ep_number TEXT,
                file_id TEXT,
                PRIMARY KEY (section, ep_number)
            )
        """)
        await db.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🐉 دراغون بول الكلاسيكي (153 حلقة)", callback_data="db_classic")],
        [InlineKeyboardButton("⚡ دراغون بول زد (291 حلقة)", callback_data="db_z")],
        [InlineKeyboardButton("🔥 دراغون بول سوبر (131 حلقة)", callback_data="db_super")],
        [InlineKeyboardButton("✨ دراغون بول دايما (الأحدث)", callback_data="db_daima")],
        [InlineKeyboardButton("💫 سوبر دراغون بول هيروز", callback_data="db_heroes")],
        [InlineKeyboardButton("🌀 دراغون بول جي تي (64 حلقة)", callback_data="db_gt")],
        [InlineKeyboardButton("🎬 قائمة الأفلام والخاصات", callback_data="db_movies")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔥 أهلاً بك في بوت دراغون بول الرسمي!\nاختر القسم الذي ترغب في تصفحه:",
        reply_markup=reply_markup
    )

# أمر خاص بالأدمن لبدء رفع حلقة: /upload [القسم] [رقم الحلقة]
# مثال: /upload db_z 1
async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرف فقط.")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ الاستخدام الخاطئ للأمر.\n"
            "الطريقة الصحيحة:\n`/upload [اسم_القسم] [رقم_الحلقة]`\n\n"
            "الأقسام المتاحة:\n"
            "- `db_classic`\n- `db_z`\n- `db_super`\n- `db_daima`\n- `db_heroes`\n- `db_gt`\n- `db_movies`",
            parse_mode="Markdown"
        )
        return
    
    section = args[0]
    ep_num = args[1]
    
    valid_sections = ["db_classic", "db_z", "db_super", "db_daima", "db_heroes", "db_gt", "db_movies"]
    if section not in valid_sections:
        await update.message.reply_text("❌ اسم القسم غير صحيح تأكد منه.")
        return
    
    # حفظ حالة الرفع المؤقتة للأدمن
    user_upload_state[user_id] = {"section": section, "ep_number": ep_num}
    await update.message.reply_text(f"✅ تم تحديد القسم (`{section}`) ورقم الحلقة (`{ep_num}`).\n\n**الآن قم بإرسال الفيديو (أو الملف) الخاص بالحلقة مباشرة هنا:**")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    user_sections[user_id] = data
    
    section_names = {
        "db_classic": "دراغون بول الكلاسيكي",
        "db_z": "دراغون بول زد",
        "db_super": "دراغون بول سوبر",
        "db_daima": "دراغون بول دايما",
        "db_heroes": "سوبر دراغون بول هيروز",
        "db_gt": "دراغون بول جي تي",
        "db_movies": "أفلام دراغون بول والخاصات"
    }
    
    current_section = section_names.get(data, "القسم")
    
    await query.edit_message_text(
        text=f"✨ أنت الآن في قسم: **{current_section}**\n\n📝 أرسل الآن رقم الحلقة التي تريدها:"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # 1. إذا كان المرسل هو الأدمن وكان في وضع رفع حلقة جديدة (أرسل فيديو)
    if user_id == ADMIN_ID and user_id in user_upload_state:
        if update.message.video or update.message.document:
            file_id = update.message.video.file_id if update.message.video else update.message.document.file_id
            state = user_upload_state[user_id]
            section = state["section"]
            ep_num = state["ep_number"]
            
            # حفظ الحلقة في قاعدة البيانات
            async with aiosqlite.connect("database.db") as db:
                await db.execute(
                    "INSERT OR REPLACE INTO episodes (section, ep_number, file_id) VALUES (?, ?, ?)",
                    (section, ep_num, file_id)
                )
                await db.commit()
            
            del user_upload_state[user_id]
            await update.message.reply_text(f"🎉 تم حفظ الحلقة رقم ({ep_num}) في قسم (`{section}`) بنجاح تام!")
            return
        else:
            await update.message.reply_text("⚠️ أنت في وضع الرفع، يرجى إرسال ملف فيديو الحلقة الآن.")
            return

    # 2. التعامل مع المستخدمين العاديين عند طلب حلقة برقمها
    if update.message.text:
        text = update.message.text.strip()
        
        if user_id not in user_sections:
            await update.message.reply_text("الرجاء اختيار القسم أولاً بالضغط على /start 🔄")
            return
        
        section = user_sections[user_id]
        
        # البحث عن الحلقة في قاعدة البيانات
        async with aiosqlite.connect("database.db") as db:
            async with db.execute(
                "SELECT file_id FROM episodes WHERE section = ? AND ep_number = ?",
                (section, text)
            ) as cursor:
                row = await cursor.fetchone()
                
        if row:
            file_id = row[0]
            await context.bot.send_video(chat_id=update.message.chat_id, video=file_id, caption=f"🎬 تفضل طلبك للحلقة رقم ({text})")
        else:
            await update.message.reply_text(f"⚠️ عذراً يا صديقي، الحلقة رقم ({text}) غير متوفرة حالياً في هذا القسم أو لم يتم رفعها بعد! 🛑")

def main():
    if not TOKEN:
        return

    app = ApplicationBuilder().token(TOKEN).build()
    
    # تهيئة قاعدة البيانات عند بدء التشغيل
    app.job_queue.run_once(lambda context: app.create_task(init_db()), 0)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler((filters.TEXT | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND, handle_message))
    
    print("Bot with Admin Upload panel is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
