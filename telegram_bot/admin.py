from django.contrib import admin

from telegram_bot.models import *

admin.site.register(TelegramBot)
admin.site.register(TelegramUser)
admin.site.register(Subscription)
admin.site.register(Payment)
admin.site.register(RobokassaLogs)
