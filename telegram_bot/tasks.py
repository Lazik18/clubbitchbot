from celery import shared_task

from datetime import timedelta

import telepot
import datetime

from telegram_bot.models import TelegramBot


@shared_task
def subscriptions():
    bot_settings = TelegramBot.objects.filter().first()
    bot = telepot.Bot(bot_settings.token)

    bot.sendMessage(chat_id='673616491', text='tes55t')
