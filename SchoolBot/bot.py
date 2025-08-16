import telebot

# التوكن بتاع البوت
TOKEN = "8391860066:AAGIisoaKtjI2ibIsyPikLxknP-rSiaxp5g"
bot = telebot.TeleBot(TOKEN)

# القوائم
data = {
    "الصف الأول": [
        "موائع و حرارة",
        "الأنظمة الكهربائية والإلكترونية للسيارات - HVT303",
        "مجموعة نقل القدرة للمركبات الهجين - HVT304",
        "مهارات تقني السيارات (عملي (11)) - HVT401",
        "تكنولوجيا المعادن والمعالجة الحرارية - HVT402",
        "أنظمة هياكل السيارات - HVT403",
        "أساسيات المحرك - HVT404"
    ],
    "الصف الثاني": {
        "الترم الأول": [
            "الرسم بالأتوكاد - FAC111",
            "رياضيات تطبيقية (2) - FAC113",
            "كتابة تقارير فنية (2) - HVT301"
        ],
        "الترم الثاني": [
            "تكنولوجيا المركبات الهجين والكهربائية - HVT405",
            "أساسيات جسم السيارة واستعادة العمل - SKL102",
            "مهارات القيادة - UNI102",
            "الفحص وضمان الجودة بمساعدة الحاسب - UN1103",
            "المبادئ الأساسية لحماية البيئة"
        ]
    }
}

# رسالة البدء
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("الصف الأول", "الصف الثاني")
    bot.send_message(message.chat.id, "اختر الصف:", reply_markup=markup)

# الرد على اختيار الصف
@bot.message_handler(func=lambda m: True)
def send_data(message):
    if message.text == "الصف الأول":
        bot.send_message(message.chat.id, "\n".join(data["الصف الأول"]))
    elif message.text == "الصف الثاني":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("الترم الأول", "الترم الثاني")
        bot.send_message(message.chat.id, "اختر الترم:", reply_markup=markup)
    elif message.text == "الترم الأول":
        bot.send_message(message.chat.id, "\n".join(data["الصف الثاني"]["الترم الأول"]))
    elif message.text == "الترم الثاني":
        bot.send_message(message.chat.id, "\n".join(data["الصف الثاني"]["الترم الثاني"]))
    else:
        bot.send_message(message.chat.id, "اختيار غير صحيح.")

bot.polling()

