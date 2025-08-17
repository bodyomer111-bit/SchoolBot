import telebot
from telebot import types
import os
import json

# التوكن الخاص بك
TOKEN = "8391860066:AAGwmcQDPDQ7OwBSmL1Cp9YAXaU9oqU9io8"
bot = telebot.TeleBot(TOKEN)

# ملف البيانات لتخزين الملفات المضافة
DATA_FILE = "data.json"
FILES_DIR = "files"

# تحميل البيانات أو إنشاء جديد
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {}

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

user_state = {}
temp_selection = {}

# القوائم
YEARS = ["الصف الأول", "الصف الثاني", "الصف الثالث", "الصف الرابع"]
TERMS = ["الترم الأول", "الترم الثاني"]

# المواد لكل سنة وترم (اتركها فارغة لتملأها انت)
SUBJECTS = {
    "الصف الأول": {"الترم الأول": ["لغه انجلزيه" ], "الترم الثاني": []},
    "الصف الثاني": {"الترم الأول": [], "الترم الثاني": []},
    "الصف الثالث": {"الترم الأول": [], "الترم الثاني": []},
    "الصف الرابع": {"الترم الأول": [], "الترم الثاني": []},
}

# حفظ البيانات
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# بدء البوت
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for year in YEARS:
        markup.add(year)
    bot.send_message(message.chat.id, "اختر السنة الدراسية:", reply_markup=markup)
    user_state[message.chat.id] = "choose_year"

# اختيار السنة
@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id) == "choose_year")
def choose_year(message):
    if message.text not in YEARS:
        bot.send_message(message.chat.id, "اختر سنة صحيحة.")
        return
    temp_selection[message.chat.id] = {"year": message.text}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for term in TERMS:
        markup.add(term)
    bot.send_message(message.chat.id, "اختر الترم:", reply_markup=markup)
    user_state[message.chat.id] = "choose_term"

# اختيار الترم
@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id) == "choose_term")
def choose_term(message):
    year = temp_selection[message.chat.id]["year"]
    if message.text not in TERMS:
        bot.send_message(message.chat.id, "اختر ترم صحيح.")
        return
    temp_selection[message.chat.id]["term"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for subject in SUBJECTS[year][message.text]:
        markup.add(subject)
    bot.send_message(message.chat.id, "اختر المادة:", reply_markup=markup)
    user_state[message.chat.id] = "choose_subject"

# اختيار المادة
@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id) == "choose_subject")
def choose_subject(message):
    year = temp_selection[message.chat.id]["year"]
    term = temp_selection[message.chat.id]["term"]
    if message.text not in SUBJECTS[year][term]:
        bot.send_message(message.chat.id, "اختر مادة صحيحة.")
        return
    temp_selection[message.chat.id]["subject"] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📄 عرض ملفات المادة", "➕ إضافة ملف")
    markup.add("🏠 العودة للقائمة الرئيسية")
    bot.send_message(message.chat.id, "اختر الإجراء:", reply_markup=markup)
    user_state[message.chat.id] = "subject_menu"

# قائمة المادة
@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id) == "subject_menu")
def subject_menu(message):
    if message.text == "📄 عرض ملفات المادة":
        year = temp_selection[message.chat.id]["year"]
        term = temp_selection[message.chat.id]["term"]
        subject = temp_selection[message.chat.id]["subject"]

        files_list = data.get(year, {}).get(term, {}).get(subject, [])
        if not files_list:
            bot.send_message(message.chat.id, "لا توجد ملفات لهذه المادة.")
        else:
            for file_path in files_list:
                bot.send_document(message.chat.id, open(file_path, "rb"))

    elif message.text == "➕ إضافة ملف":
        bot.send_message(message.chat.id, "أرسل لي ملف PDF أو صورة لإضافته.")
        user_state[message.chat.id] = "add_file"

    elif message.text == "🏠 العودة للقائمة الرئيسية":
        send_welcome(message)
    else:
        bot.send_message(message.chat.id, "اختر أمر صحيح.")

# إضافة ملف
@bot.message_handler(content_types=["document", "photo"], func=lambda msg: user_state.get(msg.chat.id) == "add_file")
def add_file(message):
    year = temp_selection[message.chat.id]["year"]
    term = temp_selection[message.chat.id]["term"]
    subject = temp_selection[message.chat.id]["subject"]

    path_dir = os.path.join(FILES_DIR, year, term, subject)
    os.makedirs(path_dir, exist_ok=True)

    if message.document:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_path = os.path.join(path_dir, message.document.file_name)
        with open(file_path, "wb") as f:
            f.write(downloaded_file)
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_path = os.path.join(path_dir, f"{file_id}.jpg")
        with open(file_path, "wb") as f:
            f.write(downloaded_file)

    data.setdefault(year, {}).setdefault(term, {}).setdefault(subject, []).append(file_path)
    save_data()
    bot.send_message(message.chat.id, "✅ تم إضافة الملف بنجاح.")
    user_state[message.chat.id] = "subject_menu"

# تشغيل البوت
bot.polling(none_stop=True)
