import os
import telebot
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

users_db = {}

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {'lang': 'ru'}
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ru = types.InlineKeyboardButton("Русский 🇷🇺", callback_data="set_lang_ru")
    btn_en = types.InlineKeyboardButton("English 🇺🇸", callback_data="set_lang_en")
    btn_es = types.InlineKeyboardButton("Español 🇪🇸", callback_data="set_lang_es")
    btn_zh = types.InlineKeyboardButton("中文 🇨🇳", callback_data="set_lang_zh")
    markup.add(btn_ru, btn_en, btn_es, btn_zh)
    
    bot.send_message(
        message.chat.id, 
        "🌐 Пожалуйста, выберите ваш язык интерфейса:\nPlease choose your interface language:", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_lang_'))
def callback_lang(call):
    user_id = call.from_user.id
    lang = call.data.split('_')[-1]
    
    if user_id not in users_db:
        users_db[user_id] = {}
    users_db[user_id]['lang'] = lang
    
    texts = {
        'ru': "✅ Язык успешно изменен на Русский! Используйте меню для звонков или вызова ИИ.",
        'en': "✅ Language successfully changed to English! Use menu for calls or AI assistant.",
        'es': "✅ ¡Idioma cambiado con éxito a Español! Use el menú para llamadas o asistente IA.",
        'zh': "✅ 语言已成功切换为中文！使用菜单进行通话或呼叫人工智能助手。"
    }
    
    bot.answer_callback_query(call.id, "Done!")
    bot.send_message(call.message.chat.id, texts.get(lang, texts['ru']))

@bot.message_handler(commands=['assistant'])
def assistant_cmd(message):
    user_id = message.from_user.id
    user_lang = users_db.get(user_id, {}).get('lang', 'ru')
    
    ai_texts = {
        'ru': "🤖 Здравствуйте! Я ваш ИИ-помощник по эксплуатации PolyCall. Чем я могу помочь вам настроить звонок?",
        'en': "🤖 Hello! I am your PolyCall AI operations assistant. How can I help you set up your call?",
        'es': "🤖 ¡Hola! Soy su asistente de operaciones de IA de PolyCall. ¿Cómo puedo ayudarle a configurar su llamada?",
        'zh': "🤖 您好！我是您的 PolyCall 人工智能助手。我能如何帮您设置通话？"
    }
    bot.send_message(message.chat.id, ai_texts.get(user_lang, ai_texts['ru']))

@bot.message_handler(commands=['call'])
def call_cmd(message):
    user_id = message.from_user.id
    user_lang = users_db.get(user_id, {}).get('lang', 'ru')
    
    call_texts = {
        'ru': "📞 Введите номер телефона в международном формате (например, +1...) или выберите контакт для звонка с ИИ-переводом в реальном времени:",
        'en': "📞 Enter the phone number in international format (e.g., +1...) or select a contact for a real-time AI-translated call:",
        'es': "📞 Ingrese el número de teléfono en formato internacional (por ejemplo, +1...) o seleccione un contacto para una llamada traducida por IA en tiempo real:",
        'zh': "📞 请输入国际格式的电话号码（例如 +1...）或选择联系人以进行实时人工智能翻译通话："
    }
    bot.send_message(message.chat.id, call_texts.get(user_lang, call_texts['ru']))

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Статистика", "📢 Рассылка рекламы")
    bot.send_message(message.chat.id, "👑 Добро пожаловать в панель разработчика PolyCall! Управляйте ботом без лимитов:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def admin_stats(message):
    count = len(users_db) if len(users_db) > 0 else 1
    bot.send_message(message.chat.id, f"📈 Всего уникальных пользователей в базе: {count}\n🎯 Цель: 1,000,000,000")

@bot.message_handler(func=lambda message: message.text == "📢 Рассылка рекламы")
def admin_broadcast(message):
    bot.send_message(message.chat.id, "📝 Напишите текст рекламного сообщения или вставьте реферальную ссылку, которую хотите разослать всем подписчикам:")

import threading
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run_port():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 80))

if __name__ == '__main__':
    # Запуск порта для обхода ошибки Render
    threading.Thread(target=run_port).start()
    print("Бот PolyCall успешно запущен...")
    bot.infinity_polling()


