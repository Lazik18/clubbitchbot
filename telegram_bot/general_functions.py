from telepot.namedtuple import KeyboardButton
from telepot.namedtuple import ReplyKeyboardMarkup
from telepot.namedtuple import InlineKeyboardButton
from telepot.namedtuple import InlineKeyboardMarkup

import telepot
import random
import string
import sys
import os


# Создание рандомной строки
def random_string(length=10, numbers=True, letters=True):
    options_string = ''

    if numbers:
        options_string += '0123456789'

    if letters:
        options_string += string.ascii_lowercase

    return ''.join(random.choice(options_string) for i in range(length))


# Ловушка ошибок
def bug_trap(type_output='telegram', additional_parameter=None):
    exc_type = sys.exc_info()[0]
    exc_tb = sys.exc_info()[2]
    file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

    text_error = f'Тип ошибки: {exc_type}\nПуть:\n     {file_name}({exc_tb.tb_lineno})'

    while exc_tb.tb_next is not None:
        exc_tb = exc_tb.tb_next
        file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        text_error += f' -> \n     {file_name}({exc_tb.tb_lineno})'

    # Добавляем доп параметр
    if additional_parameter is not None:
        text_error += f'\n\nДоп парметр: {additional_parameter}'

    if type_output == 'console':
        print(text_error)
    elif type_output == 'telegram':
        # Авторизируемся в боте
        bot = telepot.Bot('5543379327:AAGEVtTh-buSk6qPvCMWXIJBk2kqOZaAguQ')

        # Делаем заголовок
        bot_text = f'Сообщения для Ильи\n\n{text_error}'

        # Отправить сообщение Илье
        bot.sendMessage(chat_id='673616491', text=bot_text)


# Сборщиик клавиатуры
# Тип клавиатуры:
# reply - Кнопки под чатом
# inline - Кнопки под сообщением
# Нужно еще будет добавить исчезнование клавиатуры
def build_keyboard(type_keyboard, keyboard_list, one_time=False):
    try:
        keyboard_button = []

        if type_keyboard == 'inline':
            for keyboard in keyboard_list:
                keyboard_line = []

                for key, value in keyboard.items():
                    if 'this_url' in value:
                        keyboard_line.append(InlineKeyboardButton(text=key, url=value.replace('this_url', '')))
                    else:
                        keyboard_line.append(InlineKeyboardButton(text=key, callback_data=value))

                keyboard_button.append(keyboard_line)

            return InlineKeyboardMarkup(inline_keyboard=keyboard_button)
        elif type_keyboard == 'reply':
            for keyboard in keyboard_list:
                keyboard_line = []

                for key, value in keyboard.items():
                    keyboard_line.append(KeyboardButton(text=key))

                keyboard_button.append(keyboard_line)

            return ReplyKeyboardMarkup(keyboard=keyboard_button, resize_keyboard=True, one_time_keyboard=one_time)
        else:
            return None
    except Exception:
        bug_trap()
