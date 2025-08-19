import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import telebot
from telebot import types
from keep_alive import keep_alive
import time

# إعداد نطاق الوصول لجوجل شيت
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets"
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    'path_to_your_credentials.json', scope)
client = gspread.authorize(creds)


# تحميل المواد من أوراق Google Sheets
def load_subjects_from_sheets():
    try:
        sheet_urls = [
            "https://docs.google.com/spreadsheets/d/1hdCK7m44eU5c0dD8agOj1prJxxdHIMa61XE_BO6jFqw/edit?gid=0",
            "https://docs.google.com/spreadsheets/d/1hdCK7m44eU5c0dD8agOj1prJxxdHIMa61XE_BO6jFqw/edit?gid=2140109628",
            "https://docs.google.com/spreadsheets/d/1hdCK7m44eU5c0dD8agOj1prJxxdHIMa61XE_BO6jFqw/edit?gid=92915964",
            "https://docs.google.com/spreadsheets/d/1hdCK7m44eU5c0dD8agOj1prJxxdHIMa61XE_BO6jFqw/edit?gid=1925235200"
        ]
        subjects_data = {}
        for index, url in enumerate(sheet_urls):
            sheet = client.open_by_url(url).sheet1
            subjects_data[f"الصف {index + 1}"] = {
                "الترم الأول": sheet.col_values(1)[1:],  # العمود الأول
                "الترم الثاني": sheet.col_values(2)[1:]  # العمود الثاني
            }
        return subjects_data
    except Exception as e:
        print(f"خطأ في تحميل المواد: {e}")
        return {}


# إعداد البوت
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في متغيرات البيئة")
    print("📋 يرجى إضافة TOKEN في Secrets")
    exit()

bot = telebot.TeleBot(TOKEN)

# متغيرات عامة
user_state = {}
temp_selection = {}
FILES_DIR = "files"
DATA_FILE = "data.json"


# تحميل البيانات
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"خطأ في تحميل البيانات: {e}")
    return {}


# حفظ البيانات
def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"خطأ في حفظ البيانات: {e}")


data = load_data()


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
        print(f"خطأ في /start: {e}")


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
        elif call.data.startswith("subject_"):
            year, term, subject = call.data.replace("subject_", "").split("||")
            browse_files(chat_id, year, term, subject)
        elif call.data.startswith("file_"):
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
        elif call.data.startswith("add_subject_"):
            subject = call.data.replace("add_subject_", "")
            temp_selection[chat_id]["subject"] = subject
            bot.send_message(chat_id, "📤 أرسل الملف الذي تريد إضافته:")
            user_state[chat_id] = "add_file"

        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"خطأ في معالج الأزرار: {e}")


def browse_years(chat_id):
    try:
        if not data:
            bot.send_message(chat_id, "❌ لا توجد مواد متاحة حالياً")
            return

        markup = types.InlineKeyboardMarkup()
        for year in data.keys():
            markup.add(
                types.InlineKeyboardButton(f"📅 {year}",
                                           callback_data=f"year_{year}"))
        markup.add(
            types.InlineKeyboardButton("🏠 العودة للقائمة الرئيسية",
                                       callback_data="back_to_main"))

        bot.send_message(chat_id,
                         "📅 اختر السنة الدراسية:",
                         reply_markup=markup)
    except Exception as e:
        print(f"خطأ في تصفح السنوات: {e}")


def browse_terms(chat_id, year):
    try:
        markup = types.InlineKeyboardMarkup()
        for term in data[year].keys():
            markup.add(
                types.InlineKeyboardButton(
                    f"📚 {term}", callback_data=f"term_{year}||{term}"))
        markup.add(
            types.InlineKeyboardButton("↩️ العودة", callback_data="browse"))

        bot.send_message(chat_id,
                         f"📚 اختر الترم في {year}:",
                         reply_markup=markup)
    except Exception as e:
        print(f"خطأ في تصفح الترمات: {e}")


def browse_subjects(chat_id, year, term):
    try:
        markup = types.InlineKeyboardMarkup()
        for subject in data[year][term].keys():
            markup.add(
                types.InlineKeyboardButton(
                    f"📖 {subject}",
                    callback_data=f"subject_{year}||{term}||{subject}"))
        markup.add(
            types.InlineKeyboardButton("↩️ العودة",
                                       callback_data=f"year_{year}"))

        bot.send_message(chat_id,
                         f"📖 اختر المادة في {term} - {year}:",
                         reply_markup=markup)
    except Exception as e:
        print(f"خطأ في تصفح المواد: {e}")


def browse_files(chat_id, year, term, subject):
    try:
        files = data[year][term][subject]
        if not files:
            bot.send_message(chat_id, "❌ لا توجد ملفات في هذه المادة")
            return

        markup = types.InlineKeyboardMarkup()
        for file_path in files:
            file_name = os.path.basename(file_path)
            markup.add(
                types.InlineKeyboardButton(f"📄 {file_name}",
                                           callback_data=f"file_{file_path}"))
        markup.add(
            types.InlineKeyboardButton("↩️ العودة",
                                       callback_data=f"term_{year}||{term}"))

        bot.send_message(chat_id, f"📄 ملفات {subject}:", reply_markup=markup)
    except Exception as e:
        print(f"خطأ في تصفح الملفات: {e}")


def send_file(chat_id, file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                bot.send_document(chat_id, f)
        else:
            bot.send_message(chat_id, "❌ الملف غير موجود")
    except Exception as e:
        print(f"خطأ في إرسال الملف: {e}")
        bot.send_message(chat_id, "❌ حدث خطأ في إرسال الملف")


# تعديل add_material لعرض المواد من Google Sheets
def add_material(chat_id):
    try:
        subjects_data = load_subjects_from_sheets()
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
        print(f"خطأ في إضافة المادة: {e}")


# تشغيل البوت
if __name__ == "__main__":
    print("🤖 Bot is starting...")
    keep_alive()
    print("✅ Keep alive server started on port 8080")
    print("🔄 Starting bot polling...")

    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ خطأ في البوت: {e}")
            print("🔄 إعادة تشغيل البوت خلال 15 ثانية...")
            time.sleep(15)
            print("🤖 البوت يعمل مرة أخرى...")
