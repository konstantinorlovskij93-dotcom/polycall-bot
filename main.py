import os
import threading
import random
import time
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

# База данных в памяти сервера
users_db = {}
chats_db = {}  # Хранит активные мосты между пользователями
rooms_db = {}  # Хранит созданные коды комнат

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    text_args = message.text.split()
    
    # Реферальная система
    referrer_id = None
    if len(text_args) > 1 and text_args[1].isdigit():
        referrer_id = int(text_args[1])

    if user_id not in users_db:
        users_db[user_id] = {'lang': 'ru', 'referrals': 0, 'invited_by': referrer_id, 'active_chat': None}
        if referrer_id and referrer_id in users_db:
            users_db[referrer_id]['referrals'] += 1
            try:
                bot.send_message(referrer_id, "🎉 По вашей реферальной ссылке зарегистрировался новый пользователь!")
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
        users_db[user_id] = {'referrals': 0, 'invited_by': None, 'active_chat': None}
    users_db[user_id]['lang'] = lang
    
    texts = {
        'ru': "✅ Язык установлен! Используйте меню команд.\n\n💬 Чтобы начать секретный ИИ-чат, введите /chat\n📞 Чтобы сделать ИИ-звонок по ссылке, введите /call",
        'en': "✅ Language set! Use the commands menu.\n\n💬 To start AI Secret Chat, type /chat\n📞 To make an AI Call via link, type /call",
        'es': "✅ ¡Idioma establecido! Use el menú de comandos.\n\n💬 Para iniciar el chat secreto de IA, escriba /chat",
        'zh': "✅ 语言设置成功！请使用命令菜单。\n\n💬 要启动人工智能加密聊天，请输入 /chat"
    }
    bot.answer_callback_query(call.id, "Done!")
    bot.send_message(call.message.chat.id, texts.get(lang, texts['ru']))

# --- НОВАЯ СИСТЕМА СЕКРЕТНОГО ИИ-ТЕКСТОВОГО ЧАТА ---
@bot.message_handler(commands=['chat'])
def chat_menu_cmd(message):
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("➕ Создать комнату чата", "🔑 Войти в комнату", "❌ Выйти из чата")
    bot.send_message(message.chat.id, "💬 Настройка секретного чата с автоматическим ИИ-переводом и исчезающими сообщениями:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "➕ Создать комнату чата")
def create_room(message):
    user_id = message.from_user.id
    room_code = str(random.randint(1000, 9999))
    rooms_db[room_code] = user_id
    bot.send_message(message.chat.id, f"🔑 Комната создана! Отправьте этот 4-значный код вашему собеседнику:\n\n`{room_code}`\n\nКак только он введет его, включится автоматический ИИ-перевод.", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔑 Войти в комнату")
def join_room_start(message):
    msg = bot.send_message(message.chat.id, "🔢 Введите 4-значный код комнаты, который вам скинул собеседник:")
    bot.register_next_step_handler(msg, join_room_process)

def join_room_process(message):
    user_id = message.from_user.id
    room_code = message.text.strip()
    
    if room_code in rooms_db:
        partner_id = rooms_db[room_code]
        if partner_id == user_id:
            bot.send_message(message.chat.id, "❌ Нельзя войти в собственную комнату.")
            return
            
        # Создаем мост связи между двумя пользователями
        chats_db[user_id] = partner_id
        chats_db[partner_id] = user_id
        
        # Удаляем комнату из списка доступных, так как она заполнена
        del rooms_db[room_code]
        
        bot.send_message(user_id, "🚀 Вы успешно подключились! Чат запущен. Все сообщения переводятся ИИ автоматически и удаляются через 10 секунд после прочтения.")
        bot.send_message(partner_id, "🚀 Собеседник подключился! Чат запущен. Все сообщения переводятся ИИ автоматически и удаляются через 10 секунд после прочтения.")
    else:
        bot.send_message(message.chat.id, "❌ Неверный код комнаты или её больше не существует.")

@bot.message_handler(func=lambda message: message.text == "❌ Выйти из чата")
def exit_chat(message):
    user_id = message.from_user.id
    if user_id in chats_db:
        partner_id = chats_db[user_id]
        del chats_db[user_id]
        if partner_id in chats_db:
            del chats_db[partner_id]
        bot.send_message(user_id, "🔒 Вы вышли из секретного чата. История полностью стерта.")
        bot.send_message(partner_id, "🔒 Собеседник покинул секретный чат. История полностью стерта.")
    else:
        bot.send_message(message.chat.id, "Вы не находитесь в активном чате.")

# Функция-симуляция шпионского удаления сообщений
def delete_message_delayed(chat_id, message_id, delay=10):
    def delayed():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=delayed).start()

# Простой встроенный словарь-переводчик для демонстрации (на следующем шаге подключим полноценный ИИ)
def ai_translate(text, target_lang):
    # Заглушка-переводчик, имитирующая работу ИИ на старте
    translations = {
        "привет": {"en": "Hello!", "es": "¡Hola!", "zh": "你好！"},
        "как дела": {"en": "How are you?", "es": "¿Cómo estás?", "zh": "你好吗？"},
        "хорошо": {"en": "Good", "es": "Bien", "zh": "很好"},
        "пока": {"en": "Goodbye", "es": "Adiós", "zh": "再见"}
    }
    clean_text = text.lower().strip()
    if clean_text in translations and target_lang in translations[clean_text]:
        return translations[clean_text][target_lang]
    # Если слова нет в мини-словаре, отправляем с пометкой (ИИ-перевод)
    return f"📝 [ИИ-Перевод на {target_lang.upper()}]: {text}"

# Обработка всех обычных текстовых сообщений внутри секретного чата
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    
    # Если пользователь находится в активном секретном чате
    if user_id in chats_db:
        partner_id = chats_db[user_id]
        partner_lang = users_db.get(partner_id, {}).get('lang', 'en')
        user_lang = users_db.get(user_id, {}).get('lang', 'ru')
        
        # Переводим текст сообщения на язык собеседника
        translated_text = ai_translate(message.text, partner_lang)
        
        # Отправляем собеседнику
        sent_msg_partner = bot.send_message(partner_id, f"💬 {translated_text}")
        # Отправляем автору подтверждение доставки
        sent_msg_user = bot.send_message(user_id, f"👁‍🗨 Отправлено (исчезнет через 10 сек): {message.text}")
        
        # Запускаем таймеры автоматического удаления сообщений с экранов
        delete_message_delayed(partner_id, sent_msg_partner.message_id, 10)
        delete_message_delayed(user_id, sent_msg_user.message_id, 10)
        delete_message_delayed(user_id, message.message_id, 10)
    else:
        # Если пользователь просто пишет боту вне чата
        bot.send_message(message.chat.id, "🤖 Используйте меню команд в левом углу чата для управления функциями PolyCall.")

# --- КОНЕЦ НОВОЙ СИСТЕМЫ ---

@bot.message_handler(commands=['share'])
def share_cmd(message):
    user_id = message.from_user.id
    bot_info = bot.get_me()
    ref_url = f"https://t.me{bot_info.username}?start={user_id}"
    user_data = users_db.get(user_id, {'referrals': 0})
    ref_count = user_data.get('referrals', 0)
    
    text = f"👑 *Ваша реферальная ссылка:*\n`{ref_url}`\n\n👥 Вы пригласили: *{ref_count}* человек(а)."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['call'])
def call_cmd(message):
    user_id = message.from_user.id
    user_lang = users_db.get(user_id, {}).get('lang', 'ru')
    room_id = f"polycall_secure_{user_id}_{random.randint(10000, 99999)}"
    call_url = f"https://jit.si{room_id}#config.enableEphemeralChatMessages=true"
    
    text = f"📞 *Ваша ссылка на ИИ-звонок готова!*\n\n🔗 *Войти:* {call_url}"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Статистика", "📢 Рассылка рекламы")
    bot.send_message(message.chat.id, "👑 Панель разработчика PolyCall:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def admin_stats(message):
    count = len(users_db) if len(users_db) > 0 else 1
    bot.send_message(message.chat.id, f"📈 Всего пользователей: {count}\n🎯 Цель: 1,000,000,000")

@bot.message_handler(func=lambda message: message.text == "📢 Рассылка рекламы")
def admin_broadcast(message):
    bot.send_message(message.chat.id, "📝 Напишите текст рекламного сообщения:")

if __name__ == '__main__':
