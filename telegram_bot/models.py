from urllib import parse

import requests
from django.db import models

import telepot
import json

from telepot.exception import BotWasBlockedError


# Подписки
class Subscription(models.Model):
    # Название
    name = models.TextField(verbose_name='Название')
    # Цена
    price = models.FloatField(default=0, verbose_name='Цена')
    # Активность
    active = models.BooleanField(default=True, verbose_name='Активность')
    # Описание при оплате
    description = models.TextField(default='Описание', verbose_name='Описание при оплате')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Настройки подписки"
        verbose_name_plural = "Настройки подписок"


# Для тестов
class TelegramBot(models.Model):
    # Ссылка на бота
    link = models.TextField(blank=True, null=True, verbose_name='Ссылка на бота')
    # URL для бота
    url = models.TextField(verbose_name='URL для бота')
    # Токен бота
    token = models.TextField(verbose_name='Токен бота')

    # Приветственное сообщение
    start_message = models.TextField(verbose_name='Приветственное сообщение')
    # Про клуб
    club_info_message = models.TextField(verbose_name='Про клуб')
    # Про автора
    author_info_message = models.TextField(verbose_name='Про автора')
    # Цена вопроса
    issue_price_message = models.TextField(verbose_name='Цена вопроса')
    # Заголовок со ссылкой на оплату
    title_payment = models.TextField(verbose_name='Заголовок с ссылкой на оплату', default='Оплата')
    # Успешная оплата
    success_payment = models.TextField(verbose_name='Успешная оплата', default='Оплата')
    # Текст с кнопкой отмены
    cancel_text = models.TextField(verbose_name='Текст с кнопкой отмены', default='Оплата')
    # Текст итоговой отмены
    end_cancel_text = models.TextField(verbose_name='Текст итоговой отмены', default='Оплата')

    # Оферта
    doc_1 = models.FileField(upload_to='static/file', blank=True, null=True, verbose_name='Оферта')
    # Политика персональных данных
    doc_2 = models.FileField(upload_to='static/file', blank=True, null=True, verbose_name='Политика персональных данных')

    # ID магазина из ЛК Robokassa
    id_shop = models.TextField(default='test', verbose_name='ID магазина из ЛК Robokassa')
    # Пароль #1
    password_shop_1 = models.TextField(default='test', verbose_name='Пароль #1')
    # Пароль #2
    password_shop_2 = models.TextField(default='test', verbose_name='Пароль #2')

    # id группы
    chat_id = models.TextField(default='123', blank=True, null=True)

    # Отправить сообщение ботом
    def send_telegram_message(self, chat_id, text, keyboard=None, parse_mode=None):
        bot = telepot.Bot(self.token)

        # Проверяем нужно ли отправить клавиатуру
        if keyboard is None:
            # Отправляем сообщение через бот
            try:
                bot.sendMessage(chat_id=chat_id, text=text, parse_mode=parse_mode)
            except BotWasBlockedError:
                pass
        else:
            # Отправляем сообщение через бот
            try:
                bot.sendMessage(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode=parse_mode)
            except BotWasBlockedError:
                pass

    # Создать ссылку на приглашение
    def create_chat_link(self):
        link = f'https://api.telegram.org/bot{self.token}/createChatInviteLink'

        params = {
            'chat_id': self.chat_id,
            'member_limit': 1
        }

        return json.loads(requests.post(f'{link}?{parse.urlencode(params)}').text).get('result').get('invite_link')

    def __str__(self):
        return self.link

    class Meta:
        verbose_name = "Настройки бота"
        verbose_name_plural = "Настройки бота"


# Пользователи
class TelegramUser(models.Model):
    # Бот
    bot = models.ForeignKey(TelegramBot, on_delete=models.CASCADE, verbose_name='Бот')
    # id
    chat_id = models.TextField(verbose_name='Чат ID')
    # Текущий шаг
    step = models.TextField(default='start', verbose_name='Текущий шаг')
    # Текущая подписка
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, default=None, blank=True, null=True)

    # Отправляем сообщение
    # Отправить пользователю сообщение
    def send_telegram_message(self, text, keyboard=None, parse_mode=None):
        if keyboard is None:
            self.bot.send_telegram_message(self.chat_id, text, parse_mode=parse_mode)
        else:
            self.bot.send_telegram_message(self.chat_id, text, keyboard, parse_mode=parse_mode)

    def __str__(self):
        return self.chat_id

    class Meta:
        verbose_name = "Пользователь бота"
        verbose_name_plural = "Пользователи бота"


# Квитация оплаты
class Payment(models.Model):
    # Дата создания
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    # Подписка
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    # Пользователь
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    # Номер счета
    invoice_number = models.IntegerField()
    # Статус
    status = models.BooleanField(default=False)
    # Предупреждение о следующей оплате
    warning_new_payment = models.BooleanField(default=False)
    # Попыток провести оплату
    attempt = models.IntegerField(default=0)

    # Получить ссылку на оплату
    # def get_payment_link(self):
    #     return generate_payment_link(
    #         self.user.bot.id_shop,
    #         self.user.bot.password_shop_1,
    #         self.subscription.price,
    #         self.invoice_number,
    #         self.subscription.description
    #     )

    # Проверяем оплату
    def get_payment_statys(self):
        pass

    def __str__(self):
        return f'{self.date} {self.invoice_number} {self.subscription} {self.user}'

    class Meta:
        verbose_name = "Квитантция на оплату"
        verbose_name_plural = "Квитантции на оплату"
