import gspread
import os
import json
import telebot
from telebot import types
from keep_alive import keep_alive
import time
from credentials_manager import get_google_credentials
from typing import Union

# Type aliases for credentials
try:
    from google.oauth2.service_account import Credentials as ModernCredentials
except ImportError:
    ModernCredentials = None

try:
    from oauth2client.service_account import ServiceAccountCredentials as LegacyCredentials
except ImportError:
    LegacyCredentials = None

# إعداد نطاق الوصول لجوجل شيت
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets"
]

# تهيئة عميل Google Sheets
def initialize_google_client():
    try:
        creds = get_google_credentials()
        if creds:
            # Handle both modern and legacy credential types
            return gspread.authorize(creds)
        else:
            print("❌ لم يتم العثور على بيانات اعتماد Google Sheets")
            return None
    except Exception as e:
        print(f"❌ خطأ في تهيئة عميل Google Sheets: {e}")
        return None

client = initialize_google_client()

# في حالة عدم توفر Google Sheets، استخدم البيانات المحلية
if not client:
    print("⚠️  تحذير: سيتم استخدام البيانات المحلية فقط (بدون Google Sheets)")
    print("💡 لتفعيل Google Sheets، يرجى إضافة GOOGLE_CREDENTIALS صحيح")

# تحميل المواد من أوراق Google Sheets أو البيانات المحلية
def load_subjects_from_sheets():
    try:
        if not client:
            print("❌ عميل Google Sheets غير متاح - استخدام البيانات المحلية")
            # إرجاع بيانات جميع الصفوف الأربعة
            return {
                "الصف 1": {
                    "الترم الأول": ["رسم ميكانيكي", "قضايا مجتمعية", "الفيزياء التطبيقية","السلامة والصحة المهنية","كتابة تقارير فنية (1)","لغة انجليزية","تكنواوجيا الورش (عملي)"],
                    "الترم الثاني": ["رياضيات تطبيقية (1)", "كيمياء صناعية", "تكنولوجيا المعلومات ومعالجة البيانات و احصاء","الرسم فني والتجميعي","التفكير الابداعي والتواصل","مهارات تقني السيارات (عملي I)","أنظمة السيارات","لغة انجليزية فنية (1)"]
                },
                "الصف 2": {
                    "الترم الأول": ["رياضيات تطبيقية (2)", "الرسم بالأتوكاد", "فيزياء تطبيقية (2)", "علوم المواد", "ديناميكا حرارية", "كتابة تقارير فنية (2)", "تكنولوجيا الحاسوب"],
                    "الترم الثاني": ["آليات وتصنيع", "إلكترونيات السيارات", "كهرباء السيارات", "مهارات تقني السيارات (عملي II)", "لحام وقطع المعادن", "قوى الآلات", "إدارة مشاريع"]
                },
                "الصف 3": {
                    "الترم الأول": ["محركات الاحتراق الداخلي", "هندسة المركبات", "أنظمة نقل الحركة", "أنظمة التعليق والتوجيه", "كهرباء متقدمة", "إلكترونيات متقدمة", "مهارات تقني السيارات (عملي III)"],
                    "الترم الثاني": ["تشخيص أعطال السيارات", "أنظمة التبريد والتكييف", "أنظمة الوقود", "تكنولوجيا متقدمة", "إدارة ورش السيارات", "تدريب ميداني", "مشروع التخرج (1)"]
                },
                "الصف 4": {
                    "الترم الأول": ["سيارات هجينة وكهربائية", "أنظمة الأمان المتقدمة", "إدارة جودة", "ريادة الأعمال", "مشروع التخرج (2)", "تدريب تعاوني", "صيانة متقدمة"],
                    "الترم الثاني": ["تكنولوجيا المستقبل", "إدارة مراكز الخدمة", "دراسة الجدوى", "لغة أجنبية متخصصة", "مهارات القيادة", "مشروع نهائي", "تدريب نهائي"]
                }
            }

        # استخدام معرف الجدول مباشرة
        spreadsheet_id = "1hdCK7m44eU5c0dD8agOj1prJxxdHIMa61XE_BO6jFqw"
        sheet_names = ["الصف 1", "الصف 2", "الصف 3", "الصف 4"]
        sheet_gids = [0, 2140109628, 92915964, 1925235200]
        subjects_data = {}

        try:
            spreadsheet = client.open_by_key(spreadsheet_id)

            for index, sheet_name in enumerate(sheet_names):
                try:
                    # محاولة الوصول للورقة بالفهرس
                    sheet = spreadsheet.get_worksheet(index)

                    if sheet:
                        all_values = sheet.get_all_values()
                        if len(all_values) > 0:
                            # العمود الأول للترم الأول، العمود الثاني للترم الثاني
                            term1_subjects = [row[0] for row in all_values[1:] if len(row) > 0 and row[0].strip()]
                            term2_subjects = [row[1] for row in all_values[1:] if len(row) > 1 and row[1].strip()]

                            subjects_data[sheet_name] = {
                                "الترم الأول": term1_subjects,
                                "الترم الثاني": term2_subjects
                            }
                        else:
                            subjects_data[sheet_name] = {
                                "الترم الأول": [],
                                "الترم الثاني": []
                            }
                    else:
                        raise Exception("لم يتم العثور على الورقة")

                except Exception as sheet_error:
                    print(f"❌ خطأ في تحميل {sheet_name}: {sheet_error}")
                    subjects_data[sheet_name] = {
                        "الترم الأول": [],
                        "الترم الثاني": []
                    }
        except Exception as spreadsheet_error:
            print(f"❌ خطأ في فتح الجدول: {spreadsheet_error}")
            return {}

        return subjects_data
    except Exception as e:
        print(f"❌ خطأ في تحميل المواد: {e}")
        return {}

# إعداد البوت
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في متغيرات البيئة")
    print("📋 يرجى إضافة TOKEN في متغيرات البيئة")
    exit(1)

# تنظيف التوكن من أي مسافات أو علامات اقتباس
TOKEN = TOKEN.strip()
if TOKEN.startswith("'") and TOKEN.endswith("'"):
    TOKEN = TOKEN[1:-1]
if TOKEN.startswith('"') and TOKEN.endswith('"'):
    TOKEN = TOKEN[1:-1]

print(f"🔍 تحقق من طول التوكن: {len(TOKEN)} حرف")
print(f"🔍 أول 10 أحرف من التوكن: {TOKEN[:10]}...")

# التحقق من صحة تنسيق التوكن
if TOKEN == "BOT_TOKEN" or not ":" in TOKEN or len(TOKEN) < 40:
    print("❌ خطأ: التوكن غير صحيح - يبدو أن القيمة لم يتم تعيينها بشكل صحيح")
    print("💡 يرجى التأكد من أن BOT_TOKEN يحتوي على التوكن الفعلي من @BotFather")
    print("💡 التنسيق الصحيح: 123456789:ABCdefGhIjKlmNoPQRsTuVwXYZ")
    print("💡 التوكن الحالي قصير جداً أو لا يحتوي على ':'")
    exit(1)

try:
    bot = telebot.TeleBot(TOKEN)
    print("✅ تم إنشاء البوت بنجاح")
except Exception as e:
    print(f"❌ خطأ في إنشاء البوت: {e}")
    exit(1)

# متغيرات عامة
user_state = {}
temp_selection = {}
subjects_cache = {}
FILES_DIR = "files"
DATA_FILE = "data.json"

# إنشاء مجلد الملفات إذا لم يكن موجوداً
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

# تحميل البيانات
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ خطأ في تحميل البيانات: {e}")
    return {}

# حفظ البيانات
def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ خطأ في حفظ البيانات: {e}")

data = load_data()
subjects_cache = load_subjects_from_sheets()  # تحميل البيانات التعليمية

# بداية البوت
@bot.message_handler(commands=["start"])
def start(message):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📚 تصفح المواد",
                                       callback_data="browse"))
        markup.add(
            types.InlineKeyboardButton("➕ إضافة مادة", callback_data="add"))

        bot.send_message(message.chat.id,
                         "🎓 *مرحباً بك في بوت المواد الدراسية*\n\n"
                         "📋 اختر ما تريد فعله:",
                         reply_markup=markup,
                         parse_mode="Markdown")
        user_state[message.chat.id] = "main_menu"
    except Exception as e:
        print(f"❌ خطأ في /start: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ، يرجى المحاولة مرة أخرى")

# معالج الملفات
@bot.message_handler(content_types=['document', 'photo', 'video', 'audio'])
def handle_file(message):
    try:
        chat_id = message.chat.id

        if user_state.get(chat_id) != "add_file":
            bot.send_message(chat_id, "❌ يرجى اختيار إضافة مادة أولاً")
            return

        if chat_id not in temp_selection:
            bot.send_message(chat_id, "❌ يرجى البدء من جديد")
            return

        selection = temp_selection[chat_id]
        year = selection["year"]
        term = selection["term"]
        subject = selection["subject"]

        # تحديد نوع الملف ومعرفه
        file_info = None
        file_name = ""

        if message.document:
            file_info = bot.get_file(message.document.file_id)
            file_name = message.document.file_name
        elif message.photo:
            file_info = bot.get_file(message.photo[-1].file_id)
            file_name = f"photo_{int(time.time())}.jpg"
        elif message.video:
            file_info = bot.get_file(message.video.file_id)
            file_name = f"video_{int(time.time())}.mp4"
        elif message.audio:
            file_info = bot.get_file(message.audio.file_id)
            file_name = message.audio.file_name or f"audio_{int(time.time())}.mp3"

        if not file_info:
            bot.send_message(chat_id, "❌ لم يتم العثور على الملف")
            return

        # إنشاء مسار حفظ الملف
        year_dir = os.path.join(FILES_DIR, year)
        term_dir = os.path.join(year_dir, term)
        subject_dir = os.path.join(term_dir, subject)

        os.makedirs(subject_dir, exist_ok=True)

        file_path = os.path.join(subject_dir, file_name)

        # تحميل وحفظ الملف
        if not file_info.file_path:
            bot.send_message(chat_id, "❌ فشل في الحصول على مسار الملف")
            return
        downloaded_file = bot.download_file(file_info.file_path)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # تحديث البيانات
        if year not in data:
            data[year] = {}
        if term not in data[year]:
            data[year][term] = {}
        if subject not in data[year][term]:
            data[year][term][subject] = []

        data[year][term][subject].append(file_path)
        save_data()

        # رسالة تأكيد
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🏠 العودة للقائمة الرئيسية",
                                       callback_data="back_to_main"))

        bot.send_message(chat_id,
                         f"✅ تم إضافة الملف بنجاح!\n\n"
                         f"📅 السنة: {year}\n"
                         f"📚 الترم: {term}\n"
                         f"📖 المادة: {subject}\n"
                         f"📄 الملف: {file_name}",
                         reply_markup=markup)

        # إعادة تعيين الحالة
        user_state[chat_id] = "main_menu"
        if chat_id in temp_selection:
            del temp_selection[chat_id]

    except Exception as e:
        print(f"❌ خطأ في معالجة الملف: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في رفع الملف، يرجى المحاولة مرة أخرى")

# معالج الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        chat_id = call.message.chat.id

        if call.data == "browse":
            browse_years(chat_id)
        elif call.data == "add":
            add_material(chat_id)
        elif call.data.startswith("year_"):
            year = call.data.replace("year_", "")
            browse_terms(chat_id, year)
        elif call.data.startswith("term_"):
            year, term = call.data.replace("term_", "").split("||")
            browse_subjects(chat_id, year, term)
        elif call.data.startswith("subj_"): # Handling the new callback for subjects
            parts = call.data.split("_")
            index = parts[1]
            year = parts[2]
            term = parts[3]

            if chat_id in temp_selection and "browse_subjects" in temp_selection[chat_id]:
                subjects_map = temp_selection[chat_id]["browse_subjects"]
                if index in subjects_map:
                    subject = subjects_map[index]
                    # Now call browse_files with the actual subject name
                    browse_files(chat_id, year, term, subject)
                else:
                    bot.send_message(chat_id, "❌ لم يتم العثور على المادة المطلوبة.")
            else:
                bot.send_message(chat_id, "❌ حدث خطأ في استرجاع بيانات المواد.")

        elif call.data.startswith("dl_"):
            # معالجة تحميل الملفات
            index = call.data.replace("dl_", "")
            if chat_id in temp_selection and "files" in temp_selection[chat_id]:
                files_map = temp_selection[chat_id]["files"]
                if index in files_map:
                    file_path = files_map[index]
                    send_file(chat_id, file_path)
                else:
                    bot.send_message(chat_id, "❌ لم يتم العثور على الملف المطلوب.")
            else:
                bot.send_message(chat_id, "❌ حدث خطأ في استرجاع بيانات الملفات.")
        elif call.data.startswith("file_"):
            # التعامل مع النظام القديم إن وجد
            file_path = call.data.replace("file_", "")
            send_file(chat_id, file_path)
        elif call.data == "back_to_main":
            start(call.message)
        elif call.data.startswith("add_year_"):
            year = call.data.replace("add_year_", "")
            temp_selection[chat_id] = {"year": year}
            add_select_term(chat_id)
        elif call.data.startswith("add_term_"):
            term = call.data.replace("add_term_", "")
            temp_selection[chat_id]["term"] = term
            add_select_subject(chat_id)
        elif call.data.startswith("add_subj_"):
            parts = call.data.split("_")
            index = parts[2]
            year = parts[3]
            term = parts[4]

            if chat_id in temp_selection and "add_subjects" in temp_selection[chat_id]:
                subjects_map = temp_selection[chat_id]["add_subjects"]
                if index in subjects_map:
                    subject = subjects_map[index]
                    temp_selection[chat_id]["subject"] = subject
                    bot.send_message(chat_id, f"📤 أرسل الملف للمادة: {subject}")
                    user_state[chat_id] = "add_file"
                else:
                    bot.send_message(chat_id, "❌ لم يتم العثور على المادة المطلوبة.")
            else:
                bot.send_message(chat_id, "❌ حدث خطأ في استرجاع بيانات المواد.")
        elif call.data.startswith("add_subject_"):
            subject = call.data.replace("add_subject_", "")
            temp_selection[chat_id]["subject"] = subject
            bot.send_message(chat_id, "📤 أرسل الملف الذي تريد إضافته:")
            user_state[chat_id] = "add_file"

        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ خطأ في معالج الأزرار: {e}")

def browse_years(chat_id):
    try:
        # استخدام البيانات التعليمية بدلاً من الملفات المرفوعة
        if not subjects_cache:
            bot.send_message(chat_id, "❌ لا توجد مواد متاحة حالياً")
            return

        markup = types.InlineKeyboardMarkup()
        for grade in subjects_cache.keys():
            markup.add(
                types.InlineKeyboardButton(f"📅 {grade}",
                                           callback_data=f"year_{grade}"))
        markup.add(
            types.InlineKeyboardButton("🏠 العودة للقائمة الرئيسية",
                                       callback_data="back_to_main"))

        bot.send_message(chat_id,
                         "📅 اختر الصف الدراسي:",
                         reply_markup=markup)
    except Exception as e:
        print(f"❌ خطأ في تصفح الصفوف: {e}")

def browse_terms(chat_id, year):
    try:
        markup = types.InlineKeyboardMarkup()
        if year in subjects_cache:
            for term in subjects_cache[year].keys():
                markup.add(
                    types.InlineKeyboardButton(
                        f"📚 {term}", callback_data=f"term_{year}||{term}"))
        markup.add(
            types.InlineKeyboardButton("↩️ العودة", callback_data="browse"))

        bot.send_message(chat_id,
                         f"📚 اختر الترم في {year}:",
                         reply_markup=markup)
    except Exception as e:
        print(f"❌ خطأ في تصفح الترمات: {e}")

def browse_subjects(chat_id, year, term):
    try:
        markup = types.InlineKeyboardMarkup()
        if year in subjects_cache and term in subjects_cache[year]:
            subjects = subjects_cache[year][term]
            if subjects:
                for i, subject in enumerate(subjects):
                    # تقصير اسم المادة إذا كان طويلاً لتجنب خطأ callback_data
                    display_name = subject[:25] + "..." if len(subject) > 25 else subject
                    # استخدام فهرس مع اسم مختصر
                    callback_data = f"subj_{i}_{year}_{term}"
                    markup.add(
                        types.InlineKeyboardButton(
                            f"📖 {display_name}",
                            callback_data=callback_data))

                # حفظ تطابق الفهارس مع أسماء المواد
                if chat_id not in temp_selection:
                    temp_selection[chat_id] = {}
                temp_selection[chat_id]["browse_subjects"] = {
                    str(i): subject for i, subject in enumerate(subjects)
                }
                temp_selection[chat_id]["current_year"] = year
                temp_selection[chat_id]["current_term"] = term
            else:
                bot.send_message(chat_id, f"❌ لا توجد مواد في {term} - {year}")
                return
        else:
            bot.send_message(chat_id, f"❌ لا توجد مواد في {term} - {year}")
            return

        markup.add(
            types.InlineKeyboardButton("↩️ العودة",
                                       callback_data=f"year_{year}"))

        bot.send_message(chat_id,
                         f"📖 المواد المتاحة في {term} - {year}:",
                         reply_markup=markup)
    except Exception as e:
        print(f"❌ خطأ في تصفح المواد: {e}")
        bot.send_message(chat_id, "❌ حدث خطأ في عرض المواد")

def browse_files(chat_id, year, term, subject):
    try:
        # البحث عن الملفات المرفوعة في البيانات المحفوظة
        files = []
        if year in data and term in data[year] and subject in data[year][term]:
            files = data[year][term][subject]

        markup = types.InlineKeyboardMarkup()
        
        if files:
            # عرض الملفات المرفوعة
            for i, file_path in enumerate(files):
                file_name = os.path.basename(file_path)
                # تقصير اسم الملف إذا كان طويلاً
                display_name = file_name[:25] + "..." if len(file_name) > 25 else file_name
                # استخدام callback_data مختصر
                callback_data = f"dl_{i}"
                markup.add(
                    types.InlineKeyboardButton(f"📄 {display_name}",
                                               callback_data=callback_data))
            
            # حفظ مسارات الملفات للاستخدام في callback
            if chat_id not in temp_selection:
                temp_selection[chat_id] = {}
            temp_selection[chat_id]["files"] = {
                str(i): file_path for i, file_path in enumerate(files)
            }
            temp_selection[chat_id]["current_subject"] = subject
            temp_selection[chat_id]["current_year"] = year
            temp_selection[chat_id]["current_term"] = term
            
            message_text = f"📄 الملفات المتاحة في:\n📖 المادة: {subject}\n📅 الصف: {year}\n📚 الترم: {term}\n\n📂 اختر الملف الذي تريد تحميله:"
        else:
            # لا توجد ملفات مرفوعة
            message_text = f"📖 المادة: {subject}\n📅 الصف: {year}\n📚 الترم: {term}\n\n❌ لا توجد ملفات مرفوعة لهذه المادة حالياً.\n\n💡 يمكنك إضافة ملفات باستخدام خيار 'إضافة مادة'."

        markup.add(
            types.InlineKeyboardButton("↩️ العودة",
                                       callback_data=f"term_{year}||{term}"))

        bot.send_message(chat_id, message_text, reply_markup=markup)

    except Exception as e:
        print(f"❌ خطأ في تصفح الملفات: {e}")
        bot.send_message(chat_id, "❌ حدث خطأ في عرض الملفات")

def send_file(chat_id, file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                bot.send_document(chat_id, f)
        else:
            bot.send_message(chat_id, "❌ الملف غير موجود")
    except Exception as e:
        print(f"❌ خطأ في إرسال الملف: {e}")
        bot.send_message(chat_id, "❌ حدث خطأ في إرسال الملف")

def add_material(chat_id):
    try:
        # تحميل بيانات المواد من Google Sheets مع التخزين المؤقت
        if not subjects_cache:
            subjects_cache.update(load_subjects_from_sheets())

        subjects_data = subjects_cache

        if not subjects_data:
            bot.send_message(chat_id,
                             "❌ لا توجد بيانات مواد متاحة من Google Sheets")
            return

        markup = types.InlineKeyboardMarkup()
        for year, terms in subjects_data.items():
            markup.add(
                types.InlineKeyboardButton(f"📅 {year}",
                                           callback_data=f"add_year_{year}"))
        markup.add(
            types.InlineKeyboardButton("🏠 العودة للقائمة الرئيسية",
                                       callback_data="back_to_main"))

        bot.send_message(chat_id,
                         "📅 اختر السنة الدراسية:",
                         reply_markup=markup)
    except Exception as e:
        print(f"❌ خطأ في إضافة المادة: {e}")

def add_select_term(chat_id):
    try:
        year = temp_selection[chat_id]["year"]
        subjects_data = subjects_cache if subjects_cache else load_subjects_from_sheets()

        if year not in subjects_data:
            bot.send_message(chat_id, "❌ السنة الدراسية غير موجودة")
            return

        markup = types.InlineKeyboardMarkup()
        for term in subjects_data[year].keys():
            markup.add(
                types.InlineKeyboardButton(f"📚 {term}",
                                           callback_data=f"add_term_{term}"))
        markup.add(
            types.InlineKeyboardButton("↩️ العودة", callback_data="add"))

        bot.send_message(chat_id, f"📚 اختر الترم في {year}:", reply_markup=markup)
    except Exception as e:
        print(f"❌ خطأ في اختيار الترم: {e}")

def add_select_subject(chat_id):
    try:
        year = temp_selection[chat_id]["year"]
        term = temp_selection[chat_id]["term"]
        subjects_data = subjects_cache if subjects_cache else load_subjects_from_sheets()

        if year not in subjects_data or term not in subjects_data[year]:
            bot.send_message(chat_id, "❌ الترم غير موجود")
            return

        subjects = subjects_data[year][term]
        if not subjects:
            bot.send_message(chat_id, "❌ لا توجد مواد متاحة في هذا الترم")
            return

        markup = types.InlineKeyboardMarkup()
        # حفظ تطابق الفهارس مع أسماء المواد
        if chat_id not in temp_selection:
            temp_selection[chat_id] = {}
        temp_selection[chat_id]["add_subjects"] = {
            str(i): subject for i, subject in enumerate(subjects)
        }
        
        for i, subject in enumerate(subjects):
            # تقصير اسم المادة إذا كان طويلاً
            display_name = subject[:25] + "..." if len(subject) > 25 else subject
            # استخدام فهرس بدلاً من اسم المادة
            callback_data = f"add_subj_{i}_{year}_{term}"
            markup.add(
                types.InlineKeyboardButton(f"📖 {display_name}",
                                           callback_data=callback_data))
        markup.add(
            types.InlineKeyboardButton("↩️ العودة",
                                       callback_data=f"add_year_{year}"))

        bot.send_message(chat_id, f"📖 اختر المادة في {term} - {year}:", reply_markup=markup)
    except Exception as e:
        print(f"❌ خطأ في اختيار المادة: {e}")

# تشغيل البوت
if __name__ == "__main__":
    print("🤖 Bot is starting...")
    keep_alive()
    print("✅ Keep alive server started on port 5000")
    print("🔄 Starting bot polling...")

    while True:
        try:
            # حذف webhook إذا كان موجوداً لتجنب التعارض
            try:
                bot.delete_webhook()
                print("✅ Webhook deleted successfully")
            except:
                pass
            
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ خطأ في البوت: {e}")
            print("🔄 إعادة تشغيل البوت خلال 15 ثانية...")
            time.sleep(15)
            print("🤖 البوت يعمل مرة أخرى...")
