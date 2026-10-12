import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT,
    ep_number TEXT,
    title TEXT,
    file_id TEXT
)
''')

try:
    cursor.execute("ALTER TABLE episodes ADD COLUMN title TEXT")
    conn.commit()
except Exception:
    pass

cursor.execute('''
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
''')
conn.commit()

DEFAULT_ADMIN = 7080361795
cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (DEFAULT_ADMIN,))
conn.commit()

default_links = {
    "telegram_1": "",
    "telegram_2": "",
    "whatsapp_1": "",
    "whatsapp_2": "",
    "facebook_1": "",
    "facebook_2": "",
    "youtube_1": "",
    "youtube_2": "",
    "force_sub": "on"
}

for key, val in default_links.items():
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
conn.commit()
TITLES_DB = {
    "db_classic": {
        1: "سر كرات التنين (Secret of the Dragon Balls)",
        2: "رغبة الإمبراطور (Emperor Pilaf's Wish)",
        3: "لغز السلحفاة (The Turtle's Request)",
        4: "أويول شيطان الحانات (Oolong the Terrible)",
        5: "يامشا قط الصحراء القوي (Yamcha, the Desert Bandit)",
        6: "زوار منتصف الليل (These Aren't Dragon Balls!)",
        7: "جوهان في جبل فريبان (The Ox-King on Frypan Mountain)",
        8: "كاميهااميها السلحفاة (The Kamehameha Wave)",
        9: "رئيس الحراس أوسا أوغما (Boss Rabbit's Magic Touch)",
        10: "سر كرات التنين المسروقة (The Pilaf Gang's Plot)",
        11: "التنين يخرج أخيراً (The Dragon Appears!)",
        12: "أمنية غوكو (The Wish to Shenron)",
        13: "تحول غوكو المخيف (Goku's Nightmare)",
        14: "منافس جديد (Goku's Rival)",
        15: "فتاة غامضة تُدعى لانش (Seven-Faced Lunch)",
        16: "بداية التدريب الصارم (The Training Begins)",
        17: "التدريب مع المعلم روزي (The Journey to the Tournament)",
        18: "اختبار القوة (The Tournament Begins)",
        19: "المعارك التمهيدية (Preliminary Rounds)",
        20: "التصفيات الكبرى (The Finals: Goku vs. Krillin)",
        21: "المعركة الحامية (Danger in the Air)",
        22: "نهائي البطولة الكبرى (The Final Match: Goku vs. Jackie Chun)",
        23: "القوة القصوى لجاكي شان (The Fiercest Battle on Earth)",
        24: "الكاميهااميها العظمى (Goku's Counterattack)",
        25: "المعركة النهائية (The Decisive Blow)",
        26: "ختام البطولة (The End of the Tournament)",
        27: "عودة جيش الشريط الأحمر (The Red Ribbon Army)",
        28: "البحث يبدأ من جديد (Terror in Pirate Cave)",
        29: "السقوط في الفخ (The Red Ribbon Army)",
        30: "مغامرة بيل في البرد (Pilaf and the Red Ribbon Army)",
        31: "معركة البرج العالي (The Muscle Tower)",
        32: "رجل القوة العظمى (The Secret of Muscle Tower)",
        33: "الهكر الألي (The Android No. 8)",
        34: "وداعاً أيها البرج العسكري (The Death of Ninja Murasaki)",
        35: "الوحش بويون (The Monster Buyon)",
        36: "معركة الجنرال وايت (The Battle of Muscle Tower)",
        37: "السفر إلى قرية جينجر (The Village of Jingle)",
        38: "القراصنة والكنز المدفون (The Pirate Treasure)",
        39: "الغواصة السرية (Blue's Counterattack)",
        40: "مغامرة الكهف (The Secret Cave)",
        41: "الهروب الكبير (The Trap Is Sprung)",
        42: "مطاردة الكنز (The Runaway Submarine)",
        43: "قرية بينغوين وعالم أرالي (A Visit to Penguin Village)",
        44: "مغامرة أرالي (The Secret of Arale)",
        45: "نهاية ملاحقة الجنرال بلو (General Blue's Last Stand)",
        46: "المرتزق تاو (The Mercenary Tao)",
        47: "مواجهة تاو باي باي (The Battle at Karin Tower)",
        48: "مياه الإله (The Sacred Water)",
        49: "عودة غوكو القوية (Goku's Revenge)",
        50: "هجوم معبد الشريط الأحمر (The Final Battle)",
        51: "صعود برج كارين (Karin Tower)",
        52: "سر عرافة بابا (Fortuneteller Baba)",
        53: "المحاربون الخمسة الغامضون (The Five Fighters)",
        54: "معركة حمام الدم (The Bloodbath)",
        55: "بطل غير متوقع (The Invicible Devilman)",
        56: "سر المقاتل المقنع (The Masked Fighter)",
        57: "الجد غوهان (Grandpa Gohan)",
        58: "قصر الإمبراطور بيل (Pilaf and the Dragon Balls)",
        59: "مسيرة الشياطين (The Devil's Rebirth)",
        60: "الهجوم على القلعة (The Secret of the Pyramid)",
        61: "كرات التنين تظهر (The Pilaf Gang's Trap)",
        62: "رحلة العودة (The Search for the Last Ball)",
        63: "معركة الجسر (Goku's Wish)",
        64: "المعركة الكبرى (The Tournament of Power Begins)",
        65: "البطل الجديد (The New Hero)",
        66: "معركة الحلبة (The Ring of Fire)",
        67: "النهاية السعيدة (The Dragon's Return)",
        68: "لقاء الأصدقاء (The 22nd World Tournament)",
        69: "التصفيات تبدأ (The Preliminaries)",
        70: "المعارك النارية (The Eight Finalists)",
        71: "يامشا ضد تين شين هان (Yamcha vs. Tien)",
        72: "مفاجأة البطولة (The Secret of Tien)",
        73: "بيكو ضد المطرقة (Goku vs. Krillin)",
        74: "بيكو في مواجهة تين شين هان (Goku vs. Tien)",
        75: "القتال الشرس (The Final Match Begins)",
        76: "الكاميهااميها العظمى (The Ultimate Attack)",
        77: "المعركة الحاسمة (The Winner)",
        78: "خطر الملك الدايماو (Terror from the Sky)",
        79: "سر الملك الدايماو (The Mystery of King Piccolo)",
        80: "مأساة الكريشان (Krillin's Death)",
        81: "غضب غوكو (Goku's Vengeance)",
        82: "مغامرة يادجيروبي (Yajirobe Appears)",
        83: "عودة الشرير الأكبر (The Demon King's Return)",
        84: "بيكو في مواجهة تامبورين (Goku vs. Tambourine)",
        85: "رحلة الشفاء (Karin's Test)",
        86: "ظهور موتشي (Muten Roshi's Last Stand)",
        87: "خطة المعلم روزي الفاشلة (The Mafuba)",
        88: "عودة الملك للحياة (King Piccolo's Youth)",
        89: "الهجوم على العاصمة (The Attack on the Capital)",
        90: "عرش الملك الشرير (King Piccolo's Palace)",
        91: "مياه الآلهة المقدسة (Goku's Power Up)",
        92: "غوكو يصل إلى القصر (Goku's Counterattack)",
        93: "المعركة الأخيرة تبدأ (Goku vs. King Piccolo)",
        94: "الضربات القاضية (The Final Battle)",
        95: "تضحية غوكو (Goku's Sacrifice)",
        96: "أمنية السيد بو (Mr. Popo's Training)",
        97: "بناء كرات التنين من جديد (The Dragon Is Reborn)",
        98: "عودة غوكو (Goku's Return)",
        99: "اختبار الإله (Kami's Test)",
        100: "السفر عبر الزمن للتدريب (The Training of Kami)",
        101: "عودة بيكو الشاب (The Rebirth of Goku)",
        102: "لقاء بعد سنوات (The 23rd World Tournament)",
        103: "الفتاة الغامضة تشي تشي (Chichi's Secret)",
        104: "حبوب الفاصوليا السحرية (The Promise)",
        105: "التصفيات النهائية الكبرى (The Eight Finalists)",
        106: "معركة تين شين هان وتاو (Tien vs. Tao)",
        107: "غوكو ضد تشي تشي (Goku vs. Chi-Chi)",
        108: "بيكوولو الابن ضد كرين (Goku vs. Piccolo Jr.)",
        109: "معركة نصف النهائي (The Semifinals Begin)",
        110: "غوكو ضد شين (Goku vs. Shen)",
        111: "القتال الحاسم (Goku's True Power)",
        112: "نهائي البطولة الكبرى (The Final Match Begins)",
        113: "بيكو في مواجهة بيكولو (Goku vs. Piccolo)",
        114: "المعركة الجوية (The Sky Battle)",
        115: "الصدمة الكبرى (Goku's Defeat)",
        116: "اللحظة الأخيرة (Goku's Counterattack)",
        117: "الفوز الأخير (The Winner)",
        118: "زواج غوكو وتشي تشي (The Wedding)",
        119: "عروس الشيطان (The Fire-Eater)",
        120: "مغامرة جبل فريبان (The Magic Furnace)",
        121: "شبح القلعة (The Ghost of the Castle)",
        122: "الحصار الكبير (The Escape)",
        123: "رحلة العشاق (The Wedding Dress)",
        124: "قطار الجحيم (The Train of Doom)",
        125: "الهجوم الأخير (The Final Challenge)",
        126: "نهاية الكلاسيكي وبداية الملحمة (The End of the Journey)"
    },
    "db_kai1": {
        1: "ظهور مقاتل جديد! هويّة غوكو المذهلة",
        2: "العدو هو شقيق غوكو الأكبر! حقيقة محاربي الفضاء السيانز",
        3: "النصر بالتحالف! أقوى رجلين في العالم يقاتلان معاً",
        4: "بطاقة ترامب لبيكو! هجوم الكاميهااميها اليائس",
        5: "تضحية غوكو! المعركة الأخيرة بلمسة واحدة",
        6: "إهداء من الآخرة! طريق كايو الطويل",
        7: "التدريب تحت جازية الثقل! مطاردة البابلي",
        8: "ظهور المقاتل الأسطوري! بيكو وغوهان تحت الاختبار",
        9: "رحلة جوعان مع الصداقة! دموع في الصحراء",
        10: "بداية المعركة الحقيقية! وصول السيانز",
        11: "هزيمة يامشا! رعب زراعة السابايمان",
        12: "وداعاً تشاوستي! تضحية الشجاعة الأخيرة",
        13: "تين شين هان يبذل قصارى جهده! هجوم الكيهوكو الأخير",
        14: "معركة يائسة! تأخير وصول غوكو حتى النهاية",
        15: "غضب غوكو يشتعل! نهاية نابا المغرور",
        16: "المواجهة الكبرى في الأراضي الوعرة! غوكو ضد فيجيتا",
        17: "دفع الحدود إلى أقصاها! الكايوكن الثلاثية",
        18: "تراجع فيجيتا! طاقة غوكو تصل لحافتها",
        19: "ضربة الرحمة! أمل كوكب الأرض الأخير",
        20: "الإقلاع نحو الفضاء! كوكب ناميك في الانتظار السفلي",
        21: "مفاجأة في الكوكب البعيد! سفينة الفضاء الغامضة",
        22: "الهبوط الخطير في ناميك! أعداء جدد في الأفق",
        23: "ظهور كابوس الفضاء! فريزا يبسط سيطرته",
        24: "أصدقاء أم أعداء؟ الكشف عن نوايا فيجيتا",
        25: "استرجاع كرات التنين! بيكو يستعرض قوته",
        26: "مأساة قرية ناميك! غضب غوهان الصامت",
        27: "المعركة المشتعلة على كرات التنين! فيجيتا في مواجهة دودوريا",
        28: "سر كرات التنين الكبرى! ظهور زاربون المرعب",
        29: "تحول زاربون الوحشي! هزيمة فيجيتا الأولى",
        30: "تدريب فيجاكا السري! استعادة القوة المدمرة",
        31: "قوة كرين الخارقة! فتح القدرات الكامنة على يد الحكيم",
        32: "صراع الأقوياء في سفينة فريزا! فيجيتا ضد زاربون النسخة الثانية",
        33: "قوة فريق جينيو المرعب! فرقة المرتزقة الخاصة تصل",
        34: "مناورات مرعبة في الحقول الخضراء! مواجهة غوهان وكرين مع جودو",
        35: "تحرك فيجيتا السريع! القضاء على جودو وريكوم",
        36: "غوكو يصل أخيراً ميدان المعركة! القوة الجديدة تظهر",
        37: "قوة غوكو المرعبة! هزيمة بورت وجيس بكل سهولة",
        38: "قائد الفرقة يتدخل! الكابتن جينيو في مواجهة غوكو",
        39: "تبديل الأجساد المروّع! غوكو يصبح جينيو",
        40: "استعادة الجسد الأصلي! فخ الإنزلاق الناجح",
        41: "أمنية بورس الإلهية! ظهور التنين الناميكي",
        42: "المعركة تحتد مع فريزا! التحول الأول للوحش",
        43: "غوهان يفقد السيطرة! غضب طفولي يواجه فريزا",
        44: "عودة بيكولو القوية! اتحاد الأبطال على كوكب ناميك",
        45: "تحول فريزا الثاني المخيف! الكابوس يتضاعف",
        46: "فريزا يكشف عن شكله النهائي! بداية الدمار الشامل",
        47: "وصول البطل المنتظر! شفاء غوكو بالكامل",
        48: "المعركة الأسطورية تبدأ! غوكو ضد فريزا وجهاً لوجه",
        49: "تتجاوز الحدود! الكايوكن العشرين ضد فريزا",
        50: "سلاح الملاذ الأخير! قنبلة الروح الكبرى (جينكي داما)",
        51: "انفجار كوكب ناميك الهائل! غوكو يفقد السيطرة",
        52: "ظهور المحارب الأسطوري! غوكو يتحول إلى سوبر سايان لأول مرة",
        53: "انهيار فريزا الأخير! غوكو يرفض الاستسلام",
        54: "نهاية كوكب ناميك المدمر! وداعاً أيتها الأراضي الخضراء",
        55: "عودة فريزا إلى الأرض! المفاجأة المروّعة",
        56: "ظهور الشاب الغامض! ترانكس يهزم فريزا بضربة واحدة",
        57: "اجتماع الأبطال في الأرض! سر هوية ترانكس",
        58: "تدريب الاستعداد للأسوأ! ثلاث سنوات من التحضير",
        59: "ظهور الأندرويد 19 و 20! بداية المعركة في الشتاء",
        60: "قوة فيجيتا الجديدة! تحول السوبر سايان الملكي",
        61: "هزيمة الأندرويد 20! اكتشاف سر الدكتور جيرو الحقيقي",
        62: "استيقاظ الأندرويد 17 و 18! الخطر الحقيقي يقترب",
        63: "معركة الآليين المرعبة! فيجيتا في مواجهة الأندرويد 18",
        64: "اكتشاف السر المظلم! ظهور آلة الزمن الثانية",
        65: "بيكولو يتجاوز الحدود! الاتحاد مع الإله (كامي)",
        66: "الكائن الغريب يظهر! ظهور سيل الغامض في المدينة",
        67: "وحش المستقبل المتعطش للطاقة! مواجهة بيكولو مع سيل",
        68: "امتصاص الأندرويد 17! تطور سيل للشكل الثاني",
        69: "قوة فيجيتا المتفوقة! سيل يقع في فخ الغرور",
        70: "سماح فيجيتا لسيل بالتطور! خطأ العمر القاتل",
        71: "سيل بصورته الكاملة والمثالية! رعب العالم يبدأ",
        72: "صدمة فيجيتا الكبرى! العرض الأولي لقوة سيل التامة",
        73: "بداية بطولة ألعاب سيل (Cell Games)! التحدي العلني للعالم",
        74: "تدريب غرفة الروح والزمن! الآباء والأبناء يتجاوزون الحدود",
        75: "افتتاح ألعاب سيل الرسمية! غوكو في مواجهة سيل",
        76: "غوكو ينسحب بذكاء! مفاجأة إشراك غوهان في المعركة",
        77: "غضب غوهان المكبوت! ظهور السوبر سايان الثاني لأول مرة",
        78: "نهاية سيل الصغير المزيف! غوهان يكتسح الساحة",
        79: "خطة سيل الانتحارية! ضغط النفس للدمار الشامل",
        80: "تضحية غوكو الكبرى! الانتقال الفوري لكوكب الملك كايو",
        81: "عودة سيل بقوة أقوى! التحول المثالي النهائي",
        82: "صراع كاميهااميها الأبدي! غوهان يطلق طاقته القصوى بمساعدة والده",
        83: "نهاية سيل الأبدية! سلام يعم الأرض من جديد"
    },
    "db_kai2": {
        1: "بعد سبع سنوات! غوهان يبدأ دراسته الثانوية كبطل خارق",
        2: "ظهور فتاة الغموض فيديل! اكتشاف هوية غريت سايامان",
        3: "التسجيل في بطولة العالم للمقاتلين! عودة غوكو المؤقتة من الآخرة",
        4: "صدمة الأصدقاء في التدريبات! إصرار جوتن وكييد ترانكس",
        5: "انطلاق التصفيات التمهيدية! منافسة الأقوياء تبدأ",
        6: "بطل العالم للناشئين! ترانكس يواجه غوتين في النهائي",
        7: "بدء منافسات الكبار! ظهور الشخصيات الغامضة شين وكابيتو",
        8: "خوف غوهان المفاجئ! سبوبوفيتش يكشف عن قوته الغريبة",
        9: "سر الطاقة المسروقة! هجوم الأشرار على غوهان",
        10: "انطلاق الأبطال نحو سفينة بابيدي السرية! كشف خطة السحر المظلم",
        11: "معركة يامو وسبوبوفيتش! الوقوع في فخ الساحر بابيدي",
        12: "غوهان في مواجهة داربرا ملك الشياطين! قتال محتدم داخل المركبة",
        13: "سقوط فيجيتا في فخ الشر! سيطرة بابيدي وتحوله إلى ماجين فيجيتا",
        14: "عودة الصراع القديم! غوكو في مواجهة فيجيتا وجهاً لوجه",
        15: "ذروة المعركة بين الصديقين! قوة سوبر سايان 2 تزلزل الأرض",
        16: "طاقة المعركة توقظ الكابوس! اكتمال عداد إيقاظ ماجين بو",
        17: "ظهور ماجين بو المرعب! الشكل الغريب للشر المطلق",
        18: "قوة ماجين بو المدمرة تفوق التوقعات! هزيمة داربرا بسهولة",
        19: "تضحية فيجيتا البطولية! الانفجار العظيم لإنقاذ العائلة والأرض",
        20: "استيقاظ الجميع بعد الكارثة! بيكولو يبحث عن الناجين",
        21: "فكرة الاندماج العجيبة! غوكو يعلم الأطفال تقنية الفيوجن",
        22: "تدمير قاعدة بابيدي! غوكو يستعرض قوة سوبر سايان 3 أمام ماجين بو",
        23: "عودة غوكو إلى عالم الأرواح! الوقت ينفد بسرعة",
        24: "أسرار السيف الأسطوري (Z-Sword)! جوتن وترانكس في عالم الكايوشين",
        25: "مدينة ستان تشتعل بالدمار! ماجين بو يغير مظهره الشرير",
        26: "ولادة بو الشرير النحيف! الصراع الداخلي للوحش",
        27: "ابتلاع بو الطيب! تحول الكابوس إلى الشكل الخارق المرعب (Super Buu)",
        28: "اقتحام قصر المراقبة الإلهي! بو يطالب بمواجهة الأقوياء",
        29: "دخول غرفة الروح والزمن! جوتنكس يبدأ التدريب الحاسم",
        30: "قوة جوتنكس الخارقة الجديدة! الوصول إلى مستوى سوبر سايان 3 داخل الغرفة",
        31: "هروب بو من البعد الآخر! بيكولو يخدع الشرير بذكاء",
        32: "هجوم جوتنكس الأخير! تقنية كاتينا في مواجهة بو",
        33: "امتصاص جوتنكس وبيكولو! بو يصبح في أقوى أشكاله على الإطلاق",
        34: "عودة جوهان الأسطورية مع القوة المطلقة! غوهان المقتدر يصل الميدان",
        35: "تفوق غوهان الكسح على بو! الشرير يلجأ لحيلة اليأس",
        36: "انفجار بو الماكر! امتصاص غوهان وجوتنكس معاً",
        37: "تضحية الكايوشين الأكبر! إهداء حياة غوكو للعودة للأرض",
        38: "استخدام أقراط بورتارا الإلهية! ولادة المحارب الأسطوري فاجيتو (Vegito)",
        39: "فاجيتو يذل بو الخارق! المعركة من طرف واحد",
        40: "امتصاص فاجيتو المتوقع! الدخول إلى داخل جسم ماجين بو عمداً",
        41: "إنقاذ المخطوفين من أحشاء الشرير! تحرير غوهان وبقية الأطفال",
        42: "التدهور المرعب لبو! العودة إلى الشكل الأصلي الأول (Kid Buu)",
        43: "تدمير كوكب الأرض بالكامل! كايوشين ينقذ غوكو وشركائه في اللحظة الأخيرة",
        44: "المعركة الكبرى على كوكب الكايوشين! غوكو في مواجهة كيد بو وجهاً لوجه",
        45: "إعياء غوكو في سوبر سايان 3! فيجيتا يتدخل لإنقاذ الموقف بمعركة شاقة",
        46: "خطة بيل الكبرى! تجميع طاقة سكان الأرض عبر كرات التنين",
        47: "إطلاق قنبلة الروح الكبرى (جينكي داما) النهائية! أمل الكون الأخير",
        48: "كلمات غوكو المؤثرة ونهاية الشر المطلق! انتصار الخير والعدالة الأبدي"
    },
    "db_super": {
        1: "جائزة السلام العالمي! من سيحصل على المليار زيني؟",
        2: "إلى منتجع العطلات! رحلة عائلة فيجيتا إلى الشاطئ",
        3: "البحث عن سوبر سايان غود! هل يعرف إله الدمار شيئاً؟",
        4: "الهدف هو كرات التنين! معركة الإمبراطور بيل في كوكب الكايوشين",
        5: "المعركة في كوكب الملك كايو! غوكو في مواجهة إله الدمار بيروس",
        6: "لا تغضب إله الدمار! درس قاسي في غرفة المعلم كايو",
        7: "ظهور إله الدمار بيروس في كوكب الأرض! البحث عن المقاتل الأسطوري",
        8: "غوكو يعود من جديد! تحول سوبر سايان غود يلوح في الأفق",
        9: "ظهور سوبر سايان غود أخيرًا! طاقة الأساطير تشتعل",
        10: "غوكو يواجه بيروس! المعركة التي تزلزل الكون",
        11: "دعنا نستمر يا إله الدمار بيروس! معركة الكون على المحك",
        12: "الكون يتحطم بفعل الصدمات! هل ينهار العالم؟",
        13: "غوكو يتخطى طاقة الإله! المحاولة الأخيرة الحاسمة",
        14: "نهاية المعركة الأسطورية! طاقة السلام تعود من جديد",
        15: "بطل الشيطان العظيم! سورو يبحث عن كرات التنين",
        16: "بداية التدريب السري! غوكو وغوهان تحت إمرة ويس",
        17: "ولادة فتاة السراب! ظهور البنت الغامضة ومغامرة المخبأ",
        18: "وصول جيش فريزا المرعب إلى الأرض! 1000 مقاتل في مواجهة الأصدقاء",
        19: "غوهان في اختبار قاسي! جيش الفريزا يهاجم بقسوة",
        20: "عودة فريزا المرعبة! الانتقام يبدأ الآن",
        21: "فريزا يواجه غوهان! قوة التحول الجديد تكشف عن نفسها",
        22: "قوة سوريبا وغوهان تصل للحدود! تدخل بيكولو البطولي",
        23: "الأرض في خطر داهم! غوكو وغويتا يستشعران الكارثة في الفضاء",
        24: "عودة غوكو وفيجيتا الفورية! المواجهة المرتقبة مع فريزا",
        25: "المعركة الحاسمة تبدأ! سوبر سايان بلو في مواجهة فريزا الذهبي",
        26: "نقطة ضعف فريزا تظهر! الصراع يحتدم على حافة الهاوية",
        27: "تدمير الأرض والإنقاذ العجيب! تراجع الزمن على يد ويس ونهاية فريزا",
        28: "التحدي الكبير بين الحاكمين! إشاعتان عن بطولات الأكوان",
        29: "التحضير لبطولة الفضاء! غوكو وفيجيتا يجمعان الفريق الخارق",
        30: "التدريب المشترك قبل المعركة! من هم أعضاء فريق الكون السابع؟",
        31: "السفر إلى كوكب النون! لقاء حكام الأكوان وزينو ساما",
        32: "بداية مباريات البطولة الكبرى! الكون السابع في مواجهة الكون السادس",
        33: "قوة فرست الصاعقة! بوتامو ومجيتو في مواجهة غوكو وفيجيتا",
        34: "معركة السيانز الحماسية! غوكو في مواجهة كابا الذكي",
        35: "سلاح فيجيتا السري! تحول سوبر سايان بلو في مواجهة هيت",
        36: "هزيمة فيجيتا المفاجئة! مهارة تخطي الوقت الغامضة لهيت",
        37: "إصرار سايان كوكب السادسة! كابا يشعل الحماس",
        38: "غوكو يواجه هيت القاتل! بداية النزال الأقوى في البطولة",
        39: "قوة الكايوكن المدمجة مع سوبر سايان بلو! غوكو يتخطى المستحيل",
        40: "نهاية البطولة بفوز مذهل! ظهور شخصية زينو"
    }
}
def get_setting(key):
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else ""

def update_setting(key, value):
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()

def is_admin(user_id):
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def get_section_count(section_code):
    cursor.execute("SELECT COUNT(*) FROM episodes WHERE section = ?", (section_code,))
    row = cursor.fetchone()
    return row[0] if row else 0

def get_subscription_keyboard():
    keyboard = []
    link_mapping = [
        ("telegram_1", "📢 قناة التليجرام 1"),
        ("telegram_2", "📢 قناة التليجرام 2"),
        ("whatsapp_1", "💬 قناة الواتساب 1"),
        ("whatsapp_2", "💬 قناة الواتساب 2"),
        ("facebook_1", "🌐 جروب الفيسبوك 1"),
        ("facebook_2", "🌐 جروب الفيسبوك 2"),
        ("youtube_1", "📺 قناة اليوتيوب 1"),
        ("youtube_2", "📺 قناة اليوتيوب 2"),
    ]
    for key, text in link_mapping:
        link_val = get_setting(key)
        if link_val and link_val.strip() != "":
            keyboard.append([InlineKeyboardButton(text, url=link_val)])
    keyboard.append([InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    force_sub_status = get_setting("force_sub")
    
    if force_sub_status == "on" and user and not is_admin(user.id):
        reply_markup = get_subscription_keyboard()
        if len(reply_markup.inline_keyboard) == 1:
            await show_main_menu(update)
            return
        await update.message.reply_text(
            "أهلاً بك يا غالي! 😊\n"
            "للاستمرار واستخدام البوت، نرجو منك الانضمام إلى القنوات والروابط أولاً، ثم اضغط على زر (تحقق من الاشتراك):",
            reply_markup=reply_markup
        )
        return
    await show_main_menu(update)

async def show_main_menu(update: Update):
    c_classic = get_section_count("db_classic")
    c_kai1 = get_section_count("db_kai1")
    c_kai2 = get_section_count("db_kai2")
    c_super = get_section_count("db_super")
    c_gt = get_section_count("db_gt")
    c_daima = get_section_count("db_daima")
    c_heroes = get_section_count("db_heroes")
    c_super_remake = get_section_count("db_super_remake")
    c_specials = get_section_count("db_specials")
    c_movies = get_section_count("db_movies")

    keyboard = [
        [InlineKeyboardButton(f"🐉 الكلاسيكي ({c_classic})", callback_data="db_classic"), InlineKeyboardButton(f"⚡ كاي الأول ({c_kai1})", callback_data="db_kai1")],
        [InlineKeyboardButton(f"⚔️ زد كاي 2 ({c_kai2})", callback_data="db_kai2"), InlineKeyboardButton(f"🔥 سوبر ({c_super})", callback_data="db_super")],
        [InlineKeyboardButton(f"🌀 جي تي ({c_gt})", callback_data="db_gt"), InlineKeyboardButton(f"✨ دايما ({c_daima})", callback_data="db_daima")],
        [InlineKeyboardButton(f"💫 هيروز ({c_heroes})", callback_data="db_heroes"), InlineKeyboardButton(f"✨ سوبر ريمك ({c_super_remake})", callback_data="db_super_remake")],
        [InlineKeyboardButton(f"⭐ الحلقات الخاصة ({c_specials})", callback_data="db_specials"), InlineKeyboardButton(f"🎬 الأفلام ({c_movies})", callback_data="db_movies")],
        [InlineKeyboardButton("📖 معلومات الأقسام والحلقات المتوفرة", callback_data="bot_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        "مرحباً بك في بوت أنمي دراغون بول الرسمي! 🌟\n"
        "اختر القسم المطلوب من الأزرار بالأسفل لتصفح الحلقات بكل سهولة:"
    )
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        if update.message:
            await update.message.reply_text("عذراً، هذا الأمر مخصص للمشرفين فقط. 🌸")
        return

    force_sub_status = get_setting("force_sub")
    status_text = "🟢 مفعل" if force_sub_status == "on" else "🔴 معطل"
    
    keyboard = [
        [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
        [InlineKeyboardButton("➕ إضافة حلقات جديدة (اختر القسم)", callback_data="admin_sections_menu")],
        [InlineKeyboardButton("✏️ تعديل وإدارة أرقام والحلقات", callback_data="edit_episodes_menu")],
        [InlineKeyboardButton("👤 إضافة مطور / متحكم جديد", callback_data="add_admin_prompt")],
        [InlineKeyboardButton("🔗 إضافة وتعديل الروابط للمنصات", callback_data="admin_links_menu")],
        [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    admin_text = "🎛️ أهلاً بك في لوحة تحكم الأدمن المباشرة:\n\nاختر ما تريد فعله من الأزرار بالأسفل:"
    if update.message:
        await update.message.reply_text(admin_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(admin_text, reply_markup=reply_markup)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    user_id = user.id if user else 0

    if data == "toggle_sub":
        if not is_admin(user_id):
            return
        current_status = get_setting("force_sub")
        new_status = "off" if current_status == "on" else "on"
        update_setting("force_sub", new_status)
        status_txt = "🟢 مفعل" if new_status == "on" else "🔴 معطل"
        
        keyboard = [
            [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_txt}", callback_data="toggle_sub")],
            [InlineKeyboardButton("➕ إضافة حلقات جديدة (اختر القسم)", callback_data="admin_sections_menu")],
            [InlineKeyboardButton("✏️ تعديل وإدارة أرقام والحلقات", callback_data="edit_episodes_menu")],
            [InlineKeyboardButton("👤 إضافة مطور / متحكم جديد", callback_data="add_admin_prompt")],
            [InlineKeyboardButton("🔗 إضافة وتعديل الروابط للمنصات", callback_data="admin_links_menu")],
            [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.message.reply_text(f"تم تغيير حالة الاشتراك الإجباري لتصبح: {status_txt} 👍")
        return

    elif data == "bot_info":
        sections = [
            ("db_classic", "الكلاسيكي"),
            ("db_kai1", "دراغون بول كاي - الجزء الأول"),
            ("db_kai2", "دراغون بول زد كاي - الجزء الثاني"),
            ("db_super", "دراغون بول سوبر"),
            ("db_gt", "دراغون بول جي تي"),
            ("db_daima", "دراغون بول دايما"),
            ("db_heroes", "سوبر دراغون بول هيروز"),
            ("db_super_remake", "سوبر ريمك"),
            ("db_specials", "الحلقات الخاصة"),
            ("db_movies", "الأفلام السينمائية")
        ]
        info_msg = "معلومات الأقسام وحالة الحلقات المتوفرة في البوت:\n\n"
        for code, name in sections:
            cnt = get_section_count(code)
            info_msg += f"• {name}: تم رفع {cnt} حلقة متوفرة ✅\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_main")]]
        await query.message.edit_text(info_msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data == "back_to_main":
        await show_main_menu(update)
        return

    elif data == "add_admin_prompt":
        if not is_admin(user_id):
            return
        context.user_data['waiting_for_new_admin'] = True
        await query.message.reply_text(
            "👤 **إضافة مطور أو متحكم جديد:**\n\n"
            "أرسل الآن (آي دي / ID) الشخص المراد إضافته كأدمن في رسالة جديدة:"
        )
        return

    elif data == "edit_episodes_menu":
        if not is_admin(user_id):
            return
        keyboard = [
            [InlineKeyboardButton("🗑️ حذف حلقة محددة", callback_data="delete_ep_prompt")],
            [InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")]
        ]
        await query.message.reply_text(
            "✏️ **تعديل وإدارة الحلقات:**\n\n"
            "اختر الإجراء المطلوب:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    elif data == "delete_ep_prompt":
        if not is_admin(user_id):
            return
        context.user_data['waiting_for_delete_ep'] = True
        await query.message.reply_text(
            "🗑️ **حذف حلقة:**\n\n"
            "أرسل اسم القسم ورقم الحلقة هكذا مثال:\n`db_super 5`\nأو رقم الحلقة مباشرة إذا كنت قد حددت القسم مسبقاً."
        )
        return

    elif data == "admin_sections_menu":
        if not is_admin(user_id):
            return
        c_classic = get_section_count("db_classic")
        c_kai1 = get_section_count("db_kai1")
        c_kai2 = get_section_count("db_kai2")
        c_super = get_section_count("db_super")
        c_gt = get_section_count("db_gt")
        c_daima = get_section_count("db_daima")
        c_heroes = get_section_count("db_heroes")
        c_super_remake = get_section_count("db_super_remake")
        c_specials = get_section_count("db_specials")
        c_movies = get_section_count("db_movies")
        
        keyboard = [
            [InlineKeyboardButton(f"🐉 الكلاسيكي ({c_classic})", callback_data="upload_sec_db_classic"), InlineKeyboardButton(f"⚡ كاي 1 ({c_kai1})", callback_data="upload_sec_db_kai1")],
            [InlineKeyboardButton(f"⚔️ زد كاي 2 ({c_kai2})", callback_data="upload_sec_db_kai2"), InlineKeyboardButton(f"🔥 سوبر ({c_super})", callback_data="upload_sec_db_super")],
            [InlineKeyboardButton(f"🌀 جي تي ({c_gt})", callback_data="upload_sec_db_gt"), InlineKeyboardButton(f"✨ دايما ({c_daima})", callback_data="upload_sec_db_daima")],
            [InlineKeyboardButton(f"💫 هيروز ({c_heroes})", callback_data="upload_sec_db_heroes"), InlineKeyboardButton(f"✨ ريمك ({c_super_remake})", callback_data="upload_sec_db_super_remake")],
            [InlineKeyboardButton(f"⭐ الخاصة ({c_specials})", callback_data="upload_sec_db_specials"), InlineKeyboardButton(f"🎬 الأفلام ({c_movies})", callback_data="upload_sec_db_movies")],
            [InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")]
        ]
        await query.message.edit_text("📂 **اختر القسم الذي تريد إضافة حلقات إليه:**", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("upload_sec_"):
        if not is_admin(user_id):
            return
        section_code = data.replace("upload_sec_", "")
        context.bot_data[f'admin_sec_{user_id}'] = section_code
        await query.message.reply_text(
            "✅ تم اختيار القسم بنجاح.\n\n"
            "الآن **أرسل الحلقات مباشرة (كفيديوهات أو ملفات)** وسيقوم البوت بالتعرف على رقمها وحفظها تلقائياً! 🚀"
        )
        return

    elif data == "admin_links_menu":
        if not is_admin(user_id):
            return
        keyboard = [
            [InlineKeyboardButton("📢 تليجرام 1", callback_data="edit_link_telegram_1"), InlineKeyboardButton("📢 تليجرام 2", callback_data="edit_link_telegram_2")],
            [InlineKeyboardButton("💬 واتساب 1", callback_data="edit_link_whatsapp_1"), InlineKeyboardButton("💬 واتساب 2", callback_data="edit_link_whatsapp_2")],
            [InlineKeyboardButton("🌐 فيسبوك 1", callback_data="edit_link_facebook_1"), InlineKeyboardButton("🌐 فيسبوك 2", callback_data="edit_link_facebook_2")],
            [InlineKeyboardButton("📺 يوتيوب 1", callback_data="edit_link_youtube_1"), InlineKeyboardButton("📺 يوتيوب 2", callback_data="edit_link_youtube_2")],
            [InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="back_to_admin")]
        ]
        await query.message.edit_text("🔗 **اختر الرابط الذي تريد تعديله:**", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("edit_link_"):
        if not is_admin(user_id):
            return
        link_type = data.replace("edit_link_", "")
        context.user_data['waiting_for_link'] = link_type
        await query.message.reply_text(f"أرسل الآن الرابط الجديد لـ ({link_type}) في رسالة:\n*(أرسل `حذف` لإزالته)*")
        return

    elif data == "back_to_admin":
        if not is_admin(user_id):
            return
        force_sub_status = get_setting("force_sub")
        status_text = "🟢 مفعل" if force_sub_status == "on" else "🔴 معطل"
        keyboard = [
            [InlineKeyboardButton(f"حالة الاشتراك الإجباري: {status_text}", callback_data="toggle_sub")],
            [InlineKeyboardButton("➕ إضافة حلقات جديدة (اختر القسم)", callback_data="admin_sections_menu")],
            [InlineKeyboardButton("✏️ تعديل وإدارة أرقام والحلقات", callback_data="edit_episodes_menu")],
            [InlineKeyboardButton("👤 إضافة مطور / متحكم جديد", callback_data="add_admin_prompt")],
            [InlineKeyboardButton("🔗 إضافة وتعديل الروابط للمنصات", callback_data="admin_links_menu")],
            [InlineKeyboardButton("📋 عرض ونسخ قائمة الحلقات", callback_data="list_episodes")],
        ]
        await query.message.edit_text("🎛️ أهلاً بك في لوحة تحكم الأدمن المباشرة:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data == "list_episodes":
        if not is_admin(user_id):
            return
        cursor.execute("SELECT section, ep_number FROM episodes ORDER BY section, CAST(ep_number AS INTEGER)")
        rows = cursor.fetchall()
        if not rows:
            await query.message.reply_text("لا توجد أي حلقات مرفوعة حتى الآن يا غالي. 🌸")
            return
        result_msg = "📋 **قائمة الحلقات المحفوظة دائمًا:**\n\n"
        current_section = ""
        for section, ep_number in rows:
            if section != current_section:
                current_section = section
                result_msg += f"\n📂 **القسم: `{section}`**\n"
            auto_title = TITLES_DB.get(section, {}).get(int(ep_number) if ep_number.isdigit() else ep_number, "")
            t_str = f" - {auto_title}" if auto_title else ""
            result_msg += f"• حلقة {ep_number}{t_str}\n"
        if len(result_msg) > 4000:
            for i in range(0, len(result_msg), 4000):
                await query.message.reply_text(result_msg[i:i+4000], parse_mode="Markdown")
        else:
            await query.message.reply_text(result_msg, parse_mode="Markdown")
        return

    elif data == "check_sub":
        await show_main_menu(update)
        return

    section = data
    context.user_data['selected_section'] = section
    await query.message.reply_text("تم اختيار القسم بنجاح! 🎯\nالرجاء إرسال رقم الحلقة المطلوبة الآن (مثال: 1 أو 5):")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.effective_user
    user_id = user.id if user else 0

    if is_admin(user_id) and context.user_data.get('waiting_for_new_admin') and update.message.text:
        text = update.message.text.strip()
        context.user_data.pop('waiting_for_new_admin', None)
        if text.isdigit():
            new_admin_id = int(text)
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (new_admin_id,))
            conn.commit()
            await update.message.reply_text(f"✅ تم إضافة الآي دي ({new_admin_id}) كمطور/متحكم جديد بنجاح! 🚀")
        else:
            await update.message.reply_text("⚠️ يرجى إرسال رقم الآي دي صحيحاً ومكوناً من أرقام فقط.")
        return

    if is_admin(user_id) and context.user_data.get('waiting_for_delete_ep') and update.message.text:
        text = update.message.text.strip()
        context.user_data.pop('waiting_for_delete_ep', None)
        parts = text.split()
        if len(parts) == 2:
            sec, ep = parts[0], parts[1]
            cursor.execute("DELETE FROM episodes WHERE section = ? AND ep_number = ?", (sec, ep))
            conn.commit()
            await update.message.reply_text(f"🗑️ تم حذف الحلقة ({ep}) من القسم ({sec}) بنجاح.")
        else:
            await update.message.reply_text("⚠️ الصيغة غير صحيحة. أرسل هكذا مثلاً: `db_super 5`")
        return

    if is_admin(user_id) and 'waiting_for_link' in context.user_data and update.message.text:
        text = update.message.text.strip()
        link_type = context.user_data.pop('waiting_for_link')
        new_link = "" if text.lower() in ["حذف", "empty", "none", "-"] else text
        update_setting(link_type, new_link)
        await update.message.reply_text(f"تم تحديث رابط ({link_type}) بنجاح! 🚀")
        return

    if is_admin(user_id) and f'admin_sec_{user_id}' in context.bot_data:
        media_file = update.message.video or update.message.document
        if media_file:
            section = context.bot_data[f'admin_sec_{user_id}']
            file_id = media_file.file_id
            caption = update.message.caption or media_file.file_name or ""
            
            numbers = re.findall(r'\d+', caption)
            if numbers:
                ep_number = numbers[0]
                auto_title = TITLES_DB.get(section, {}).get(int(ep_number) if ep_number.isdigit() else ep_number, "")
                
                cursor.execute("SELECT id FROM episodes WHERE section = ? AND ep_number = ?", (section, ep_number))
                row = cursor.fetchone()
                if not row:
                    cursor.execute("INSERT INTO episodes (section, ep_number, title, file_id) VALUES (?, ?, ?, ?)", (section, ep_number, auto_title, file_id))
                    conn.commit()
                    await update.message.reply_text(f"✅ تم حفظ الحلقة ({ep_number}) تلقائياً!")
                else:
                    cursor.execute("UPDATE episodes SET title = ?, file_id = ? WHERE section = ? AND ep_number = ?", (auto_title, file_id, section, ep_number))
                    conn.commit()
                    await update.message.reply_text(f"🔄 تم تحديث الحلقة ({ep_number}) بنجاح!")
            else:
                await update.message.reply_text("⚠️ لم يتم العثور على رقم في اسم أو وصف الملف لكي يتم استخراجه وحفظه تلقائياً.")
            return

    if not update.message.text:
        return
        
    text = update.message.text.strip()
    force_sub_status = get_setting("force_sub")
    
    if force_sub_status == "on" and not is_admin(user_id):
        reply_markup = get_subscription_keyboard()
        if len(reply_markup.inline_keyboard) == 1:
            await show_main_menu(update)
            return
        await update.message.reply_text(
            "أهلاً بك يا غالي! 😊\n"
            "للاستمرار واستخدام البوت، نرجو منك الانضمام إلى القنوات والروابط أولاً، ثم اضغط على زر (تحقق من الاشتراك):",
            reply_markup=reply_markup
        )
        return
    
    if 'selected_section' in context.user_data:
        section = context.user_data['selected_section']
        cursor.execute("SELECT file_id, title FROM episodes WHERE section = ? AND ep_number = ?", (section, text))
        row = cursor.fetchone()
        if row:
            file_id, title = row[0], row[1]
            if not title:
                title = TITLES_DB.get(section, {}).get(int(text) if text.isdigit() else text, "")
            title_str = f" - {title}" if title else ""
            await update.message.reply_video(video=file_id, caption=f"🎬 الحلقة رقم ({text}){title_str} - متوفرة ✅")
        else:
            await update.message.reply_text(f"عذراً، الحلقة رقم ({text}) غير متوفرة في هذا القسم حالياً ❌. 🌸")
    else:
        if update.effective_chat.type in ["group", "supergroup"]:
            return
        await update.message.reply_text("أهلاً بك! يرجى استخدام الأمر /start للبدء واختيار القسم المناسب. 😊")

def main():
    TOKEN = "8911756458:AAEADtUnJ5pYSv5SshjjXuMUd4GA9TnAMYY"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))

    print("Telegram bot is running smoothly...")
    app.run_polling()

if __name__ == '__main__':
    main()
        
