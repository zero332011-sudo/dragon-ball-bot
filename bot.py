import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

# قراءة الـ Token من متغيرات البيئة في Railway
TOKEN = os.getenv("BOT_TOKEN")

# دالة بدء البوت وإرسال الأقسام كأزرار تفاعلية
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
    
    # التحقق مما إذا كان الطلب من رسالة عادية أو ضغط على زر
    if update.message:
        await update.message.reply_text(
            "🔥 أهلاً بك في بوت دراغون بول الرسمي!\nاختر القسم الذي ترغب في تصفحه:",
            reply_markup=reply_markup
        )

# دالة للتعامل مع الضغط على الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # الرد بناءً على القسم الذي اختاره المستخدم
    if query.data == "db_classic":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول الكلاسيكي**\nقريباً سيتم إرسال الحلقات هنا!")
    elif query.data == "db_z":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول زد**\nقريباً سيتم إرسال الحلقات هنا!")
    elif query.data == "db_super":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول سوبر**\nقريباً سيتم إرسال الحلقات هنا!")
    elif query.data == "db_daima":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول دايما**\nقريباً سيتم إرسال الحلقات هنا!")
    elif query.data == "db_heroes":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **سوبر دراغون بول هيروز**\nقريباً سيتم إرسال الحلقات هنا!")
    elif query.data == "db_gt":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول جي تي**\nقريباً سيتم إرسال الحلقات هنا!")
    elif query.data == "db_movies":
        await query.edit_message_text(text="🎬 أنت الآن في قسم: **أفلام دراغون بول والخاصات**\nقريباً سيتم إرسال الأفلام هنا!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    # إضافة الأوامر ومعالجة الأزرار
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is running...")
    app.run_polli
    ng()
