# 📁 boats/urls.py - ПОЛНЫЙ ФАЙЛ URL-маршрутов для раздела "Лодки"
# 🛥️ Все URL для каталога лодок, корзины и избранного
# ✅ ПРОВЕРЕНО: Структура URL скопирована с products/urls.py

from django.urls import path
from . import views

# 🛥️ Устанавливаем namespace для лодок
app_name = 'boats'

urlpatterns = [
    # 🏠 ОСНОВНЫЕ СТРАНИЦЫ ЛОДОК

    # 🛥️ Главная страница лодок (каталог всех лодок)
    path('', views.boat_category_list, name='category_list'),

    # 📂 Список товаров в конкретной категории лодок
    path('category/<slug:slug>/', views.boat_product_list, name='product_list_by_category'),

    # 📄 Детальная страница товара-лодки
    path('product/<slug:slug>/', views.boat_product_detail, name='product_detail'),

    # 🔍 ПОИСК ЛОДОК

    # 🔍 Поиск среди лодочных товаров
    path('search/', views.boat_search, name='search'),

    # 🛒 КОРЗИНА ДЛЯ ЛОДОК

    # 🛒 Добавление лодочного товара в корзину
    path('add-to-cart/<uid>/', views.boat_add_to_cart, name='add_to_cart'),

    # 🗑️ Удаление лодочного товара из корзины
    path('remove-from-cart/<uid>/', views.boat_remove_from_cart, name='remove_from_cart'),

    # 📊 Обновление количества лодочного товара в корзине
    path('update-cart/<uid>/', views.boat_update_cart_quantity, name='update_cart'),

    # ❤️ ИЗБРАННОЕ ДЛЯ ЛОДОК

    # ❤️ Добавление/удаление лодочного товара в/из избранного (toggle)
    path('add-to-wishlist/<uid>/', views.boat_add_to_wishlist, name='add_to_wishlist'),
]

# 🔧 СТРУКТУРА URL ДЛЯ ЛОДОК:
#
# 🏠 ОСНОВНЫЕ:
# /boats/ → главная страница лодок (все товары)
# /boats/category/yamaha/ → товары категории Yamaha
# /boats/product/lodka-kovrik-yamaha-350/ → детальная страница товара
# /boats/search/?q=коврик → поиск лодочных товаров
#
# 🛒 КОРЗИНА:
# /boats/add-to-cart/UUID/ → добавить в корзину
# /boats/remove-from-cart/UUID/ → удалить из корзины
# /boats/update-cart/UUID/ → обновить количество
#
# ❤️ ИЗБРАННОЕ:
# /boats/add-to-wishlist/UUID/ → добавить/удалить из избранного
#
# 📋 ОСОБЕННОСТИ:
# • app_name = 'boats' для namespace
# • Все URL используют slug для SEO
# • UID используется для операций с корзиной/избранным
# • Структура аналогична products/urls.py
# • Готовность к добавлению новых функций (фильтры, сравнение и т.д.)
#
# 🌐 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ В ШАБЛОНАХ:
# {% url 'boats:category_list' %} → /boats/
# {% url 'boats:product_list_by_category' 'yamaha' %} → /boats/category/yamaha/
# {% url 'boats:product_detail' product.slug %} → /boats/product/slug/
# {% url 'boats:add_to_cart' product.uid %} → /boats/add-to-cart/uuid/
# {% url 'boats:add_to_wishlist' product.uid %} → /boats/add-to-wishlist/uuid/