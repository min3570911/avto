# 📁 home/urls.py - ИСПРАВЛЕННЫЕ URL без конфликта категорий
# 🏠 Главная страница и информационные страницы (БЕЗ категорий товаров)

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

    # 🗑️ УДАЛЕНО: path('category/<slug:slug>/', category_view, name='category'),
    # 📂 Категории товаров теперь обрабатываются в products/urls.py
]

# 🔧 ИСПРАВЛЕНИЯ:
# ❌ УБРАН: path('category/<slug:slug>/', category_view, name='category')
# ✅ ПРИЧИНА: конфликт с products/urls.py
# ✅ ЛОГИКА: home = информационные страницы, products = товары и категории
#
# 💡 РЕЗУЛЬТАТ:
# - /contact/, /about/ → home приложение
# - /category/*, /products/* → products приложение
# - Конфликт URL устранен