import datetime

import requests

import decimal
import hashlib
import json
import xmltodict
import telepot

from urllib import parse
from urllib.parse import urlparse

from telegram_bot.models import TelegramBot, Payment, TelegramUser


# Создание подписи
def calculate_signature(*args) -> str:
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


# Формирование URL переадресации пользователя на оплату.
def generate_payment_link(
    merchant_login: str,  # Логин магазина
    merchant_password_1: str,  # Пароль магазина
    cost: decimal,  # Цена
    number,  # Номер заказа
    description: str,  # Описание заказа
) -> str:
    # Генерация подписи (signature)
    signature = calculate_signature(
        merchant_login,
        cost,
        number,
        merchant_password_1
    )

    robokassa_payment_url = 'https://auth.robokassa.ru/Merchant/Index.aspx'

    data = {
        'MerchantLogin': merchant_login,
        'OutSum': cost,
        'InvId': number,
        'Description': description,
        'SignatureValue': signature,
        'Recurring': "true"
    }
    return f'{robokassa_payment_url}?{parse.urlencode(data)}'


# Получаем результат оплаты
def result_payment2(
    merchant_login: str,  # Логин магазина
    merchant_password_2: str,  # Пароль магазина
    number,  # Номер заказа
) -> bool:
    # Адрес для получения результата
    url = 'https://auth.robokassa.ru/Merchant/WebService/Service.asmx/OpStateExt'

    # Генерируем цифровую подпись
    signature = calculate_signature(
        merchant_login,
        number,
        merchant_password_2
    )

    # Параметры для запроса
    params = {
        'MerchantLogin': merchant_login,
        'InvoiceID': number,
        'Signature': signature,
    }

    # Отправляем запрос на проверку платежа
    result = requests.get(f'{url}?{parse.urlencode(params)}')

    # Конверт
    data_xml = xmltodict.parse(result.content.decode('utf-8'))
    data_json = json.dumps(data_xml)
    data_dict = json.loads(data_json)

    try:
        if data_dict.get('OperationStateResponse').get('State').get('Code') == '100':
            return True
        else:
            return False
    except Exception:
        return False


def result_payment(request):
    param_request = request.POST.dict()
    cost = param_request['OutSum']
    number = param_request['InvId']
    signature = param_request['SignatureValue']

    bot_settings = TelegramBot.objects.filter().first()

    new_signature = calculate_signature(cost, number, bot_settings.password_shop_2)

    if signature.lower() == new_signature.lower():
        payment = Payment.objects.filter(invoice_number=int(number)).first()
        payment.status = True
        payment.save()
        user = payment.user
        user.subscription = payment.subscription
        user.date_sub = datetime.datetime.now()
        user.previous_invoice_id = number
        user.save()
        return 'OK{}'.format(number)
    else:
        return 'bad sign'


def recurring_payment(user_pk):
    url = 'https://auth.robokassa.ru/Merchant/Recurring'
    bot_settings = TelegramBot.objects.filter().first()
    user = TelegramUser.objects.get(pk=user_pk)

    invoice_number = bot_settings.invoice_number + 1
    bot_settings.invoice_number += 1
    bot_settings.save()

    payment = Payment.objects.create(
        subscription=user.subscription,
        user=user,
        invoice_number=invoice_number,
    )

    signature = calculate_signature(
        bot_settings.id_shop,
        payment.subscription.price,
        invoice_number,
        bot_settings.password_shop_1
    )

    data = {"MerchantLogin": f"{bot_settings.id_shop}",
            "InvoiceID": f"{invoice_number}",
            "PreviousInvoiceID": f"{user.previous_invoice_id}",
            "Description": f"{payment.subscription.description}",
            "SignatureValue": f"{signature}",
            "OutSum": f"{payment.subscription.price}"}

    return requests.post(url, data)
