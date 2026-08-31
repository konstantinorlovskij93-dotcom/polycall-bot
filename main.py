import os
import threading
import random
import telebot
from telebot import types
from flask import Flask

# Настройка фальшивого веб-порта для обхода ошибки Render
app = Flask('')

@app.route('/')
def home():
    return "PolyCall бот успешно запущен и работает вечно!"

def run_port():
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port)

# Настройка самого Telegram-бота
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
    
    # Генерируем случайный уникальный ID комнаты для звонка
    room_id = f"polycall_{user_id}_{random.randint(1000, 9999)}"
    call_url = f"https://jit.si{room_id}"
    
    # Формируем тексты со ссылками на разных языках
    if user_lang == 'en':
        text = f"📞 *Your secure AI-translated call link is ready!*\n\n1. Tap the link below to enter the room.\n2. Send this link to your friend (they can open it in WhatsApp, SMS, or any browser).\n\n🔗 *Join call:* {call_url}"
    elif user_lang == 'es':
        text = f"📞 *¡Su enlace de llamada segura traducida por IA está listo!*\n\n1. Toque el enlace de abajo para entrar.\n2. Envíe este enlace a su amigo (puede abrirlo en WhatsApp, SMS o cualquier navegador).\n\n🔗 *Unirse a la llamada:* {call_url}"
    elif user_lang == 'zh':
        text = f"📞 *您的加密人工智能翻译通话链接已准备 code 就绪！*\n\n1. 点击下方链接进入房间。\n2. 将此链接发送给您的朋友（他们可以在 WhatsApp、短信或任何浏览器中打开）。\n\n🔗 *加入通话:* {call_url}"
    else: # По умолчанию Русский
        text = f"📞 *Ваша защищенная ссылка на ИИ-звонок готова!*\n\n1. Нажмите на ссылку ниже, чтобы войти в комнату звонка.\n2. Отправьте эту ссылку собеседнику (он может открыть её в WhatsApp, СМС или любом браузере на телефоне).\n\n🔗 *Войти в звонок:* {call_url}"
        
    bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=False)

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

if __name__ == '__main__':
    threading.Thread(target=run_port).start()
    print("Бот PolyCall успешно запущен...")
    bot.infinity_polling()
