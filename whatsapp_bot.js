const { Client, LocalAuth } = require('whatsapp-web.js');
const sqlite3 = require('sqlite3').verbose();

// الاتصال بقاعدة البيانات المشتركة
const db = new sqlite3.Database('./database.db', (err) => {
    if (err) console.error('خطأ في قاعدة البيانات:', err.message);
    else console.log('تم اتصال بوت الواتساب بقاعدة البيانات بنجاح.');
});

// إعداد عميل الواتساب مع دعم رقم الهاتف
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// رقم الهاتف المراد ربطه (بدون علامات أو مسافات، مع رمز الدولة مثلاً: مصر 20)
const PHONE_NUMBER = "201154684341"; 

client.on('qr', (qr) => {
    // تم إيقاف الاعتماد على QR وتفعيل طريقة رقم الهاتف أدناه
});

client.on('ready', async () => {
    console.log('WhatsApp Bot is online and connected successfully!');
});

// محاولة ربط الجهاز باستخدام رقم الهاتف وطلب رمز الاقتران (Pairing Code)
client.on('authenticated', () => {
    console.log('تم توثيق جلسة الواتساب بنجاح!');
});

// عند جاهزية العميل للبدء في عملية الربط برقم الهاتف
setTimeout(async () => {
    try {
        if (!client.info || !client.info.wid) {
            console.log(`جاري طلب رمز الاقتران (Pairing Code) لرقم الهاتف: ${PHONE_NUMBER}...`);
            const pairingCode = await client.requestPairingCode(PHONE_NUMBER);
            console.log(`========================================`);
            console.log(`🔑 رمز الاقتران الخاص بك هو: ${pairingCode}`);
            console.log(`========================================`);
            console.log(`أدخل هذا الرمز في تطبيق الواتساب على هاتفك في خيار (ربط الجهاز برقم الهاتف).`);
        }
    } catch (error) {
        console.error('خطأ أثناء طلب رمز الاقتران:', error);
    }
}, 5000);

const userSections = {};

client.on('message', async (message) => {
    const chatId = message.from;
    const text = message.body.trim();

    if (text === '/start' || text === 'القائمة' || text === 'مرحبا') {
        userSections[chatId] = null;
        await message.reply(
            "🔥 *أهلاً بك في بوت دراغون بول عبر الواتساب!*\n\n" +
            "أرسل كود القسم المطلوب أولاً (مثال: `db_z` أو `db_kai` أو `db_classic`)، ثم أرسل رقم الحلقة."
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

client.initialize();
