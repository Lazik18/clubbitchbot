from celery import shared_task

from telegram_bot.general_functions import *
from telegram_bot.models import *

from datetime import timedelta

import telepot
import datetime


# Проверяем оплаченный чек
@shared_task
def check_payment():
    try:
        date_start = datetime.datetime.now() - timedelta(hours=1)

        for payment in Payment.objects.filter(date__gte=date_start, status=False):
            if payment.get_payment_statys():
                bot_text = payment.user.bot.cancel_text
                keyboard = build_keyboard('reply', [{'Отменить подписку': 'Отменить подписку'}], True)
                payment.user.send_telegram_message(bot_text, keyboard)

                bot_text = payment.user.bot.success_payment
                keyboard = build_keyboard('inline', [
                    {'Вступить': f'this_url{payment.user.bot.create_chat_link()}'},
                ], True)

                payment.user.send_telegram_message(bot_text, keyboard)

                payment.status = True
                payment.save()

                payment.user.subscription = payment.subscription
                payment.user.save()
    except Exception as e:
        bug_trap()


# Ищем подписки которые нужно оплатить
@shared_task
def subscriptions_payment():
    try:
        # Дата для оплаты
        date_start = datetime.datetime.now() - timedelta(days=30)

        for payment in Payment.objects.filter(date__lte=date_start, status=True):
            bot = telepot.Bot('5543379327:AAGEVtTh-buSk6qPvCMWXIJBk2kqOZaAguQ')
            # Делаем заголовок
            bot_text = f'Сообщения для Ильи\n\n{payment.id}'
            # Отправить сообщение Илье
            bot.sendMessage(chat_id='673616491', text=bot_text)
    except Exception as e:
        bug_trap()
