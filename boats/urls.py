# 📁 boats/urls.py - URL-маршруты для раздела "Лодки"

from django.urls import path
from . import views  # Мы создадим этот файл на следующем шаге

app_name = 'boats'

urlpatterns = [
    # 🛥️ Список всех категорий лодок (главная страница раздела)
    path('', views.boat_category_list, name='category_list'),

    # 🛥️ Список товаров в конкретной категории лодок
    path('category/<slug:slug>/', views.boat_product_list, name='product_list_by_category'),

    # 🛥️ Детальная страница товара-лодки
    path('product/<slug:slug>/', views.boat_product_detail, name='product_detail'),
]