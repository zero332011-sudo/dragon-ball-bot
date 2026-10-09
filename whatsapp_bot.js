const { Client, LocalAuth } = require('whatsapp-web.js');
const sqlite3 = require('sqlite3').verbose();

// الاتصال بقاعدة البيانات المشتركة
const db = new sqlite3.Database('./database.db', (err) => {
    if (err) console.error('خطأ في قاعدة البيانات:', err.message);
    else console.log('تم اتصال بوت الواتساب بقاعدة البيانات بنجاح.');
});

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
});

// رقم هاتف البوت والرقم المطور
const PHONE_NUMBER = "201154684341";
const DEVELOPER_NUMBER = "201032219184@c.us"; // رقم المطور

client.on('qr', async (qr) => {
    // تم تخطي الـ QR والاعتماد على رمز الاقتران برقم الهاتف
});

client.on('ready', () => {
    console.log('✅ WhatsApp Bot is online and connected successfully!');
});

// طلب رمز الاقتران برقم الهاتف بعد تشغيل العميل
setTimeout(async () => {
    try {
        console.log(`جاري طلب رمز الاقتران لرقم الهاتف: ${PHONE_NUMBER}...`);
        const pairingCode = await client.requestPairingCode(PHONE_NUMBER);
        console.log(`\n========================================`);
        console.log(`🔑 رمز الاقتران الخاص بك هو: ${pairingCode}`);
        console.log(`========================================\n`);
    } catch (error) {
        console.error('خطأ أثناء طلب رمز الاقتران:', error);
    }
}, 6000);

const userSections = {};

client.on('message', async (message) => {
    const chatId = message.from;
    const text = message.body.trim();

    // التحقق إذا كانت الرسالة من المطور
    const isDeveloper = chatId === DEVELOPER_NUMBER;

    if (text === '/start' || text === 'القائمة' || text === 'مرحبا') {
        userSections[chatId] = null;
        let replyText = "🔥 *أهلاً بك في بوت دراغون بول عبر الواتساب!*\n\n" +
            "أرسل كود القسم المطلوب (مثال: `db_z` أو `db_kai` أو `db_classic`)، ثم أرسل رقم الحلقة.";
        
        if (isDeveloper) {
            replyText += "\n\n🛠️ *مرحباً بك يا مطور النظام (صلاحيات كاملة مفعلة).*";
        }

        await message.reply(replyText);
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

client.initialize();
