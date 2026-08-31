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
        "🌐 Пожалуйста, выберите ваш язык接口 интерфейса:\nPlease choose your interface language:", 
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
    room_id = f"polycall_{user_id}_{random.randint(10000, 99999)}"
    call_url = f"https://jit.si{room_id}"
    
    # Формируем тексты со ссылками и инструкциями по ИИ-переводу
    if user_lang == 'en':
        text = f"📞 *Your secure link is ready!*\n\n1. Tap the link below to enter the room.\n2. Send it to your friend.\n\n🔗 *Join call:* {call_url}\n\n🤖 *Need AI Translation?* Inside the call, tap three dots (...) ➡️ *Start Subtitles* ➡️ choose languages and check *Translation*."
    elif user_lang == 'es':
        text = f"📞 *¡Su enlace seguro está listo!*\n\n1. Toque el enlace de abajo para entrar.\n2. Envíalo a tu amigo.\n\n🔗 *Unirse:* {call_url}\n\n🤖 *¿Necesitas traducción IA?* Dentro de la llamada, toca tres puntos (...) ➡️ *Start Subtitles* ➡️ elige idiomas y marca *Translation*."
    elif user_lang == 'zh':
        text = f"📞 *您的安全通话链接已就绪！*\n\n1. 点击下方链接进入房间。\n2. 发送给您的朋友。\n\n🔗 *加入通话:* {call_url}\n\n🤖 *需要人工智能翻译吗？* 在通话中，点击三个点 (...) ➡️ *Start Subtitles* ➡️ 选择语言并勾选 *Translation*。"
    else: # По умолчанию Русский
        text = f"📞 *Ваша защищенная ссылка готова!*\n\n1. Нажмите на ссылку ниже, чтобы войти в комнату.\n2. Отправьте её собеседнику в любой мессенджер.\n\n🔗 *Войти в звонок:* {call_url}\n\n🤖 *Нужен ИИ-перевод?* Внутри звонка нажмите на три точки (...) ➡️ *Start Subtitles* (Включить субтитры) ➡️ выберите языки разговора и поставьте галочку *Translation*."
        
    bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)

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
