import os
import re
import logging
import asyncio
import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات (Logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7080361795"))

CHANNEL_ID = "@YourChannelUsername"  # ضع يوزر قناتك أو الآيدي الرقمي هنا
CHANNEL_LINK = "https://t.me/+6A997HR9zOw5NTVk"

user_sections = {}
user_upload_state = {}
bulk_upload_state = {}

# تهيئة قاعدة البيانات
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

async def check_user_subscription(user_id, context):
    if not await get_force_sub_status():
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        return True 
    return False

# القائمة الرئيسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
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
        [InlineKeyboardButton("🐉 دراغون بول الكلاسيكي", callback_data="db_classic")],
        [InlineKeyboardButton("⚡ دراغون بول زد", callback_data="db_z")],
        [InlineKeyboardButton("🔥 دراغون بول سوبر", callback_data="db_super")],
        [InlineKeyboardButton("🔥 دراغون بول سوبر 2 (الإصدار الجديد)", callback_data="db_super_2")],
        [InlineKeyboardButton("✨ دراغون بول دايما", callback_data="db_daima")],
        [InlineKeyboardButton("💫 سوبر دراغون بول هيروز", callback_data="db_heroes")],
        [InlineKeyboardButton("🌀 دراغون بول جي تي", callback_data="db_gt")],
        [InlineKeyboardButton("⭐ الحلقات الخاصة", callback_data="db_specials")],
        [InlineKeyboardButton("🎬 قائمة الأفلام", callback_data="db_movies")]
    ]
    
    await message.reply_text(
        "🔥 أهلاً بك في بوت دراغون بول الرسمي!\nاختر القسم الذي ترغب في تصفحه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# لوحة تحكم الأدمن
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    current_status = await get_force_sub_status()
    status_text = "🟢 مفعل" if current_status else "🔴 معطل"
    
    keyboard = [
        [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
        [InlineKeyboardButton("📊 مساعدة الأوامر والرفع الجماعي", callback_data="admin_help")]
    ]
    
    await update.message.reply_text(
        "🎛️ **لوحة تحكم المشرف (الأدمن):**\n"
        "يمكنك التحكم في الاشتراك الإجباري أو مراجعة أوامر الرفع السريع:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# أمر رفع حلقة مفردة
async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ الاستخدام الصحيح:\n`/upload [القسم] [رقم_الحلقة]`", parse_mode="Markdown")
        return
    
    section, ep_num = args[0], args[1]
    valid_sections = ["db_classic", "db_z", "db_super", "db_super_2", "db_daima", "db_heroes", "db_gt", "db_specials", "db_movies"]
    if section not in valid_sections:
        await update.message.reply_text("❌ اسم القسم غير صحيح.")
        return
    
    user_upload_state[user_id] = {"section": section, "ep_number": ep_num}
    await update.message.reply_text(f"✅ تم تحديد القسم (`{section}`) ورقم الحلقة (`{ep_num}`).\n\n**أرسل فيديو الحلقة الآن:**")

# أمر الرفع الجماعي المتسلسل (Bulk Upload)
async def bulk_upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ **الاستخدام الصحيح للرفع الجماعي:**\n"
            "`/bulk [القسم] [رقم_البداية]`\n\n"
            "📋 **أوامر الأقسام الجاهزة للنسخ:**\n"
            "• دراغون بول الكلاسيكي: `/bulk db_classic 1`\n"
            "• دراغون بول زد: `/bulk db_z 1`\n"
            "• دراغون بول سوبر: `/bulk db_super 1`\n"
            "• دراغون بول سوبر 2: `/bulk db_super_2 1`\n"
            "• دراغون بول دايما: `/bulk db_daima 1`\n"
            "• سوبر دراغون بول هيروز: `/bulk db_heroes 1`\n"
            "• دراغون بول جي تي: `/bulk db_gt 1`\n"
            "• الحلقات الخاصة: `/bulk db_specials 1`\n"
            "• قائمة الأفلام: `/bulk db_movies 1`\n\n"
            "طريقة العمل: انسخ الأمر المناسب، أرسله، ثم أرسل الحلقات وراء بعضها، وللإنهاء والخروج أرسل: `/done`",
            parse_mode="Markdown"
        )
        return
    
    section = args[0]
    try:
        start_ep = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ رقم البداية يجب أن يكون رقماً صحيحاً.")
        return
        
    valid_sections = ["db_classic", "db_z", "db_super", "db_super_2", "db_daima", "db_heroes", "db_gt", "db_specials", "db_movies"]
    if section not in valid_sections:
        await update.message.reply_text(f"❌ اسم القسم غير صحيح. الأقسام المتاحة:\n`" + "`, `".join(valid_sections) + "`", parse_mode="Markdown")
        return
        
    bulk_upload_state[user_id] = {"section": section, "current_ep": start_ep}
    if user_id in user_sections:
        del user_sections[user_id]

    await update.message.reply_text(
        f"🚀 **تم تفعيل وضع الرفع الجماعي المتسلسل بنجاح!**\n"
        f"📂 القسم: `{section}`\n"
        f"🔢 يبدأ الترقيم التلقائي من: `{start_ep}`\n\n"
        "📥 **أرسل الفيديوهات الآن (تباعاً أو دفعة واحدة).**\n"
        "عند الانتهاء تماماً، أرسل الأمر: `/done`"
    )

async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID and user_id in bulk_upload_state:
        del bulk_upload_state[user_id]
        await update.message.reply_text("🛑 تم إيقاف وضع الرفع الجماعي وحفظ الإعدادات بنجاح.")

# معالجة الأزرار والإنلاين
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "check_sub":
        if await check_user_subscription(user_id, context):
            await query.message.delete()
            await show_main_menu(query.message)
        else:
            await query.answer("❌ لم تقم بالاشتراك في القناة بعد!", show_alert=True)
        return

    if data == "toggle_sub" and user_id == ADMIN_ID:
        current = await get_force_sub_status()
        new_status = not current
        await set_force_sub_status(new_status)
        
        status_text = "🟢 مفعل" if new_status else "🔴 معطل"
        keyboard = [[InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")]]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "admin_help":
        await query.message.reply_text(
            "💡 **دليل وأوامر الرفع الجماعي لكل الأقسام:**\n\n"
            "• **دراغون بول الكلاسيكي:**\n`/bulk db_classic 1`\n\n"
            "• **دراغون بول زد:**\n`/bulk db_z 1`\n\n"
            "• **دراغون بول سوبر:**\n`/bulk db_super 1`\n\n"
            "• **دراغون بول سوبر 2 (الجديد):**\n`/bulk db_super_2 1`\n\n"
            "• **دراغون بول دايما:**\n`/bulk db_daima 1`\n\n"
            "• **سوبر دراغون بول هيروز:**\n`/bulk db_heroes 1`\n\n"
            "• **دراغون بول جي تي:**\n`/bulk db_gt 1`\n\n"
            "• **الحلقات الخاصة:**\n`/bulk db_specials 1`\n\n"
            "• **قائمة الأفلام:**\n`/bulk db_movies 1`\n\n"
            "📌 *ملاحظة:* استبدل الرقم `1` برقم البداية الذي تريده، ثم أرسل الحلقات واكتب `/done` عند الانتهاء.",
            parse_mode="Markdown"
        )
        return

    if not await check_user_subscription(user_id, context):
        await query.answer("⚠️ يجب الاشتراك في القناة أولاً!", show_alert=True)
        return

    user_sections[user_id] = data
    section_names = {
        "db_classic": "دراغون بول الكلاسيكي", "db_z": "دراغون بول زد",
        "db_super": "دراغون بول سوبر", "db_super_2": "دراغون بول سوبر 2",
        "db_daima": "دراغون بول دايما", "db_heroes": "سوبر دراغون بول هيروز",
        "db_gt": "دراغون بول جي تي", "db_specials": "الحلقات الخاصة",
        "db_movies": "قائمة الأفلام"
    }
    await query.edit_message_text(text=f"✨ أنت الآن في قسم: **{section_names.get(data, 'القسم')}**\n\n📝 أرسل رقم الحلقة التي تريدها:")

# استقبال الرسائل والفيديوهات
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # 1. نظام الرفع الجماعي المتسلسل (Bulk Upload) للأدمن
    if user_id == ADMIN_ID and user_id in bulk_upload_state:
        if update.message.video or update.message.document:
            file_id = update.message.video.file_id if update.message.video else update.message.document.file_id
            file_name = update.message.video.file_name if (update.message.video and update.message.video.file_name) else (update.message.document.file_name if update.message.document else "")
            
            state = bulk_upload_state[user_id]
            section = state["section"]
            ep_num = str(state["current_ep"])
            
            if file_name:
                numbers = re.findall(r'\d+', file_name)
                if numbers:
                    ep_num = numbers[-1]
            
            async with aiosqlite.connect("database.db") as db:
                await db.execute(
                    "INSERT OR REPLACE INTO episodes (section, ep_number, file_id) VALUES (?, ?, ?)",
                    (section, ep_num, file_id)
                )
                await db.commit()
            
            bulk_upload_state[user_id]["current_ep"] = int(ep_num) + 1
            await update.message.reply_text(f"📥 تم حفظ الحلقة رقم ({ep_num}) بنجاح في قسم (`{section}`). (جاهز للحلقة التالية...)")
            return
        else:
            await update.message.reply_text("⚠️ أنت في وضع الرفع الجماعي، أرسل الفيديوهات الآن أو اكتب `/done` للإنهاء.")
            return

    # 2. رفع حلقة مفردة بالطريقة العادية للأدمن
    if user_id == ADMIN_ID and user_id in user_upload_state:
        if update.message.video or update.message.document:
            file_id = update.message.video.file_id if update.message.video else update.message.document.file_id
            state = user_upload_state[user_id]
            section, ep_num = state["section"], state["ep_number"]
            
            async with aiosqlite.connect("database.db") as db:
                await db.execute(
                    "INSERT OR REPLACE INTO episodes (section, ep_number, file_id) VALUES (?, ?, ?)",
                    (section, ep_num, file_id)
                )
                await db.commit()
            
            del user_upload_state[user_id]
            await update.message.reply_text(f"🎉 تم حفظ الحلقة رقم ({ep_num}) في قسم (`{section}`) بنجاح!")
            return
        else:
            await update.message.reply_text("⚠️ أنت في وضع الرفع، أرسل ملف الفيديو الآن.")
            return

    # 3. التحقق من الاشتراك للمستخدمين العاديين
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

    # 4. استقبال طلبات الحلقات من المستخدمين
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
            await context.bot.send_video(chat_id=update.message.chat_id, video=row[0], caption=f"🎬 تفضل طلبك للحلقة رقم ({text})")
        else:
            await update.message.reply_text(f"⚠️ عذراً، الحلقة رقم ({text}) غير متوفرة حالياً في هذا القسم! 🛑")

def main():
    if not TOKEN:
        return

    asyncio.run(init_db())

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("bulk", bulk_upload_command))
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler((filters.TEXT | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND, handle_message))
    
    print("Bot is running smoothly...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
