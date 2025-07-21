# 📁 boats/urls.py - ОБНОВЛЕННЫЕ URL-маршруты для раздела "Лодки"

from django.urls import path
from . import views

app_name = 'boats'

urlpatterns = [
    # 🛥️ Список всех категорий лодок (главная страница раздела)
    path('', views.boat_category_list, name='category_list'),

    # 🛥️ Список товаров в конкретной категории лодок
    path('category/<slug:slug>/', views.boat_product_list, name='product_list_by_category'),

    # 🛥️ Детальная страница товара-лодки
    path('product/<slug:slug>/', views.boat_product_detail, name='product_detail'),

    # 🛒 Добавление в корзину (специальная версия для лодок)
    path('add-to-cart/<uid>/', views.boat_add_to_cart, name='add_to_cart'),

    # ❤️ Добавление в избранное (специальная версия для лодок)
    path('add-to-wishlist/<uid>/', views.boat_add_to_wishlist, name='add_to_wishlist'),

    # 🔍 Поиск среди лодок
    path('search/', views.boat_search, name='search'),
]