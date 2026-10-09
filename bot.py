import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

# تفعيل سجل الأخطاء لمعرفة السبب بدقة لو حدث خطأ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "db_classic":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول الكلاسيكي**")
    elif query.data == "db_z":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول زد**")
    elif query.data == "db_super":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول سوبر**")
    elif query.data == "db_daimin" or query.data == "db_daima":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول دايما**")
    elif query.data == "db_heroes":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **سوبر دراغون بول هيروز**")
    elif query.data == "db_gt":
        await query.edit_message_text(text="✨ أنت الآن في قسم: **دراغون بول جي تي**")
    elif query.data == "db_movies":
        await query.edit_message_text(text="🎬 أنت الآن في قسم: **أفلام دراغون بول والخاصات**")

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
   
    main()
