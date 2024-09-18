import telebot
import math
import sqlite3
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import io
from itertools import zip_longest
from telebot import types

matplotlib.use('Agg') # Чтобы убрать ошибку (использует бэкенд Agg (Anti-Grain Geometry))

token = ''
bot = telebot.TeleBot(token)
id_send = '' # В какой чат отправить информацию об использовании
administrator = 'kurillccc' # Кого не учитываем при отправке
table_with_mailling_list = 'maillig_list'

# Подключаем базу данных
conn = sqlite3.connect('BaseD_Math.db', check_same_thread=False)
cursor = conn.cursor() # создаем курсор для работы с таблицами

### Код для администратор (отправка сообщений)
### --- Функция для отправки сообщения всем пользователям
@bot.message_handler(commands=['send'])
def send(message):
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    if (message.from_user.username == administrator):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Send to all users", callback_data='all_users')
        btn2 = types.InlineKeyboardButton("Show all users", callback_data='show_all_users')
        btn3 = types.InlineKeyboardButton("Send to one specific user", callback_data='specific_user')
        btn4 = types.InlineKeyboardButton("Close", callback_data='close')
        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)
        markup.add(btn4)
        bot.send_message(chat_id, f'Choose an action:', reply_markup=markup)
        bot.callback_query_handler(func=settings_for_administration)
    else:
        bot.send_message(id_send, f'⚠️@{message.from_user.username} пытался воспользоваться командой send ⚠️\nUser id: {message.from_user.id} \nUser name: {user_name}\n🤖: Math_bot ')  # Отправка сообщения в канал
        return
@bot.callback_query_handler(func=lambda call: call.data in ['all_users', 'show_all_users', 'specific_user', 'close'])
def settings_for_administration(call):
    if (call.data == 'all_users'):
        msg = bot.send_message(call.message.chat.id, f'Write the text:\n(write /stop to stop)')
        bot.register_next_step_handler(msg, all_users_send)
    elif (call.data == 'show_all_users'):
        chat_id = show_the_all_table_2('user_id')
        name = show_the_all_table_2('username')
        result = array_sum(chat_id, name)
        bot.send_message(call.message.chat.id, f'{result}')
    elif (call.data == 'specific_user'):
        msg = bot.send_message(call.message.chat.id, f'Send the user\'s chat id:\n(write /stop to stop)')
        bot.register_next_step_handler(msg, specific_user)
    elif (call.data == 'close'):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return
# Для отравки сообщения всем пользователям
def all_users_send(message):
    if (message.text == '/stop'):
        return
    text = message.text
    cursor.execute(f"SELECT * FROM {table_with_mailling_list}")
    result = cursor.fetchall()
    column_index = 1  # индекс колонки с чат id
    column = [row[column_index] for row in result]
    if message.photo:
        # Получаем информацию о фото
        photo = message.photo[-1]  # берем последнее (наилучшее) фото из списка
        file_id = photo.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        for id in column:
            try:
                # Получаем текстовое сообщение, которое пришло с фото (если есть)
                caption = message.caption if message.caption is not None else ""
                # Отправляем фото и текст обратно пользователю
                bot.send_photo(id, file, caption=caption, parse_mode='HTML')
            except:
                pass
    else:
        for id in column:
            try:
                send_message_to_user(id, text)
            except:
                pass
# Для обработки сообщения с конкретным пользователем
def specific_user(message):
    if (message.text == "📝 Расчеты"):
        return
    if (message.text == '/stop'):
        return
    user_id = int(message.text)
    text = bot.send_message(message.chat.id, f'Write the text\n(write /stop to stop)')
    bot.register_next_step_handler(text, send_text_specific_user, user_id)
def send_text_specific_user(message, user_id):
    if (message.text == '/stop'):
        return
    text = message.text
    if message.photo:
        # Получаем информацию о фото
        photo = message.photo[-1]  # берем последнее (наилучшее) фото из списка
        file_id = photo.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        try:
            # Получаем текстовое сообщение, которое пришло с фото (если есть)
            caption = message.caption if message.caption is not None else ""
            # Отправляем фото и текст обратно пользователю
            bot.send_photo(user_id, file, caption=caption, parse_mode='HTML')
        except:
            bot.send_message(message.chat.id, f'Not sent')
            return
        bot.send_message(message.chat.id, f'Successfully')
    else:
        try:
            send_message_to_user(user_id, text)
        except:
            bot.send_message(message.chat.id, f'Not sent')
            return
        bot.send_message(message.chat.id, f'Successfully')

# Для отправки сообщения пользователю
def send_message_to_user(user_id: int, text: str):
    bot.send_message(user_id, f'{text}', parse_mode="html".format(user_id))

# Для создания таблицы (чтобы в случае переноса бота, не создавать в базе данных таблицу вручную)
def pass_in_maillig_list(user_id: int, username: str, user_name: str, user_sername: str):
    cursor.execute('''CREATE TABLE {}
                            (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                            user_id INTEGER UNIQUE,
                            username TEXT,
                            user_name TEXT,
                            user_sername TEXT)'''.format(table_with_mailling_list))
    cursor.execute(f'INSERT INTO {table_with_mailling_list} (user_id, username, user_name, user_sername) VALUES (?, ?, ?, ?)', (user_id, username, user_name, user_sername))
    conn.commit()
def show_the_all_table_2(name_of_the_column: str): # тут сортирвовка по id иначе код будет неправильно все выдавать (именно числа)
    cursor.execute(f"SELECT {name_of_the_column} FROM {table_with_mailling_list} ORDER BY id")
    res = cursor.fetchall()  # записали столбец
    result_array = [r[0] for r in res]
    return result_array
def array_sum(arr1, arr2):
    result = "".join([f"📌 {a}   -   {b}\n" for a, b in zip(arr1, arr2)])
    return result
#############################################
@bot.message_handler(commands=['start'])
def start(message):
    username = '@' + message.from_user.username
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    user_sername = message.from_user.last_name
    try:
        cursor.execute(f'INSERT INTO {table_with_mailling_list} (user_id, username, user_name, user_sername) VALUES (?, ?, ?, ?)', (chat_id, username, user_name, user_sername))
        conn.commit()
    except:
        try:
            pass_in_maillig_list(chat_id, username, user_name, user_sername)
        except:
            pass
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📝 Расчеты")
    markup.add(btn1)
    bot.send_message(message.chat.id, text="Выбери действие: ".format(message.from_user), reply_markup=markup)

# выборка после кнопок
@bot.message_handler(content_types=['text'])
def function_first(message):
    if(message.text == "📝 Расчеты"):
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        if message.from_user.username != administrator:
            bot.send_message(id_send, f'@{message.from_user.username} нажал(-а) "📝 Расчеты" \nUser id: {user_id}\nUser name: {user_name}\nBot: Math ') # Отправка сообщения в канал
        markup = types.InlineKeyboardMarkup() # В этой выборке создаем inline кнопки
        button1 = types.InlineKeyboardButton("Погрешность", callback_data='call.pogresh')
        button2 = types.InlineKeyboardButton("Аппроксимация", callback_data='call.approksimation')
        button3 = types.InlineKeyboardButton("Корреляция", callback_data='call.corelashion')
        button4 = types.InlineKeyboardButton("Построить график", callback_data='call.creat_graph')
        markup.add(button1, button2) # Для создания inline нужно прописывать (callback_data), чтобы потом реагировать на выборку
        markup.add(button3, button4)
        bot.send_message(message.chat.id, "Выберите действие: ".format(message.from_user), reply_markup=markup)
        bot.callback_query_handler(func=function_second_1) # Для перехода в след функцию
@bot.callback_query_handler(func=lambda call: call.data in ['call.pogresh', 'call.approksimation', 'call.end', 'call.continue.pog', 'call.approksimation.continue', 'call.corelashion', 'call.creat_graph'])
def function_second_1(call):
    if call.message:
        if call.data == 'call.pogresh':  # Погрешность
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text='Введите значения через пробел: ', reply_markup=None)
            bot.register_next_step_handler(msg, start_of_pogreshnost) # Для дальнейшего перехода
        elif call.data == 'call.approksimation':    # Аппроксимация
            markup = types.InlineKeyboardMarkup()  # В этой выборке создаем inline кнопки
            button1 = types.InlineKeyboardButton("Линейная аппроксимация", callback_data='call.linear')
            button2 = types.InlineKeyboardButton("Квадратичная аппроксимация", callback_data='call.quadratic')
            button3 = types.InlineKeyboardButton("Кубическая аппроксимация", callback_data='call.cubic')
            button4 = types.InlineKeyboardButton("⬅️ Назад", callback_data='call.into_function_first')
            markup.add(button1)  # Для создания inline нужно прописывать (callback_data), чтобы потом реагировать на выборку
            markup.add(button2)
            markup.add(button3)
            markup.add(button4)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text='Выберите тип аппроксимации: ', reply_markup=markup)
            bot.callback_query_handler(func=inline_for_approksimation)
        elif call.data == 'call.corelashion':
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Введите значения x, через пробел', reply_markup=None)
            bot.register_next_step_handler(msg, start_of_corelashion)
        elif call.data == 'call.creat_graph':
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text='Введите значения x, через пробел', reply_markup=None)
            bot.register_next_step_handler(msg, creat_graph_X)
        elif call.data =='call.approksimation.continue':
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,reply_markup=None)
            markup = types.InlineKeyboardMarkup()  # В этой выборке создаем inline кнопки
            button1 = types.InlineKeyboardButton("Линейная аппроксимация", callback_data='call.linear')
            button2 = types.InlineKeyboardButton("Квадратичная аппроксимация", callback_data='call.quadratic')
            button3 = types.InlineKeyboardButton("Кубическая аппроксимация", callback_data='call.cubic')
            button4 = types.InlineKeyboardButton("⬅️ Назад", callback_data='call.into_function_first')
            markup.add(button1)  # Для создания inline нужно прописывать (callback_data), чтобы потом реагировать на выборку
            markup.add(button2)
            markup.add(button3)
            markup.add(button4)
            bot.send_message(chat_id=call.message.chat.id, text='Выберите тип аппроксимации: ', reply_markup=markup)
            bot.callback_query_handler(func=inline_for_approksimation)
        elif call.data == 'call.end':    # --Для выборки в конце погрешностей
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            return
        elif call.data == 'call.continue.pog': # Создаю отдельный call для этого, чтобы не изменять послденее собщение со значениями
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,reply_markup=None)
            msg = bot.send_message(chat_id=call.message.chat.id, text='Введите значения через пробел: ', reply_markup=None)
            bot.register_next_step_handler(msg, start_of_pogreshnost)
# ----------------------------Корреляция----------------------------
def start_of_corelashion(message):
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        x = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return
    msg = bot.send_message(message.chat.id, text='Введите значения y, через пробел ')
    bot.register_next_step_handler(msg, continue_corelashion, x)
def continue_corelashion(message, x):
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        y = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return

    # расчет средних значений
    x_mean = sum(x) / float(len(x))
    y_mean = sum(y) / float(len(y))

    # рассчитываем числитель и знаменатель корреляционной формулы
    numerator = sum([(xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)])
    denominator_X = math.sqrt(sum([(xi - x_mean) ** 2 for xi in x]))
    denominator_Y = math.sqrt(sum([(yi - y_mean) ** 2 for yi in y]))
    denominator = denominator_X * denominator_Y
    # итоговый расчет корреляции
    correlation = numerator / denominator

    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("⏮ Вернуться", callback_data='call.into_f_1_without_edit')
    button2 = types.InlineKeyboardButton("❌ Закончить", callback_data='call.end')
    markup.add(button1, button2)
    bot.send_message(message.chat.id, f"🔻 Среднее значение X: {round(x_mean, 6)}\n\n🔻 Среднее значение Y: {round(y_mean, 6)}\n\n🔻 Числитель: {round(numerator, 6)}\n\n🔻 Знаменатель с X: {round(denominator_X, 6)}\n\n🔻 Знаменатель с Y: {round(denominator_Y, 6)}\n\n🔥 Коэффициент корреляции (R): <b>{round(correlation, 6)}</b>", parse_mode="html", reply_markup=markup)
    bot.callback_query_handler(func=function_second_1)
# ----------------------------Конец----------------------------------

# ----------------------------Построить график----------------------------
def creat_graph_X(message):
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        x = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return
    msg = bot.send_message(message.chat.id, text='Введите значения y, через пробел ')
    bot.register_next_step_handler(msg, creat_graph_Y, x)
def creat_graph_Y(message, x):
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        y = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return

    # 'o-' задает стиль линии и маркеров
    plt.clf()  # Очищаем рисунок перед новой отрисовкой
    try:
        plt.plot(x, y, 'o')
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (число x должно совпадать с числом y)")
        return
    plt.title('График по точкам')
    plt.xlabel('Значения x')
    plt.ylabel('Значения y')
    # включаем дополнительные отметки на осях
    plt.minorticks_on()
    # включаем основную сетку
    plt.grid(which='major', zorder=1)
    # включаем дополнительную сетку
    plt.grid(which='minor', linestyle=':', zorder=1)
    # Сохраняем график в файл
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("⏮ Вернуться", callback_data='call.into_f_1_without_edit')
    button2 = types.InlineKeyboardButton("❌ Закончить", callback_data='call.end')
    markup.add(button1, button2)

    x_str = ' '.join(map(str, x))
    y_str = ' '.join(map(str, y))

    bot.send_photo(message.chat.id, photo=buf, caption= \
                     f'🔹 Значения X:\n {x_str}\n\n' \
                     f'🔹 Значения Y:\n {y_str}', parse_mode="html".format(message.from_user), reply_markup=markup)
    buf.close()
    del buf
    bot.callback_query_handler(func=function_second_1)

# ----------------------------Конец----------------------------------

# ----------------------------Аппроксимация----------------------------
@bot.callback_query_handler(func=lambda call: call.data in ['call.linear', 'call.quadratic', 'call.cubic', 'call.into_function_first', 'call.into_f_1_without_edit'])
def inline_for_approksimation(call):
    if call.message:
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        if call.data == 'call.linear':    # -Для линейной аппроксимации
            bot.delete_message(chat_id, message_id)
            msg = bot.send_message(chat_id=call.message.chat.id, text='Введите значения x, через пробел ')
            bot.register_next_step_handler(msg, linear_approksimation)
        elif call.data == 'call.quadratic':     # -Для квадратичной аппроксимации
            bot.delete_message(chat_id, message_id)
            msg = bot.send_message(chat_id=call.message.chat.id, text='Введите значения x, через пробел ')
            bot.register_next_step_handler(msg, quadratic_approksimation)
        elif call.data == 'call.cubic':     # -Для кубируемой аппроксимации
            bot.delete_message(chat_id, message_id)
            msg = bot.send_message(chat_id=call.message.chat.id, text='Введите значения x, через пробел ')
            bot.register_next_step_handler(msg, cubic_approksimation)
        elif call.data == 'call.into_function_first':
            #bot.delete_message(chat_id, message_id)
            key = types.InlineKeyboardMarkup()  # В этой выборке создаем inline кнопки
            button1 = types.InlineKeyboardButton("Погрешность", callback_data='call.pogresh')
            button2 = types.InlineKeyboardButton("Аппроксимация", callback_data='call.approksimation')
            button3 = types.InlineKeyboardButton("Корреляция", callback_data='call.corelashion')
            button4 = types.InlineKeyboardButton("Построить график", callback_data='call.creat_graph')
            key.add(button1,button2)  # Для создания inline нужно прописывать (callback_data), чтобы потом реагировать на выборку
            key.add(button3, button4)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text='Выберите действие: ', reply_markup=key)
            bot.callback_query_handler(func=function_second_1)  # Для перехода в след функцию
        elif call.data == 'call.into_f_1_without_edit':
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            key = types.InlineKeyboardMarkup()  # В этой выборке создаем inline кнопки
            button1 = types.InlineKeyboardButton("Погрешность", callback_data='call.pogresh')
            button2 = types.InlineKeyboardButton("Аппроксимация", callback_data='call.approksimation')
            button3 = types.InlineKeyboardButton("Корреляция", callback_data='call.corelashion')
            button4 = types.InlineKeyboardButton("Построить график", callback_data='call.creat_graph')
            key.add(button1,button2)  # Для создания inline нужно прописывать (callback_data), чтобы потом реагировать на выборку
            key.add(button3, button4)
            bot.send_message(chat_id=call.message.chat.id, text='Выберите действие: ', reply_markup=key)
            bot.callback_query_handler(func=function_second_1)  # Для перехода в след функцию
# ----Линейная аппроксимация----
def linear_approksimation(message):
    mas_x_1 = []
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        mas_x_1 = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return
    msg = bot.send_message(message.chat.id, text='Введите значения y, через пробел ')
    bot.register_next_step_handler(msg, start_of_appriksimation_y_1, mas_x_1)
# Считаем дальше для линейной аппроксимации
def start_of_appriksimation_y_1(message, mas_x_1):
    mas_y_1 = []
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        mas_y_1 = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return
    x = np.array(mas_x_1)
    y = np.array(mas_y_1)
    plus_app_b = '+'
    try:
        a, b = np.polyfit(x, y, 1)
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (число x должно совпадать с числом y)")
        return
    # Строим график
    plt.clf() # Очищаем рисунок перед новой отрисовкой
    plt.scatter(x, y, color='blue', zorder=2)
    plt.plot(x, a * x + b, color='red')
    plt.title('График линейной аппроксимации')
    plt.xlabel('Значения x')
    plt.ylabel('Значения y')
    # включаем дополнительные отметки на осях
    plt.minorticks_on()
    # включаем основную сетку
    plt.grid(which='major', zorder=1)
    # включаем дополнительную сетку
    plt.grid(which='minor', linestyle=':', zorder=1)
    # Сохраняем график в файл
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    if b < 0: plus_app_b = '-'
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("⏮ Вернуться", callback_data='call.approksimation.continue')
    button2 = types.InlineKeyboardButton("❌ Закончить", callback_data='call.end')
    markup.add(button1, button2)
    bot.send_photo(message.chat.id, photo=buf, caption=f'🔹 a = {round(a, 6)} \n\n' \
                                                       f'🔹 b = {round(b, 6)}\n\n' \
                                                       f'🔸 <b>y = {round(a, 6)}x {plus_app_b} {round(abs(b), 6)}</b>',parse_mode="html".format(message.from_user), reply_markup=markup)
    buf.close()
    del buf
    bot.callback_query_handler(func=function_second_1)
# -----Квадратичная аппроксимация-----
def quadratic_approksimation(message):
    mas_x_2 = []
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        mas_x_2 = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return
    msg = bot.send_message(message.chat.id, text='Введите значения y, через пробел ')
    bot.register_next_step_handler(msg, start_of_appriksimation_y_2, mas_x_2)
# Считаем дальше для квадратичной аппроксимации
def start_of_appriksimation_y_2(message, mas_x_2):
    mas_y_2 = []
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        mas_y_2 = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return
    x = np.array(mas_x_2)
    y = np.array(mas_y_2)
    plus_app_b = '+'
    plus_app_c = '+'
    try:
        a, b, c = np.polyfit(x, y, 2)
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (число x должно совпадать с числом y)")
        return
    # Строим график
    plt.clf()  # Очищаем рисунок перед новой отрисовкой
    plt.scatter(x, y, color='blue', zorder=2)
    plt.plot(x, a * x ** 2 + b * x + c, color='red')
    plt.title('График квадратичной аппроксимации')
    plt.xlabel('Значения x')
    plt.ylabel('Значения y')
    # включаем дополнительные отметки на осях
    plt.minorticks_on()
    # включаем основную сетку
    plt.grid(which='major', zorder=1)
    # включаем дополнительную сетку
    plt.grid(which='minor', linestyle=':', zorder=1)
    # Сохраняем график в файл
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    if b < 0: plus_app_b = '-' # Меняем, чтобы в выводе был аккуратный минус
    if c < 0: plus_app_c = '-'
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("⏮ Вернуться", callback_data='call.approksimation.continue')
    button2 = types.InlineKeyboardButton("❌ Закончить", callback_data='call.end')
    markup.add(button1, button2) # Вывод для квадратичной
    bot.send_photo(message.chat.id, photo=buf, caption= \
                     f'🔹 a = {round(a, 6)} \n\n' \
                     f'🔹 b = {round(b, 6)}\n\n' \
                     f'🔹 c = {round(c, 6)}\n\n' \
                     f'🔸 <b>y = {round(a, 6)}x² {plus_app_b} {round(abs(b), 6)}x {plus_app_c} {round(abs(c), 6)}</b>',
                     parse_mode="html".format(message.from_user), reply_markup=markup)
    buf.close()
    del buf
    bot.callback_query_handler(func=function_second_1)
# ----Кубическая аппроксимация----
def cubic_approksimation(message):
    mas_x_3 = []
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        mas_x_3 = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return
    msg = bot.send_message(message.chat.id, text='Введите значения y, через пробел ')
    bot.register_next_step_handler(msg, start_of_appriksimation_y_3, mas_x_3)
# Считаем дальше для кубической
def start_of_appriksimation_y_3(message, mas_x_3):
    mas_y_3 = []
    try:
        pr = message.text.replace(',', '.')  # Принимаем строку и заменяем "," на "."
        mas_y_3 = [float(i) for i in pr.split(' ')]  # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return
    x = np.array(mas_x_3)
    y = np.array(mas_y_3)
    plus_app_b = '+'
    plus_app_c = '+'
    plus_app_d = '+'
    try:
        a, b, c, d = np.polyfit(x, y, 3)
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (число x должно совпадать с числом y)")
        return
    if b < 0: plus_app_b = '-'
    if c < 0: plus_app_c = '-'
    if d < 0: plus_app_d = '-'
    # Строим график
    plt.clf()  # Очищаем рисунок перед новой отрисовкой
    plt.scatter(x, y, color='blue', zorder=2)
    plt.plot(x, a * x ** 3 + b * x ** 2 + c * x + d, color='red')
    plt.title('График кубической аппроксимации')
    plt.xlabel('Значения x')
    plt.ylabel('Значения y')
    # включаем дополнительные отметки на осях
    plt.minorticks_on()
    # включаем основную сетку
    plt.grid(which='major', zorder=1)
    # включаем дополнительную сетку
    plt.grid(which='minor', linestyle=':', zorder=1)
    # Сохраняем график в файл
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("⏮ Вернуться", callback_data='call.approksimation.continue')
    button2 = types.InlineKeyboardButton("❌ Закончить", callback_data='call.end')
    markup.add(button1, button2) # Вывод кубической
    bot.send_photo(message.chat.id, photo=buf, caption= \
                     f'🔹 a = {round(a, 6)} \n\n' \
                     f'🔹 b = {round(b, 6)}\n\n' \
                     f'🔹 c = {round(c, 6)}\n\n' \
                     f'🔹 d = {round(d, 6)}\n\n' \
                     f'🔸 <b>y = {round(a, 6)}x³ {plus_app_b} {round(abs(b), 6)}x² {plus_app_c} {round(abs(c), 6)}x {plus_app_d} {round(abs(d), 6)}</b>',
                     parse_mode="html".format(message.from_user), reply_markup=markup)
    buf.close()
    del buf
    bot.callback_query_handler(func=function_second_1)

# -------------------Конец_расчета_аппроксицмации--------------------

# ----------------------------Погрешность----------------------------

def start_of_pogreshnost(message):
    mas = []
    try:
        pr = message.text.replace(',', '.')     # Принимаем строку и заменяем "," на "."
        mas = [float(i) for i in pr.split(' ')] # Преобразуем строку в массив
    except:
        bot.send_message(message.chat.id, "Ошибка чтения данных (значения вводить через один пробел)")
        return
    count = len(mas)
    sred = sum(mas)/count
    So = math.sqrt(sum([(x - sred) ** 2 for x in mas]) / (count*(count - 1)))
    # Стьюдент
    if count > 1 and count < 15:
        student = [None, None, 12.706204736432095, 4.302652729911275,  3.182446305284263,  2.7764451051977987, 2.5705818366147395, 2.4469118487916806, 2.3646242510102993, 2.3060041350333704, 2.2621571627409915, 2.2281388519649385, 2.200985160082949,  2.1788128296634177, 2.1603686564610127]
        msg = bot.send_message(message.chat.id, 'Введите погрешность вашего прибора: ')
        bot.register_next_step_handler(msg, pre_end, So, student[count], sred)
    # Если стьюдента нет в массиве
    else:
        msg = bot.send_message(message.chat.id, 'Введите коэффициент стьюдента: ')
        bot.register_next_step_handler(msg, student_not_auto, So, sred)
# Определение стьюдента пользователем
def student_not_auto(message, So, sred):
    try:
        student = float(message.text.replace(',', '.'))
    except:
        bot.send_message(message.chat.id, 'Ошибка чтения данных \n(коэффициент стьюдента вводится одним числом)')
        return
    msg = bot.send_message(message.chat.id, 'Введите погрешность вашего прибора: ')
    bot.register_next_step_handler(msg, pre_end, So, student, sred)
# Вывод конечного результата погрешностей
def pre_end(message, So, student, sred):
    infinity_student = 1.960

    try:
          device_pogresh = float(message.text.replace(',', '.'))
    except:
        bot.send_message(message.chat.id, 'Ошибка чтения данных \n(погрешность вводить одним числом)')
        return
    a_device = infinity_student * (device_pogresh / 3)
    a_random = student * So
    a_pogresh = pow((pow(a_random, 2) + pow(a_device, 2)), 0.5)
    otnosit_pogreshn = a_pogresh / sred
# Отправка конечного результата + выборка что делать дальше
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("🔁 Продолжить", callback_data='call.continue.pog')
    button2 = types.InlineKeyboardButton("❌ Закончить", callback_data='call.end')
    button3 = types.InlineKeyboardButton("⏮ Вернуться", callback_data='call.into_f_1_without_edit')
    markup.add(button1, button2)
    markup.add(button3)
    # Вывод
    bot.send_message(message.chat.id,  \
    f'1️⃣ Среднее значение: {round(sred,6)} \n\n' \
    f'2️⃣ Среднеквадратичное отклонение (S₀): {round(So, 6)}\n\n' \
    f'3️⃣ Случайная погрешность (Δa сл.): {round(a_random, 6)}\n\n' \
    f'4️⃣ Приборная погрешность (Δa пр.): {round(a_device, 6)}\n\n' \
    f'5️⃣ Общая погрешность (Δa): {round(a_pogresh, 6)}\n\n' \
    f'🔥 Окончательный результат: \n<b>({round(sred, 6)} ± {round(a_pogresh, 8)})</b>\n\n' \
    f'▪️ Коэффициент стьюдента (t): {round(student, 6)}\n' \
    f'▪️ Относительная погрешность (ε): {round(otnosit_pogreshn, 6)}', parse_mode="html".format(message.from_user), reply_markup=markup)

    bot.callback_query_handler(func=function_second_1) # В этом случае `func` является именованным аргументом и передается только один параметр

# ------------------------Конец_расчета_погрешностей------------------------

bot.infinity_polling()
