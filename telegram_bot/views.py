from django.shortcuts import render, redirect

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse

from telegram_bot.models import *
from telegram_bot.general_functions import *
from telegram_bot.robokassa_api import *

import requests
import telepot
import json
import random

from telegram_bot.tasks import *


# Редирект на админку
def admin_redirect(request):
    return redirect('/admin/')


# Для тестов (потом удалить).
# Функция для ловли сообщений
@csrf_exempt
def web_hook_bot(request, bot_url):
    telegram_bot = TelegramBot.objects.get(url=bot_url)

    try:
        if request.method == "POST":
            data = json.loads(request.body.decode('utf-8'))

            # Если пользователь нажал кнопку
            if 'callback_query' in data:
                chat_id = data['callback_query']['from']['id']
                chat_data = data['callback_query']['data']
                message_id = data['callback_query']['message']['message_id']

                bot_logic(telegram_bot.id, chat_id, chat_data, 'data', message_id)

            # Если пользователь написал что-то
            if 'message' in data:
                if 'text' in data['message'].keys():
                    chat_id = data['message']['chat']['id']
                    chat_msg = data['message']['text']
                    message_id = data['message']['message_id']

                    bot_logic(telegram_bot.id, chat_id, chat_msg, 'message', message_id)

            return HttpResponse('ok', content_type="text/plain", status=200)
        else:
            if bot_url == 'test':
                # Сохраняем URL
                telegram_bot.url = random_string(length=20)
                telegram_bot.save()

                # Удалить старый web hook для бота
                requests.get(f'https://api.telegram.org/bot{telegram_bot.token}/deleteWebhook')
                # Добавить web_hook для бота
                url_bot = f'https://clubbitchbot.ru/telegram_bot/{telegram_bot.url}'
                requests.get(f'https://api.telegram.org/bot{telegram_bot.token}/setWebhook?url={url_bot}')

            # Получаем информацию по веб хук
            req_text = requests.get(f'https://api.telegram.org/bot{telegram_bot.token}/getWebhookInfo').text

            return HttpResponse(req_text)
    except Exception:
        bug_trap()

        return HttpResponse('ok', content_type="text/plain", status=200)


@csrf_exempt
def robokassa_result(request):
    RobokassaLogs.objects.create(text=str(request.POST.dict()))
    return HttpResponse(result_payment(request))


# Логика для бота
def bot_logic(bot_id, chat_id, chat_result, type_message, message_id):
    # Получаем данные бота
    telegram_bot = TelegramBot.objects.get(id=bot_id)
    # Авторизируемся в telegram api
    bot = telepot.Bot(telegram_bot.token)

    try:
        # Если пользователь пишет в первый раз создаем профиль
        if TelegramUser.objects.filter(chat_id=chat_id, bot=telegram_bot).count() == 0:
            TelegramUser.objects.create(
                bot=telegram_bot,
                chat_id=chat_id
            )

        if TelegramUser.objects.filter(chat_id=chat_id, bot=telegram_bot).count() == 1:
            user = TelegramUser.objects.get(chat_id=chat_id, bot=telegram_bot)

            if chat_result == '/start':
                user.step = 'start'
                user.save()

                if user.subscription is not None:
                    bot_text = f'У вас активна подписка {user.subscription.name}'
                    keyboard = build_keyboard('reply', [{'Отменить подписку': 'Отменить подписку'}], True)
                    user.send_telegram_message(bot_text, keyboard)

            if chat_result == 'Отменить подписку':
                user.step = 'cancel_subscription'
                user.save()

                cancel_subscription(bot_id, chat_id, chat_result, type_message, message_id)
            # Приветственное сообщение
            elif user.step == 'start':
                start(bot_id, chat_id, chat_result, type_message, message_id)
            # Про клуб
            elif user.step == 'club_info':
                club_info(bot_id, chat_id, chat_result, type_message, message_id)
            # Про автора
            elif user.step == 'author_info':
                author_info(bot_id, chat_id, chat_result, type_message, message_id)
            # Цена вопроса
            elif user.step == 'issue_price':
                issue_price(bot_id, chat_id, chat_result, type_message, message_id)
            # Отмена подписки
            elif user.step == 'cancel_subscription':
                cancel_subscription(bot_id, chat_id, chat_result, type_message, message_id)
            else:
                user.send_telegram_message('Ошибка шага')
        else:
            bot.sendMessage(chat_id=chat_id, text='Ошибка пользователя')
    except Exception:
        bug_trap()


# Стартовое сообщение
def start(bot_id, chat_id, chat_result, type_message, message_id):
    try:
        # Получаем данные бота
        telegram_bot = TelegramBot.objects.get(id=bot_id)
        # Пользователь
        user = TelegramUser.objects.get(chat_id=chat_id, bot=telegram_bot)
        # Бот
        bot = telepot.Bot(telegram_bot.token)

        def message():
            bot_text = telegram_bot.start_message

            keyboard = build_keyboard('inline', [
                {'Про клуб "Бичфэйс"': 'step club_info'},
                {'Про автора': 'step author_info'},
                {'Цена вопроса': 'step issue_price'},
            ])

            user.send_telegram_message(bot_text, keyboard)

        if type_message == 'message':
            message()
        else:
            try:
                bot.deleteMessage((chat_id, message_id))
            except telepot.exception.TelegramError:
                pass

            if chat_result == 'step club_info':
                user.step = 'club_info'
                user.save()

                club_info(bot_id, chat_id, 'test', 'message', message_id)
            elif chat_result == 'step author_info':
                user.step = 'author_info'
                user.save()

                author_info(bot_id, chat_id, 'test', 'message', message_id)
            elif chat_result == 'step issue_price':
                user.step = 'issue_price'
                user.save()

                issue_price(bot_id, chat_id, 'test', 'message', message_id)
    except Exception:
        bug_trap()


# Про клуб
def club_info(bot_id, chat_id, chat_result, type_message, message_id):
    try:
        # Получаем данные бота
        telegram_bot = TelegramBot.objects.get(id=bot_id)
        # Пользователь
        user = TelegramUser.objects.get(chat_id=chat_id, bot=telegram_bot)
        # Бот
        bot = telepot.Bot(telegram_bot.token)

        def message():
            bot_text = telegram_bot.club_info_message

            keyboard = build_keyboard('inline', [{'Назад': 'step start'}])

            user.send_telegram_message(bot_text, keyboard)

        if type_message == 'message':
            message()
        else:
            try:
                bot.deleteMessage((chat_id, message_id))
            except telepot.exception.TelegramError:
                pass

            if chat_result == 'step start':
                user.step = 'start'
                user.save()

                start(bot_id, chat_id, 'test', 'message', message_id)
    except Exception:
        bug_trap()


# Про автора
def author_info(bot_id, chat_id, chat_result, type_message, message_id):
    try:
        # Получаем данные бота
        telegram_bot = TelegramBot.objects.get(id=bot_id)
        # Пользователь
        user = TelegramUser.objects.get(chat_id=chat_id, bot=telegram_bot)
        # Бот
        bot = telepot.Bot(telegram_bot.token)

        def message():
            bot_text = telegram_bot.author_info_message

            keyboard = build_keyboard('inline', [{'Назад': 'step start'}])

            user.send_telegram_message(bot_text, keyboard)

        if type_message == 'message':
            message()
        else:
            try:
                bot.deleteMessage((chat_id, message_id))
            except telepot.exception.TelegramError:
                pass

            if chat_result == 'step start':
                user.step = 'start'
                user.save()

                start(bot_id, chat_id, 'test', 'message', message_id)
    except Exception:
        bug_trap()


# Цена вопроса
def issue_price(bot_id, chat_id, chat_result, type_message, message_id):
    try:
        # Получаем данные бота
        telegram_bot = TelegramBot.objects.get(id=bot_id)
        # Пользователь
        user = TelegramUser.objects.get(chat_id=chat_id, bot=telegram_bot)
        # Бот
        bot = telepot.Bot(telegram_bot.token)

        def message():
            bot_text = telegram_bot.issue_price_message

            button_list = []

            for subscription in Subscription.objects.filter(active=True):
                button_list.append({subscription.name: f'step subscription {subscription.id}'})

            if user.subscription:
                bot_text2 = f'У вас активна подписка {user.subscription.name}'
                keyboard = build_keyboard('reply', [{'Отменить подписку': 'Отменить подписку'}], True)
                user.send_telegram_message(bot_text2, keyboard)

            button_list.append({'Назад': 'step start'})

            keyboard = build_keyboard('inline', button_list)

            user.send_telegram_message(bot_text, keyboard)

        # Успешная оплата
        def success_subscription():
            bot_text = 'Подписка успешно оплачена'
            keyboard = build_keyboard('reply', [{'Отменить подписку': 'Отменить подписку'}], True)
            user.send_telegram_message(bot_text, keyboard)

            bot_text = 'Теперь можете вернутся на главную страницу'
            keyboard = build_keyboard('inline', [{'Главная': 'step start'}])
            user.send_telegram_message(bot_text, keyboard)

        if type_message == 'message':
            message()
        else:
            try:
                bot.deleteMessage((chat_id, message_id))
            except telepot.exception.TelegramError:
                pass

            if chat_result == 'step start':
                user.step = 'start'
                user.save()

                start(bot_id, chat_id, 'test', 'message', message_id)
            elif chat_result == 'step subscription':
                message()
            elif 'step subscription' in chat_result:
                subscription = Subscription.objects.get(id=chat_result.split(' ')[2])

                invoice_number = telegram_bot.invoice_number + 1
                telegram_bot.invoice_number += 1
                telegram_bot.save()

                payment = Payment.objects.create(
                    subscription=subscription,
                    user=user,
                    invoice_number=invoice_number,
                )

                payment_url = generate_payment_link(
                    payment.user.bot.id_shop,
                    payment.user.bot.password_shop_1,
                    payment.subscription.price,
                    payment.invoice_number,
                    payment.subscription.description)

                bot_text = telegram_bot.title_payment
                keyboard = build_keyboard('inline', [
                    {'Оплатить': f'this_url{payment_url}'},
                    {'Отменить': f'step subscription'},
                ], True)

                bot.sendDocument(user.chat_id, telegram_bot.doc_1)
                bot.sendDocument(user.chat_id, telegram_bot.doc_2)

                user.send_telegram_message(bot_text, keyboard)
    except Exception:
        bug_trap()


# Отмена подписки
def cancel_subscription(bot_id, chat_id, chat_result, type_message, message_id):
    try:
        # Получаем данные бота
        telegram_bot = TelegramBot.objects.get(id=bot_id)
        # Пользователь
        user = TelegramUser.objects.get(chat_id=chat_id, bot=telegram_bot)
        # Бот
        bot = telepot.Bot(telegram_bot.token)

        def message():
            bot_text = f"У вас есть активная подписка {user.subscription.name}\nОтменить ее?"

            keyboard = build_keyboard('inline', [{'Да': 'step cancel_subscription', 'Нет': 'step start'}])
            user.send_telegram_message(bot_text, keyboard)

        if type_message == 'message':
            message()
        else:
            try:
                bot.deleteMessage((chat_id, message_id))
            except telepot.exception.TelegramError:
                pass

            if chat_result == 'step start':
                user.step = 'start'
                user.save()

                start(bot_id, chat_id, 'test', 'message', message_id)
            elif 'step cancel_subscription' in chat_result:
                user.step = 'start'
                user.auto_payment = False
                user.save()

                bot_text = telegram_bot.end_cancel_text
                user.send_telegram_message(bot_text)

                start(bot_id, chat_id, 'test', 'message', message_id)
    except Exception:
        bug_trap()
