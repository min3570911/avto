# 📁 cars/urls.py - URL-маршруты для раздела "Автомобили"

from django.urls import path
from . import views

app_name = 'cars'

urlpatterns = [
    # 🚗 Список всех категорий автомобилей (главная страница раздела)
    path('', views.car_category_list, name='category_list'),

    # 🚗 Список товаров в конкретной категории автомобилей
    path('category/<slug:slug>/', views.car_product_list, name='product_list_by_category'),

    # 🚗 Детальная страница товара-автомобиля
    path('product/<slug:slug>/', views.car_product_detail, name='product_detail'),

    # 🛒 Добавление в корзину (специальная версия для авто)
    path('add-to-cart/<uid>/', views.car_add_to_cart, name='add_to_cart'),

    # ❤️ Добавление в избранное (специальная версия для авто)
    path('add-to-wishlist/<uid>/', views.car_add_to_wishlist, name='add_to_wishlist'),

    # 🔍 Поиск среди автомобилей
    path('search/', views.car_search, name='search'),

    # 🔧 Конфигуратор ковриков (только для автомобилей)
    path('configurator/', views.car_configurator, name='configurator'),
]