from django.contrib import admin
from django.urls import path

from telegram_bot import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.admin_redirect),
    path('telegram_bot/<str:bot_url>', views.web_hook_bot),
    path('robokassaresult/', views.robokassa_result)
]
