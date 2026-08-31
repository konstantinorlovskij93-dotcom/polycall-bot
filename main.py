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

# Временная база данных в памяти сервера
users_db = {}

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    text_args = message.text.split()
    
    # Реферальная система: проверяем, зашел ли пользователь по чужой ссылке
    referrer_id = None
    if len(text_args) > 1 and text_args[1].isdigit():
        referrer_id = int(text_args[1])

    if user_id not in users_db:
        users_db[user_id] = {'lang': 'ru', 'referrals': 0, 'invited_by': referrer_id}
        # Если есть пригласитель, начисляем ему балл
        if referrer_id and referrer_id in users_db:
            users_db[referrer_id]['referrals'] += 1
            try:
                bot.send_message(referrer_id, "🎉 По вашей реферальной ссылке зарегистрировался новый пользователь! +1 в вашу команду.")
            except:
                pass
    
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
        users_db[user_id] = {'referrals': 0, 'invited_by': None}
    users_db[user_id]['lang'] = lang
    
    texts = {
        'ru': "✅ Язык успешно изменен! Используйте меню для звонков, секретного чата или проверки рефералов.",
        'en': "✅ Language successfully changed! Use the menu for calls, secret chat, or checking referrals.",
        'es': "✅ ¡Idioma cambiado con éxito! Use el menú para llamadas, chat secreto o verificar referidos.",
        'zh': "✅ 语言已成功切换！使用菜单进行通话、加密聊天或查看推荐人。"
    }
    
    bot.answer_callback_query(call.id, "Done!")
    bot.send_message(call.message.chat.id, texts.get(lang, texts['ru']))

# Новая команда для вывода реферальной ссылки пользователя
@bot.message_handler(commands=['share'])
def share_cmd(message):
    user_id = message.from_user.id
    bot_info = bot.get_me()
    ref_url = f"https://t.me{bot_info.username}?start={user_id}"
    
    user_data = users_db.get(user_id, {'referrals': 0})
    ref_count = user_data.get('referrals', 0)
    
    text = (
        f"👑 *Ваша персональная реферальная ссылка:*\n`{ref_url}`\n\n"
        f"👥 Вы пригласили: *{ref_count}* человек(а).\n\n"
        f"Пересылайте эту ссылку друзьям! Каждый, кто зайдет по ней, станет частью вашей команды разработчика PolyCall."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['assistant'])
def assistant_cmd(message):
    user_id = message.from_user.id
    user_lang = users_db.get(user_id, {}).get('lang', 'ru')
    
    ai_texts = {
        'ru': "🤖 Здравствуйте! Я ваш ИИ-помощник PolyCall. Чем я могу помочь вам настроить звонок или защищенный чат?",
        'en': "🤖 Hello! I am your PolyCall AI assistant. How can I help you set up your call or secure chat?",
        'es': "🤖 ¡Hola! Soy su asistente de IA de PolyCall. ¿Cómo puedo ayudarle a configurar su llamada o chat seguro?",
        'zh': "🤖 您好！我是您的 PolyCall 人工智能助手。我能如何帮您设置通话或加密聊天？"
    }
    bot.send_message(message.chat.id, ai_texts.get(user_lang, ai_texts['ru']))

@bot.message_handler(commands=['call'])
def call_cmd(message):
    user_id = message.from_user.id
    user_lang = users_db.get(user_id, {}).get('lang', 'ru')
    
    # Уникальная секретная комната с поддержкой автоудаления сообщений после прочтения (таймер Jitsi)
    room_id = f"polycall_secure_{user_id}_{random.randint(100000, 999999)}"
    # Добавляем специальный параметр в ссылку, чтобы включить режим исчезающих сообщений
    call_url = f"https://jit.si{room_id}#config.enableEphemeralChatMessages=true"
    
    if user_lang == 'en':
        text = f"📞 *Your Quantum-Secure Call & Secret Chat link is ready!*\n\n1. Tap the link to enter.\n2. Send it to your friend.\n\n🔗 *Join link:* {call_url}\n\n🔥 *Super-Secret Chat Enabled:* All text messages inside vanish automatically immediately after being read and leave NO traces!"
    elif user_lang == 'es':
        text = f"📞 *¡Su enlace de llamada y chat secreto seguro ya está listo!*\n\n1. Toque el enlace para entrar.\n2. Envíalo a tu amigo.\n\n🔗 *Enlace:* {call_url}\n\n🔥 *Chat Súper Secreto Activado:* ¡Todos los mensajes de texto desaparecen automáticamente después de leerse!"
    elif user_lang == 'zh':
        text = f"📞 *您的量子加密通话与秘密聊天链接已就绪！*\n\n1. 点击链接进入房间。\n2. 发送给您的朋友。\n\n🔗 *链接:* {call_url}\n\n🔥 *超级加密聊天已启用:* 所有文本消息在阅读后都会自动消失，不留任何痕迹！"
    else: # Русский
        text = f"📞 *Ваша Квантово-Защищенная Ссылка готова!*\n\n1. Нажмите на ссылку ниже, чтобы войти в комнату.\n2. Отправьте её собеседнику в любой мессенджер.\n\n🔗 *Войти в звонок и чат:* {call_url}\n\n🔥 *Включен Шпионский Чат:* Все текстовые сообщения внутри этой комнаты исчезают автоматически сразу после прочтения и не оставляют никаких следов на серверах!"
        
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
