print('--------')
print('start bot')
print('--------')
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import random
import datetime

# Токен вашей группы ВКонтакте
token = 'vk1.a.gRVIE6L3lRe2hdKPIAtQaQB2fPvXdMRsYpJsN-dh819zvzzTySZeCEAXCg3VgWo_hTkcQ9Xa2pMZSCPYkYujtNe7Xnm4w-mhAfnDXg2xTzIz_oa50RAl8_35HAXLCaj8DzNoo7cr_sssr4DG2xp5xO-ONsIlFLyFJ9qmJCr2GNxpCl7aM-cnf7Zg9r1xwNVd_cWYKWohNGqrdIK4RGUniQ'

# Создание объекта VK API
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()

# Создание соединения с базой данных
conn = sqlite3.connect('game_data.db')
cursor = conn.cursor()

# Создание таблицы игроков, если ее нет
cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY,
        name TEXT,
        health INTEGER,
        attack INTEGER,
        defense INTEGER,
        gold INTEGER,
        balans INTEGER,
        status TEXT,
        uzers_id INTEGER,
        ban INTEGER
    )
''')
conn.commit()

# Функция для получения информации об игроке из базы данных
def get_player(user_id):
    cursor.execute('SELECT * FROM players WHERE id = ?', (user_id,))
    player = cursor.fetchone()
    if player:
        return {
            'id': player[0],
            'name': player[1],
            'health': player[2],
            'attack': player[3],
            'defense': player[4],
            'gold': player[5],
            'balans': player[6],
            'status': player[7],
            'uzers_id': player[8],
            'ban': player[9]
        }
    else:
        return None

# Функция для создания нового игрока в базе данных
idd = 0
def create_player(user_id, name):
    global idd  # Объявляем, что мы работаем с глобальной переменной
    idd += 1  # Увеличиваем счетчик

    cursor.execute('INSERT INTO players (id, name, health, attack, defense, gold, balans, status, uzers_id, ban) VALUES (?, ?, 100, 10, 5, 0, 0, "Игрок", ?, 0)', (user_id, name, idd))
    conn.commit()

# Функция для отправки сообщения пользователю
def send_message(user_id, message, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=0,
        keyboard=keyboard.get_keyboard() if keyboard else None
    )
def ban_player(vk_id):
    """Банит игрока по VK ID."""
    player = get_player(vk_id)
    if player:
        player["ban"] = 1
        cursor.execute('UPDATE players SET ban = ? WHERE id = ?', (1, vk_id))
        conn.commit()
        send_message(vk_id, 'Вы заблокированы администратором!')
        return True
    else:
        return False
def unban_player(vk_id):
    """unban игрока по VK ID."""
    player = get_player(vk_id)
    if player:
        player["ban"] = 0
        cursor.execute('UPDATE players SET ban = ? WHERE id = ?', (0, vk_id))
        conn.commit()
        send_message(vk_id, 'Вы разблокированны  администратором!')
        return True
    else:
        return False
def log_message(user_id, message):
    with open('logs.txt', 'a', encoding='utf-8') as file:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file.write(f"[{timestamp}] Пользователь {user_id}: {message}\n")
# Обработка событий long poll
longpoll = VkLongPoll(vk_session)
for event in longpoll.listen():
    # Обработка новых сообщений
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text.lower()
        player = get_player(user_id)
        log_message(user_id, text)


        if player and player["ban"] == 1:
            send_message(user_id, 'Уважаемый игрок, вы заблокированы администратором.')
            continue  # Переходим к следующему событию

        # Проверка статуса администратора
        if player and player["status"] == "admin":
            if text.startswith("разбан ") or text.startswith("/unban "):
                try:
                    target_id = int(text.split()[1])
                    if unban_player(target_id):
                        send_message(user_id, f'Игрок с VK ID {target_id} разблокирован.')
                    else:
                        send_message(user_id, f'Игрок с VK ID {target_id} не найден.')
                except ValueError:
                    send_message(user_id, 'Неверный VK ID.')
            elif text.startswith("бан ") or text.startswith("/ban "):  # Проверяем на команду "бан" только если "разбан" не подходит
                try:
                    target_id = int(text.split()[1])
                    if ban_player(target_id):
                        send_message(user_id, f'Игрок с VK ID {target_id} забанен.')
                    else:
                        send_message(user_id, f'Игрок с VK ID {target_id} не найден.')
                except ValueError:
                    send_message(user_id, 'Неверный VK ID.')
            elif text.startswith("/ban") or text.startswith("/unban"):
                send_message(user_id, 'Использование команд "/unban [vk id]" или "/ban [vk id]"')  # Объединенное сообщение

        if not player:
            user_info = vk.users.get(user_ids=user_id, fields='first_name, last_name')[0]
            name = f'{user_info["first_name"]} {user_info["last_name"]}'  # Формируем имя
            # Создаем игрока в базе данных
            create_player(user_id, name)
            player = get_player(user_id)  # Обновляем player после создания
            send_message(user_id, f'Спасибо за регистрацию в нашем боте !')

        #if text == 'Начать':
            #send_message(user_id, f'Добро пожаловать в игру, {player["name"]}!')
        elif text == 'профиль' or text == "stats" or text == 'проф':
            if player:  # Проверяем, не равен ли player None
                send_message(user_id, f'Твои профиль:\n'
                                        f'Здоровье: {player["health"]}\n'
                                        f'Атака: {player["attack"]}\n'
                                        f'Защита: {player["defense"]}\n'
                                        f'Золото: {player["gold"]}\n'
                                        f'Баланс: {player["balans"]}\n'
                                        f'VK ID: {player["id"]}\n'
                                        f'Статус: {player["status"]}\n'
                                        f'ID: {player["uzers_id"]}')
            else:
                send_message(user_id, 'Ты еще не зарегистрирован в игре! Напиши "Начать", чтобы начать.')
        elif text == 'атака':
            # Логика атаки на монстра (не реализовано)
            send_message(user_id, 'Атака!')
        elif text == 'магазин':
            # Логика магазина (не реализовано)
            send_message(user_id, 'Магазин!')
        else:
            send_message(user_id, 'Я тебя не понимаю. Введи "профиль", "атака" или "магазин".')

            # Создание клавиатуры с кнопками
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button('Профиль', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('Атака', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('Магазин', color=VkKeyboardColor.PRIMARY)
            send_message(user_id, 'Выберите действие:', keyboard)

# Закрытие соединения с базой данных
conn.close()
