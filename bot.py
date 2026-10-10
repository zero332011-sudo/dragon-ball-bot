import telebot
from telebot import types

TOKEN = "8911756458:AAE0fgUD-kxKI5Q34yuFG-NRBXd7icJn32c"
bot = telebot.TeleBot(TOKEN)

user_states = {}

# القائمة الكاملة للأقسام
SECTIONS = {
    "db_classic": "🐉 الكلاسيكي",
    "db_z": "⚡ دراغون بول زد",
    "db_kai": "⚔️ زد كاي",
    "db_super": "🔥 سوبر",
    "db_super2": "🔥 سوبر 2",
    "db_daima": "✨ دايما",
    "db_gt": "🌀 جي تي",
    "db_heroes": "💫 هيروز",
    "db_movies": "🎬 الأفلام",
    "db_specials": "⭐ الحلقات الخاصة"
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_upload = types.InlineKeyboardButton("📤 رفع حلقات", callback_data="menu_upload")
    btn_help = types.InlineKeyboardButton("ℹ️ معلومات البوت", callback_data="menu_help")
    markup.add(btn_upload, btn_help)
    
    bot.send_message(
        message.chat.id,
        "⭐ مرحباً بك في بوت أنمي دراغون بول الرسمي!\nاختر الخيار المطلوب من الأزرار بالأسفل:",
        reply_markup=markup
    )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_upload = types.InlineKeyboardButton("📤 رفع حلقات", callback_data="menu_upload")
    markup.add(btn_upload)
    
    bot.send_message(
        message.chat.id,
        "⚙️ أهلاً بك في لوحة تحكم الأدمن:\n\nيمكنك التحكم في الروابط، الحالة، والحلقات بكل مرونة من الأزرار أدناه:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
def main_menu_callback(call):
    if call.data == "menu_upload":
        show_upload_sections(call.message)
    elif call.data == "menu_help":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "هذا البوت مخصص لإدارة ورفع حلقات دراغون بول بجميع أقسامها."
        )

def show_upload_sections(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = []
    for code, name in SECTIONS.items():
        buttons.append(types.InlineKeyboardButton(name, callback_data=f"up_{code}"))
    
    markup.add(*buttons)
    btn_back = types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_back")
    markup.add(btn_back)
    
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message.id,
            text="📁 اختر القسم الذي تريد رفع الحلقات إليه:",
            reply_markup=markup
        )
    except Exception:
        bot.send_message(
            chat_id=message.chat.id,
            text="📁 اختر القسم الذي تريد رفع الحلقات إليه:",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('up_'))
def upload_section_callback(call):
    section_code = call.data.replace('up_', '')
    user_states[call.from_user.id] = {"action": "waiting_for_files", "section": section_code}
    
    name = SECTIONS.get(section_code, section_code)
    bot.answer_callback_query(call.id, f"تم اختيار: {name}")
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text=f"✅ لقد اخترت قسم: *{name}*\n\nأرسل الآن الحلقات (فيديوهات أو ملفات) وسيقوم البوت باستلامها وتصنيفها تحت هذا القسم.",
            parse_mode="Markdown"
        )
    except Exception:
        bot.send_message(
            chat_id=call.message.chat.id,
            text=f"✅ لقد اخترت قسم: *{name}*\n\nأرسل الآن الحلقات (فيديوهات أو ملفات) وسيقوم البوت باستلامها وتصنيفها تحت هذا القسم.",
            parse_mode="Markdown"
        )

@bot.callback_query_handler(func=lambda call: call.data == "menu_back")
def back_to_home(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_upload = types.InlineKeyboardButton("📤 رفع حلقات", callback_data="menu_upload")
    btn_help = types.InlineKeyboardButton("ℹ️ معلومات البوت", callback_data="menu_help")
    markup.add(btn_upload, btn_help)
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="مرحباً بك مرة أخرى في القائمة الرئيسية:",
            reply_markup=markup
        )
    except Exception:
        bot.send_message(
            chat_id=call.message.chat.id,
            text="مرحباً بك مرة أخرى في القائمة الرئيسية:",
            reply_markup=markup
        )

@bot.message_handler(content_types=['video', 'document'])
def handle_incoming_files(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id].get("action") == "waiting_for_files":
        current_section_code = user_states[user_id].get("section")
        current_section_name = SECTIONS.get(current_section_code, current_section_code)
        
        bot.reply_to(
            message, 
            f"📥 تم استلام الملف بنجاح وتوجيهه إلى القسم: `{current_section_name}`", 
            parse_mode="Markdown"
        )
    else:
        bot.reply_to(message, "⚠️ الرجاء استخدام أمر /start واختيار (رفع حلقات) وتحديد القسم أولاً.")

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True)
    
