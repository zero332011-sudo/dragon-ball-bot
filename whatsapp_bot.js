const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const sqlite3 = require('sqlite3').verbose();

// الاتصال بقاعدة البيانات المشتركة
const db = new sqlite3.Database('./database.db', (err) => {
    if (err) console.error('خطأ في قاعدة البيانات:', err.message);
    else console.log('تم اتصال بوت الواتساب بقاعدة البيانات بنجاح.');
});

const client = new Client({
    authStrategy: new LocalAuth()
});

client.on('qr', (qr) => {
    console.log('--- QR CODE FOR WHATSAPP ---');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('WhatsApp Bot is online and connected!');
});

const userSections = {};

client.on('message', async (message) => {
    const chatId = message.from;
    const text = message.body.trim();

    if (text === '/start' || text === 'القائمة' || text === 'مرحبا') {
        userSections[chatId] = null;
        await message.reply(
            "🔥 *أهلاً بك في بوت دراغون بول عبر الواتساب!*\n\n" +
            "أرسل كود القسم المطلوبة (مثال: `db_z` أو `db_kai` أو `db_classic`)، ثم أرسل رقم الحلقة."
        );
        return;
    }

    const validSections = [
        "db_classic", "db_z", "db_kai", "db_super", 
        "db_super_2", "db_daima", "db_heroes", "db_gt", 
        "db_specials", "db_movies"
    ];

    if (validSections.includes(text)) {
        userSections[chatId] = text;
        await message.reply(`✨ تم اختيار القسم بنجاح!\n📝 الآن أرسل رقم الحلقة المطلوبة.`);
        return;
    }

    if (userSections[chatId]) {
        const section = userSections[chatId];
        db.get(
            `SELECT file_id FROM episodes WHERE section = ? AND ep_number = ?`,
            [section, text],
            async (err, row) => {
                if (row) {
                    await message.reply(`🎬 عثرنا على الحلقة رقم (${text}) في القسم (${section}).`);
                } else {
                    await message.reply(`⚠️ عذراً، الحلقة رقم (${text}) غير متوفرة حالياً.`);
                }
            }
        );
    } else {
        await message.reply(`الرجاء إرسال /start لعرض الأقسام أولاً 🔄`);
    }
});

client.in
      itialize();
