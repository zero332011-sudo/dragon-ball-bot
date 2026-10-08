import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, add_episode, get_all_episodes, delete_episode

# قراءة المتغيرات الأمنية من إعدادات سرفر الاستضافه (Render)
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

app = Client(
    "dragon_ball_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "👋 أهلاً بك في بوت حلقات دراغون بول!\n\n"
        "استخدم /episodes لعرض الحلقات المتاحة للمشاهدة."
    )

@app.on_message(filters.command("episodes"))
async def list_episodes(client, message: Message):
    await init_db()
    episodes = await get_all_episodes()
    if not episodes:
        await message.reply_text("📭 لا توجد حلقات مضافة حالياً.")
        return
    
    text = "🎬 **قائمة حلقات دراغون بول المتاحة:**\n\n"
    for ep_id, title, file_id in episodes:
        text += f"🔹 {title} (ID: {ep_id})\n"
    
    await message.reply_text(text)

@app.on_message(filters.command("add") & filters.user(ADMIN_ID))
async def add_ep(client, message: Message):
    # الطريقة: /add اسم الحلقة (ثم الرد على الفيديو)
    if not message.reply_to_message or len(message.command) < 2:
        await message.reply_text("⚠️ قم بالرد على فيديو الحلقة واكتب أمر: `/add اسم_الحلقة`")
        return
    
    title = " ".join(message.command[1:])
    file_id = message.reply_to_message.video.file_id if message.reply_to_message.video else message.reply_to_message.document.file_id
    
    await init_db()
    await add_episode(title, file_id)
    await message.reply_text(f"✅ تم إضافة الحلقة ({title}) بنجاح!")

@app.on_message(filters.command("get") & filters.text)
async def get_ep(client, message: Message):
    # جلب حلقة برقمها مثلاً /get 1
    if len(message.command) < 2:
        return
    try:
        ep_id = int(message.command[1])
    except ValueError:
        return
    
    await init_db()
    episodes = await get_all_episodes()
    target_ep = next((ep for ep in episodes if ep[0] == ep_id), None)
    
    if target_ep:
        _, title, file_id = target_ep
        await message.reply_video(video=file_id, caption=f"🎬 {title}")
    else:
        await message.reply_text("❌ لم يتم العثور على هذه الحلقة.")

if __name__ == "__main__":
    app.run()
