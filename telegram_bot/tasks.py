from celery import shared_task
from datetime import timedelta

import telepot
import datetime
import requests

from telegram_bot.models import TelegramBot, TelegramUser


@shared_task
def subscriptions():
    bot_settings = TelegramBot.objects.filter().first()
    bot = telepot.Bot(bot_settings.token)

    bot.sendMessage(chat_id='673616491', text='tes5512356t')
    return True


@shared_task
def accept_users():
    bot_settings = TelegramBot.objects.filter().first()
    bot = telepot.Bot(bot_settings.token)

    # Выбрать пользователей, которые оплатили подписку
    users = TelegramUser.objects.exclude(subscription=None)

    # Пытаемся добавить этих пользователей в группу
    for user in users:
        try:
            requests.get(f'https://api.telegram.org/bot{bot_settings.token}/approveChatJoinRequest?chat_id={bot_settings.chat_id}&user_id={user.chat_id}')
        except Exception as e:
            bot.sendMessage(chat_id='673616491', text=f'{e}')
    return True


@shared_task
def remove_users():
    bot_settings = TelegramBot.objects.filter().first()
    bot = telepot.Bot(bot_settings.token)

    # Выбрать пользователей у которых закончилась подписка
    users = TelegramUser.objects.filter(subscription=None)

    # Пытаемся удалить этих пользователей из группы
    for user in users:
        try:
            requests.get(f'https://api.telegram.org/bot{bot_settings.token}/banChatMember?chat_id={bot_settings.chat_id}&user_id={user.chat_id}')
            requests.get(f'https://api.telegram.org/bot{bot_settings.token}/unbanChatMember?chat_id={bot_settings.chat_id}&user_id={user.chat_id}')
        except Exception as e:
            bot.sendMessage(chat_id='673616491', text=f'{e}')
    return True
