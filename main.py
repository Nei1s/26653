import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Настройки
GROUP_ID = os.getenv('GROUP_ID', '229086233')  # Значение по умолчанию, если переменная окружения не задана
GROUP_TOKEN = os.getenv('Token', 'vk1.a.9t_gRlRTYR0ZMLlhanlQuDeauO9QY98gXEoQjYtgRyrya6exemHNuv_PlxmR00Q_UQY7pOq7Mlt9pdIAwL4AS1hVtV4xNqGLyVXprkdYqc_OFWP84Yn4jItRanwngg-YuIPqke-yQN1vF0Wk41ikeUz0IHSRcLo_bVhmxX3-74qUPzntBRirM4zjDA-y8dJvjYeFaNh3rhqkBFEqLOt8Uw')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'bd.db')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '240052793').split(',')]

# Проверка наличия токена и ID группы
if not GROUP_TOKEN:
    logging.error("Токен группы не указан. Убедитесь, что переменная окружения 'Token' установлена.")
    exit(1)

if not GROUP_ID:
    logging.error("ID группы не указан. Убедитесь, что переменная окружения 'GROUP_ID' установлена.")
    exit(1)

# Подключение к ВК
try:
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    logging.info("Успешное подключение к VK API и LongPoll серверу.")
except Exception as e:
    logging.error(f"Ошибка подключения к VK API: {e}")
    exit(1)

# Подключение к базе данных
try:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    logging.info("Успешное подключение к базе данных.")
except Exception as e:
    logging.error(f"Ошибка подключения к базе данных: {e}")
    exit(1)

# Создание таблицы, если её нет
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS votes (
        user_id INTEGER PRIMARY KEY,
        gender TEXT CHECK(gender IN ('male', 'female')),
        vote TEXT
    )
    ''')
    conn.commit()
    logging.info("Таблица votes создана или уже существует.")
except Exception as e:
    logging.error(f"Ошибка при создании таблицы: {e}")
    exit(1)

# Состояния пользователей
user_states = {}

def get_user_info(user_id):
    """Получает информацию о пользователе."""
    try:
        user_info = vk.users.get(user_ids=user_id, fields='sex')[0]
        logging.info(f"Информация о пользователе {user_id} получена: {user_info}")
        return user_info
    except Exception as e:
        logging.error(f"Ошибка при получении информации о пользователе {user_id}: {e}")
        return None

def has_user_voted(user_id):
    """Проверяет, голосовал ли пользователь."""
    try:
        cursor.execute('SELECT user_id FROM votes WHERE user_id = ?', (user_id,))
        result = cursor.fetchone() is not None
        logging.info(f"Проверка голосования пользователя {user_id}: {'уже голосовал' if result else 'еще не голосовал'}")
        return result
    except Exception as e:
        logging.error(f"Ошибка при проверке голосования пользователя {user_id}: {e}")
        return False

def save_vote(user_id, gender, vote):
    """Сохраняет голос в базу данных."""
    try:
        cursor.execute('INSERT INTO votes (user_id, gender, vote) VALUES (?, ?, ?)', (user_id, gender, vote))
        conn.commit()
        logging.info(f"Голос пользователя {user_id} успешно сохранен.")
        return True
    except Exception as e:
        logging.error(f"Ошибка при сохранении голоса пользователя {user_id}: {e}")
        return False

def get_vote_statistics():
    """Возвращает статистику голосов."""
    try:
        cursor.execute('SELECT vote, COUNT(*) FROM votes GROUP BY vote')
        stats = cursor.fetchall()
        logging.info(f"Статистика голосов получена: {stats}")
        return stats
    except Exception as e:
        logging.error(f"Ошибка при получении статистики голосов: {e}")
        return []

def send_message(user_id, message, keyboard=None):
    """Отправляет сообщение пользователю."""
    try:
        params = {
            'user_id': user_id,
            'message': message,
            'random_id': 0
        }
        if keyboard:
            params['keyboard'] = keyboard.get_keyboard()
        vk.messages.send(**params)
        logging.info(f"Сообщение отправлено пользователю {user_id}: {message}")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

def create_keyboard():
    """Создаёт клавиатуру с кнопками."""
    keyboard = VkKeyboard(one_time=True)
    
    # Первая строка
    keyboard.add_button('Алина Комарова', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Валентина Омаровна', color=VkKeyboardColor.PRIMARY)
    
    # Вторая строка
    keyboard.add_line()
    keyboard.add_button('Алевтина Окулова', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Ольга Макулова', color=VkKeyboardColor.PRIMARY)
    
    # Третья строка
    keyboard.add_line()
    keyboard.add_button('Виктория Мормышкина', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Алена Ненайкина', color=VkKeyboardColor.PRIMARY)
    
    logging.info("Клавиатура создана.")
    return keyboard

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором."""
    result = user_id in ADMIN_IDS
    logging.info(f"Проверка прав администратора для пользователя {user_id}: {'является администратором' if result else 'не является администратором'}")
    return result

def clear_user_state(user_id):
    """Очищает состояние пользователя."""
    if user_id in user_states:
        del user_states[user_id]
    candidate_key = f"{user_id}_candidate"
    if candidate_key in user_states:
        del user_states[candidate_key]
    logging.info(f"Состояние пользователя {user_id} очищено.")

# Основной цикл бота
try:
    logging.info("Бот запущен и ожидает событий...")
    for event in longpoll.listen():
        logging.info(f"Получено событие: {event.type}")
        if event.type == VkBotEventType.MESSAGE_NEW:
            user_id = event.message['from_id']
            text = event.message['text'].lower()
            logging.info(f"Новое сообщение от пользователя {user_id}: {text}")

            # Команда для администратора
            if text == 'результаты' and is_admin(user_id):
                stats = get_vote_statistics()
                if stats:
                    message = "Результаты голосования:\n"
                    for vote, count in stats:
                        message += f"{vote}: {count} голосов\n"
                else:
                    message = "Голосов пока нет."
                send_message(user_id, message)
                continue

            # Проверка, голосовал ли пользователь
            if has_user_voted(user_id):
                send_message(user_id, 'Вы уже проголосовали!')
                continue

            # Получаем информацию о пользователе
            user_info = get_user_info(user_id)
            if not user_info:
                send_message(user_id, 'Не удалось получить информацию о вас. Попробуйте позже.')
                continue

            gender = 'male' if user_info['sex'] == 2 else 'female'

            # Проверка пола
            if gender != 'male':
                send_message(user_id, 'Голосовать могут только мужчины.')
                continue

            # Если пользователь в состоянии ожидания подтверждения
            if user_id in user_states and user_states[user_id] == 'waiting_confirmation':
                # Сохраняем голос
                if save_vote(user_id, gender, user_states[f"{user_id}_candidate"]):
                    send_message(user_id, f'Ваш голос за "{user_states[f"{user_id}_candidate"]}" учтён!')
                else:
                    send_message(user_id, 'Произошла ошибка при сохранении вашего голоса. Попробуйте позже.')
                clear_user_state(user_id)
                continue

            # Обработка выбора кандидата
            if text in ['алина комарова', 'валентина омаровна', 'алевтина окулова', 'ольга макулова', 'виктория мормышкина', 'алена ненайкина']:
                user_states[user_id] = 'waiting_confirmation'
                user_states[f"{user_id}_candidate"] = text
                send_message(user_id, f'Вы выбрали "{text}". Подтвердите ваш выбор, отправив "да".')
                continue

            # Подтверждение выбора
            if text == 'да' and user_id in user_states and user_states[user_id] == 'waiting_confirmation':
                if save_vote(user_id, gender, user_states[f"{user_id}_candidate"]):
                    send_message(user_id, f'Ваш голос за "{user_states[f"{user_id}_candidate"]}" учтён!')
                else:
                    send_message(user_id, 'Произошла ошибка при сохранении вашего голоса. Попробуйте позже.')
                clear_user_state(user_id)
                continue

            # Если пользователь отправил любое другое сообщение, отправляем клавиатуру
            keyboard = create_keyboard()
            send_message(user_id, "Добро пожаловать! Это бот для голосования. Пожалуйста, выберите вариант голосования из предложенных ниже:", keyboard)
            logging.info(f"Пользователь {user_id} отправил сообщение: {text}. Отправлена клавиатура.")

except Exception as e:
    logging.error(f"Ошибка в основном цикле бота: {e}", exc_info=True)
finally:
    conn.close()
    logging.info("Соединение с базой данных закрыто.")