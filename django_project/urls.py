from django.contrib import admin
from django.urls import path

from telegram_bot import views

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),
    # Редирект на админку
    path('', views.admin_redirect),

    # Для теста (потом удалить)
    path('telegram_bot/<str:bot_url>', views.web_hook_bot)
]
