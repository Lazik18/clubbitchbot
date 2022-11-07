from celery import shared_task
from datetime import timedelta

import telepot
import datetime
import requests

from telegram_bot.models import TelegramBot, TelegramUser
from telegram_bot.robokassa_api import recurring_payment


@shared_task
def subscriptions():
    bot_settings = TelegramBot.objects.filter().first()
    bot = telepot.Bot(bot_settings.token)

    users = TelegramUser.objects.exclude(subscription=None)

    for user in users:
        try:
            if user.date_sub < (datetime.datetime.now(tz=datetime.timezone.utc) - timedelta(days=30)):
                bot.sendMessage(chat_id=user.chat_id, text=bot_settings.end_subscribe_payment)
                user.date_sub = None
                user.subscription = None
                user.previous_invoice_id = None
                user.save()
            elif user.date_sub < (datetime.datetime.now(tz=datetime.timezone.utc) - timedelta(days=29, hours=23, minutes=30)):
                if user.auto_payment:
                    recurring_payment(user.pk)
                else:
                    bot.sendMessage(chat_id=user.chat_id, text=bot_settings.end_subscribe_cancel)
                    user.date_sub = None
                    user.subscription = None
                    user.previous_invoice_id = None
                    user.save()

        except Exception as e:
            pass
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
            if user.subscription.chat:
                requests.get(f'https://api.telegram.org/bot{bot_settings.token}/approveChatJoinRequest?chat_id={bot_settings.chat_id}&user_id={user.chat_id}')
            if user.subscription.chanel:
                requests.get(f'https://api.telegram.org/bot{bot_settings.token}/approveChatJoinRequest?chat_id={bot_settings.chanel_id}&user_id={user.chat_id}')
        except Exception as e:
            pass
    return True


@shared_task
def remove_users():
    bot_settings = TelegramBot.objects.filter().first()
    bot = telepot.Bot(bot_settings.token)

    # Выбрать пользователей у которых закончилась подписка
    users = TelegramUser.objects.filter(subscription=None)

    # Пытаемся удалить этих пользователей
    for user in users:
        try:
            requests.get(f'https://api.telegram.org/bot{bot_settings.token}/banChatMember?chat_id={bot_settings.chat_id}&user_id={user.chat_id}')
            requests.get(f'https://api.telegram.org/bot{bot_settings.token}/unbanChatMember?chat_id={bot_settings.chat_id}&user_id={user.chat_id}')
            requests.get(f'https://api.telegram.org/bot{bot_settings.token}/banChatMember?chat_id={bot_settings.chanel_id}&user_id={user.chat_id}')
            requests.get(f'https://api.telegram.org/bot{bot_settings.token}/unbanChatMember?chat_id={bot_settings.chanel_id}&user_id={user.chat_id}')
        except Exception as e:
            pass
    return True
