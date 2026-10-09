import os
import logging
import asyncio
import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7080361795"))

# ضع هنا معرف قناتك (مثال: -1001234567890 أو اليوزر @channel)
CHANNEL_ID = -100XXXXXXXXXX 
CHANNEL_LINK = "https://t.me/+6A997HR9zOw5NTVk"

user_sections = {}
user_upload_state = {}

# تهيئة قاعدة البيانات (لحفظ الحلقات وحالة تفعيل الاشتراك الإجباري)
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # تفعيل الاشتراك الإجباري افتراضياً (True)
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('force_sub', 'True')"
        )
        await db.commit()

async def get_force_sub_status():
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'force_sub'") as cursor:
            row = await cursor.fetchone()
            return row[0] == 'True' if row else True

async def set_force_sub_status(status: bool):
    async with aiosqlite.connect("database.db") as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('force_sub', ?)", (str(status),))
        await db.commit()

# دالة للتحقق مما إذا كان المستخدم مشتركاً في القناة
async def check_user_subscription(user_id, context):
    if not await get_force_sub_status():
        return True # إذا كانت ميزة الاشتراك معطلة، اسمح للجميع
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception:
        pass
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # التحقق من الاشتراك الإجباري
    if not await check_user_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة هنا", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "⚠️ عذراً يا صديقي، يجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه!\n\n"
            "بعد الاشتراك، اضغط على زر (تحقق من الاشتراك) بالأسفل 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await show_main_menu(update.message)

async def show_main_menu(message):
    keyboard = [
        [InlineKeyboardButton("🐉 دراغون بول الكلاسيكي (153 حلقة)", callback_data="db_classic")],
        [InlineKeyboardButton("⚡ دراغون بول زد (291 حلقة)", callback_data="db_z")],
        [InlineKeyboardButton("🔥 دراغون بول سوبر (131 حلقة)", callback_data="db_super")],
        [InlineKeyboardButton("✨ دراغون بول دايما (الأحدث)", callback_data="db_daima")],
        [InlineKeyboardButton("💫 سوبر دراغون بول هيروز", callback_data="db_heroes")],
        [InlineKeyboardButton("🌀 دراغون بول جي تي (64 حلقة)", callback_data="db_gt")],
        [InlineKeyboardButton("🎬 قائمة الأفلام والخاصات", callback_data="db_movies")]
    ]
    
    # إضافة زر لوحة التحكم للأدمن في القائمة الرئيسية إذا كان هو المرسل
    # (يمكنه أيضاً استخدام /admin)
    
    await message.reply_text(
        "🔥 أهلاً بك في بوت دراغون بول الرسمي!\nاختر القسم الذي ترغب في تصفحه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# لوحة تحكم الأدمن للتحكم بالاشتراك الإجباري
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    current_status = await get_force_sub_status()
    status_text = "🟢 مفعل" if current_status else "🔴 معطل"
    
    keyboard = [
        [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
        [InlineKeyboardButton("📊 إحصائيات وأوامر الرفع", callback_data="admin_help")]
    ]
    
    await update.message.reply_text(
        "🎛️ **لوحة تحكم المشرف (الأدمن):**\n"
        "يمكنك تفعيل أو إلغاء تفعيل ميزة الاشتراك الإجباري في القناة بضغط زر واحدة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرف فقط.")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ الاستخدام:\n`/upload [القسم] [رقم_الحلقة]`\n\n"
            "الأقسام:\n- `db_classic`\n- `db_z`\n- `db_super`\n- `db_daima`\n- `db_heroes`\n- `db_gt`\n- `db_movies`",
            parse_mode="Markdown"
        )
        return
    
    section = args[0]
    ep_num = args[1]
    
    valid_sections = ["db_classic", "db_z", "db_super", "db_daima", "db_heroes", "db_gt", "db_movies"]
    if section not in valid_sections:
        await update.message.reply_text("❌ اسم القسم غير صحيح.")
        return
    
    user_upload_state[user_id] = {"section": section, "ep_number": ep_num}
    await update.message.reply_text(f"✅ تم تحديد القسم (`{section}`) ورقم الحلقة (`{ep_num}`).\n\n**أرسل فيديو الحلقة الآن:**")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    # زر التحقق من الاشتراك
    if data == "check_sub":
        if await check_user_subscription(user_id, context):
            await query.message.delete()
            # إرسال القائمة الرئيسية بعد نجاح الاشتراك
            await show_main_menu(query.message)
        else:
            await query.answer("❌ لم تقم بالاشتراك في القناة بعد! اشتراك ثم حاول مجدداً.", show_alert=True)
        return

    # زر تبديل حالة الاشتراك الإجباري (خاص بالأدمن)
    if data == "toggle_sub" and user_id == ADMIN_ID:
        current = await get_force_sub_status()
        new_status = not current
        await set_force_sub_status(new_status)
        
        status_text = "🟢 مفعل" if new_status else "🔴 معطل"
        keyboard = [
            [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "admin_help":
        await query.message.reply_text(
            "💡 لرفع حلقة جديدة:\n"
            "استخدم الأمر: `/upload [اسم_القسم] [رقم_الحلقة]`\n"
            "ثم أرسل الفيديو للبوت."
        )
        return

    # باقي أقسام الأنمي
    if not await check_user_subscription(user_id, context):
        await query.answer("⚠️ يجب الاشتراك في القناة أولاً لاستخدام البوت!", show_alert=True)
        return

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
    
    # معالجة رفع الفيديو للأدمن
    if user_id == ADMIN_ID and user_id in user_upload_state:
        if update.message.video or update.message.document:
            file_id = update.message.video.file_id if update.message.video else update.message.document.file_id
            state = user_upload_state[user_id]
            section = state["section"]
            ep_num = state["ep_number"]
            
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
            await update.message.reply_text("⚠️ أنت في وضع الرفع، أرسل ملف فيديو الحلقة الآن.")
            return

    # التحقق من الاشتراك للمستخدمين العاديين
    if not await check_user_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة هنا", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "⚠️ عذراً، يجب عليك الاشتراك في قناة البوت أولاً لتستطيع طلب الحلقات!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # طلب الحلقة برقمها
    if update.message.text:
        text = update.message.text.strip()
        
        if user_id not in user_sections:
            await update.message.reply_text("الرجاء اختيار القسم أولاً بالضغط على /start 🔄")
            return
        
        section = user_sections[user_id]
        
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

    asyncio.run(init_db())

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler((filters.TEXT | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND, handle_message))
    
    print("Bot with Force Subscribe & Admin Panel is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
        
