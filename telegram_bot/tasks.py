from celery import shared_task
from celery import Celery

from datetime import timedelta

import telepot
import telebot
import datetime

from telegram_bot.models import TelegramBot, TelegramUser

app = Celery()


@app.task
def subscriptions():
    bot_settings = TelegramBot.objects.filter().first()
    bot = telepot.Bot(bot_settings.token)

    bot.sendMessage(chat_id='673616491', text='tes55t')


@app.task
def accept_users():
    bot_settings = TelegramBot.objects.filter().first()
    bot = telebot.TeleBot(bot_settings.token)

    # Выбрать пользователей, которые оплатили подписку
    users = TelegramUser.objects.exclude(subscription=None).filter(subscription__active=True)

    # Пытаемся добавить этих пользователей в группу
    for user in users:
        try:
            bot.approve_chat_join_request(bot_settings.chat_id, user.chat_id)
        except Exception as e:
            pass


@app.task
def remove_users():
    bot_settings = TelegramBot.objects.filter().first()
    bot = telebot.TeleBot(bot_settings.token)

    # Выбрать пользователей у которых закончилась подписка
    users = TelegramUser.objects.excude(subscription=None).filter(subscription__active=False)

    # Пытаемся удалить этих пользователей из группы
    for user in users:
        try:
            bot.ban_chat_member(bot_settings.chat_id, user.chat_id)
            bot.unban_chat_member(bot_settings.chat_id, user.chat_id)
        except Exception as e:
            pass
