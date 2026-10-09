import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes

# تفعيل سجلات التتبع
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# قاموس مؤقت لحفظ القسم الذي اختاره كل مستخدم
user_sections = {}

# قاموس الحلقات المتاحة (يمكنك تعديل الروابط أو استبدالها بروابط رسائل قناتك الخاصة)
AVAILABLE_EPISODES = {
    "db_classic": {
        "1": "https://t.me/your_channel/10",
        "2": "https://t.me/your_channel/11",
    },
    "db_z": {
        "1": "https://t.me/your_channel/50",
    },
    "db_super": {},
    "db_daima": {},
    "db_heroes": {},
    "db_gt": {},
    "db_movies": {}
}

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
    
    user_id = query.from_user.id
    data = query.data
    
    # حفظ القسم الخاص بالمستخدم
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
        text=f"✨ أنت الآن في قسم: **{current_section}**\n\n📝 أرسل الآن رقم الحلقة التي تريدها (مثال: `1` أو `2`):"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    
    # التحقق إن كان المستخدم اختار قسماً مسبقاً
    if user_id not in user_sections:
        await update.message.reply_text("الرجاء اختيار القسم أولاً بالضغط على /start 🔄")
        return
    
    section = user_sections[user_id]
    section_eps = AVAILABLE_EPISODES.get(section, {})
    
    # التحقق من توفر الحلقة
    if text in section_eps:
        ep_link = section_eps[text]
        await update.message.reply_text(f"🎬 تفضل طلبك للحلقة رقم ({text}):\n{ep_link}")
    else:
        # رسالة في حال كانت الحلقة غير متوفرة
        await update.message.reply_text(
            f"⚠️ عذراً يا صديقي، الحلقة رقم ({text}) غير متوفرة حالياً في هذا القسم أو لم يتم رفعها بعد! 🛑"
        )

def main():
    if not TOKEN:
        print("Error: Token not found")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running smoothly...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
