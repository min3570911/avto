# 📁 cars/urls.py - URL-маршруты для раздела "Автомобили"

from django.urls import path
from . import views  # Мы создадим этот файл на следующих шагах

app_name = 'cars'

urlpatterns = [
    # 🚗 Список всех категорий автомобилей (главная страница раздела)
    path('', views.car_category_list, name='category_list'),

    # 🚗 Список товаров в конкретной категории автомобилей
    path('category/<slug:slug>/', views.car_product_list, name='product_list_by_category'),

    # 🚗 Детальная страница товара-автомобиля
    path('product/<slug:slug>/', views.car_product_detail, name='product_detail'),
]