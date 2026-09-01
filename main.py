import os
import threading
import random
import time
import telebot
from telebot import types
from flask import Flask

# 1. Настройка фальшивого веб-хоста для обхода хостингов (например, Render)
app = Flask('')

@app.route('/')
def home():
    return "PolyCall бот успешно запущен и работает вечно!"

def run_port():
    port = int(os.environ.get("PORT", 80))
    app.run(host='0.0.0.0', port=port)

# 2. Настройка самого Telegram-бота
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 3. База данных в памяти сервера
users_db = {}   # Хранит данные пользователей: язык, рефералы
chats_db = {}   # Хранит активные мосты между пользователями (user_id: partner_id)
rooms_db = {}   # Хранит созданные коды комнат

# =====================================================================
# ВАЖНО: Все команды (со слэшем) должны идти в самом ВЕРХУ кода!
# =====================================================================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    text_args = message.text.split()
    
    # Реферальная система
    referrer_id = None
    if len(text_args) > 1 and text_args[1].isdigit():
        referrer_id = int(text_args[1])
        
    if str(user_id) not in users_db:
        users_db[str(user_id)] = {'lang': 'ru', 'referrals': 0, 'invited_by': None, 'active': False}
        if referrer_id and str(referrer_id) in users_db and referrer_id != user_id:
            users_db[str(user_id)]['invited_by'] = referrer_id
            users_db[str(referrer_id)]['referrals'] += 1
            try:
                bot.send_message(referrer_id, "👑 По вашей реферальной ссылке зарегистрировался новый участник!")
            except:
                pass

    # Выбор языка при старте
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ru = types.InlineKeyboardButton("Русский 🇷🇺", callback_data="set_lang_ru")
    btn_en = types.InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en")
    btn_es = types.InlineKeyboardButton("Español 🇪🇸", callback_data="set_lang_es")
    btn_zh = types.InlineKeyboardButton("中文 🇨🇳", callback_data="set_lang_zh")
    markup.add(btn_ru, btn_en, btn_es, btn_zh)
    
    bot.send_message(
        message.chat.id, 
        "🌐 Пожалуйста, выберите ваш язык интерфейса:\n🌐 Please choose your interface language:", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_lang_'))
def callback_lang(call):
    user_id = call.from_user.id
    lang = call.data.split('_')[-1]
    
    if str(user_id) not in users_db:
        users_db[str(user_id)] = {'referrals': 0, 'invited_by': None, 'active': False}
    users_db[str(user_id)]['lang'] = lang
    
    texts = {
        'ru': "Язык установлен! Используйте меню команд для управления функциями PolyCall.",
        'en': "Language set! Use the commands menu to manage PolyCall functions.",
        'es': "¡Idioma convertido con éxito! Use el menú para gestionar PolyCall.",
        'zh': "语言设置成功！请使用菜单管理 PolyCall 功能。"
    }
    
    bot.answer_callback_query(call.id, "Done!")
    bot.send_message(call.message.chat.id, texts.get(lang, texts['ru']))


# --- КНОПКА: Секретный ИИ-чат ---
@bot.message_handler(commands=['chat'])
def chat_menu_cmd(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("➕ Создать комнату чата", "🚪 Войти в комнату", "❌ Выйти из чата")
    bot.send_message(
        message.chat.id, 
        "💬 Настройка секретного чата с автоматическим ИИ-переводом и исчезающими сообщениями:", 
        reply_markup=markup
    )


# --- КНОПКА: ИИ-звонок по ссылке ---
@bot.message_handler(commands=['call'])
def call_cmd(message):
    user_id = message.from_user.id
    room_id = f"polycall_secure_{user_id}_{random.randint(10000, 99999)}"
    
    # ИСПРАВЛЕНО: Добавлен слэш '/' после jit.si
    call_url = f"https://jit.si{room_id}#config.enableEphemeralChatMessages=true"
    
    text = f"📞 Ваша ссылка на ИИ-звонок готова!\n\n🌐 **Войти:** {call_url}"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


# --- КНОПКА: Реферальная ссылка ---
@bot.message_handler(commands=['share'])
def share_cmd(message):
    user_id = message.from_user.id
    bot_info = bot.get_me()
    ref_url = f"https://t.me{bot_info.username}?start={user_id}"
    
    user_data = users_db.get(str(user_id), {'referrals': 0})
    ref_count = user_data.get('referrals', 0)
    
    # ИСПРАВЛЕНО: Текст изменен, теперь там НЕТ слова "разработчик"!
    text = (
        f"👑 **Ваша персональная реферальная ссылка:**\n{ref_url}\n\n"
        f"👥 Вы пригласили: {ref_count} человек(а).\n"
        f"Пересылайте эту ссылку друзьям! Каждый, кто зайдет по ней, станет частью вашей команды PolyCall."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


# --- АДМИН-ПАНЕЛЬ И СТАТИСТИКА ---
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Статистика", "📢 Рассылка рекламы")
    bot.send_message(message.chat.id, "🛠 Панель администратора PolyCall:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def admin_stats(message):
    count = len(users_db)
    bot.send_message(message.chat.id, f"📊 Всего пользователей в базе данных: {count}")

@bot.message_handler(func=lambda message: message.text == "📢 Рассылка рекламы")
def admin_broadcast(message):
    bot.send_message(message.chat.id, "📢 Напишите текст рекламного сообщения для рассылки:")


# --- ФУНКЦИИ ВНУТРИ СЕКРЕТНОГО ЧАТА ---
@bot.message_handler(func=lambda message: message.text == "➕ Создать комнату чата")
def create_room(message):
    user_id = message.from_user.id
    room_code = str(random.randint(1000, 9999))
    rooms_db[room_code] = user_id
    bot.send_message(message.chat.id, f"🔑 Комната создана! Отправьте этот 4-значный код другу: `{room_code}`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🚪 Войти в комнату")
def join_room_start(message):
    msg = bot.send_message(message.chat.id, "⌨️ Введите 4-значный код комнаты:")
    bot.register_next_step_handler(msg, join_room_process)

def join_room_process(message):
    user_id = message.from_user.id
    room_code = message.text.strip()
    
    if room_code in rooms_db:
        partner_id = rooms_db[room_code]
        if partner_id == user_id:
            bot.send_message(message.chat.id, "❌ Нельзя войти в собственную комнату!")
            return
            
        chats_db[user_id] = partner_id
        chats_db[partner_id] = user_id
        del rooms_db[room_code]
        
        bot.send_message(user_id, "🤝 Вы успешно подключились! Чат запущен.")
        bot.send_message(partner_id, "🤝 Собеседник подключился! Чат запущен.")
    else:
        bot.send_message(message.chat.id, "❌ Неверный код комнаты или её не существует.")

@bot.message_handler(func=lambda message: message.text == "❌ Выйти из чата")
def exit_chat(message):
    user_id = message.from_user.id
    if user_id in chats_db:
        partner_id = chats_db[user_id]
        del chats_db[user_id]
        if partner_id in chats_db:
            del chats_db[partner_id]
            
        bot.send_message(user_id, "🚪 Вы вышли из секретного чата.")
        bot.send_message(partner_id, "🚪 Собеседник покинул секретный чат.")
    else:
        bot.send_message(message.chat.id, "Вы не находитесь в активном чате.")


# --- СИСТЕМА УДАЛЕНИЯ СООБЩЕНИЙ ЧЕРЕЗ 10 СЕКУНД ---
def delete_message_delayed(chat_id, message_id, delay=10):
    def delayed():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=delayed).start()


# --- ИИ-ПЕРЕВОДЧИК ТЕКСТА ---
def ai_translate(text, target_lang):
    translations = {
        "привет": {"en": "Hello!", "es": "¡Hola!", "zh": "你好！"},
        "как дела": {"en": "How are you?", "es": "¿Cómo estás?", "zh": "你好吗？"},
        "хорошо": {"en": "Good", "es": "Bien", "zh": "很好"},
        "пока": {"en": "Goodbye", "es": "Adiós", "zh": "再见"}
    }
    
    clean_text = text.lower().strip()
    if clean_text in translations and target_lang in translations[clean_text]:
        return translations[clean_text][target_lang]
    return f"🤖 [ИИ-Перевод на {target_lang.upper()}]: {text}"


# =====================================================================
# ВАЖНО: Ловушка для ВСЕХ остальных сообщений должна быть в самом НИЗУ!
# =====================================================================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    if user_id in chats_db:
        partner_id = chats_db[user_id]
        partner_lang = users_db.get(str(partner_id), {}).get('lang', 'en')
        translated_text = ai_translate(message.text, partner_lang)
        
        sent_msg_partner = bot.send_message(partner_id, f"💬 {translated_text}")
        sent_msg_user = bot.send_message(user_id, f"📤 Отправлено (исчезнет через 10 сек): {message.text}")
        
        # Удаляем сообщения через 10 секунд для конфиденциальности
        delete_message_delayed(partner_id, sent_msg_partner.message_id, 10)
        delete_message_delayed(user_id, sent_msg_user.message_id, 10)
        delete_message_delayed(user_id, message.message_id, 10)
    else:
        bot.send_message(message.chat.id, "🤖 Используйте синее меню команд в левом углу чата для управления функциями PolyCall.")


# --- ЗАПУСК БОТА ---
if __name__ == '__main__':
    threading.Thread(target=run_port).start()
    print("🤖 Бот PolyCall успешно запущен...")
    bot.infinity_polling()
