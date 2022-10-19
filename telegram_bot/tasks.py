from celery import shared_task

from datetime import timedelta

import telepot
import datetime

from telegram_bot.models import TelegramBot


@shared_task
def subscriptions_payment():
    # Получаем данные бота
    bot_settings = TelegramBot.objects.filter().first()
    # Авторизируемся в telegram api
    bot = telepot.Bot(bot_settings.token)

    bot.sendMessage(chat_id='673616491', text='test')
