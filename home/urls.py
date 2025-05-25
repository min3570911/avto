# 📁 home/urls.py - ПОЛНЫЕ URL для home приложения
# 🏠 Главная страница и страницы сайта

from django.urls import path
from home.views import *

urlpatterns = [
    # 🏠 Главная страница
    path('', index, name="index"),

    # 🔍 Поиск товаров
    path('search/', product_search, name='product_search'),

    # 📞 Информационные страницы
    path('contact/', contact, name='contact'),
    path('about/', about, name='about'),
    path('terms-and-conditions/', terms_and_conditions, name='terms-and-conditions'),
    path('privacy-policy/', privacy_policy, name='privacy-policy'),

    # 📂 Категории товаров
    path('category/<slug:slug>/', category_view, name='category'),
]

# 🔧 ИСПРАВЛЕНИЯ:
# ✅ ПРОВЕРЕН: path('', index) для главной страницы
# ✅ ДОБАВЛЕН: маршрут для категорий (если отсутствовал)
# ✅ СОХРАНЕНЫ: все существующие URL-маршруты
# ✅ ПОДТВЕРЖДЕНА: правильная структура home приложения