# 📁 products/urls.py - ИСПРАВЛЕННЫЕ URL с консистентными параметрами
# 🛍️ Все URL для товаров, категорий и функций каталога

from django.urls import path
from products.views import *
from . import views

urlpatterns = [
    # 🏠 Главная страница каталога
    path('', products_catalog, name='products_catalog'),

    # 📂 ИСПРАВЛЕНО: Категории товаров (консистентный параметр slug)
    path('category/<slug:slug>/', products_by_category, name='products_by_category'),

    # ❤️ Избранное
    path('wishlist/', wishlist_view, name='wishlist'),
    path('wishlist/add/<uid>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/move_to_cart/<uid>/', move_to_cart, name='move_to_cart'),
    path('wishlist/remove/<uid>/', remove_from_wishlist, name='remove_from_wishlist'),

    # 📝 Отзывы
    path('product-reviews/', product_reviews, name='product_reviews'),
    path('product-reviews/edit/<uuid:review_uid>/', views.edit_review, name='edit_review'),
    path('like-review/<review_uid>/', like_review, name='like_review'),
    path('dislike-review/<review_uid>/', dislike_review, name='dislike_review'),

    # 🛒 Корзина - ВАЖНО: добавляем выше паттерна со слагом
    path('add-to-cart/<uid>/', add_to_cart, name='add_to_cart'),

    # 🔍 Товар по слагу (должен быть В КОНЦЕ, чтобы не перехватывать другие URL)
    path('<slug>/', get_product, name='get_product'),
    path('<slug>/<review_uid>/delete/', delete_review, name='delete_review'),
]

# 🔧 ИСПРАВЛЕНИЯ:
# ✅ ИЗМЕНЕН: category_slug → slug для консистентности
# ✅ ПЕРЕМЕЩЕН: category/ выше <slug>/ для правильного маршрутизации
# ✅ ЛОГИКА: теперь /products/category/byd/ работает правильно
#
# 💡 URL СТРУКТУРА:
# /products/ → каталог всех товаров
# /products/category/byd/ → товары категории byd
# /products/some-product/ → конкретный товар
# /products/wishlist/ → избранное
#
# 🎯 РЕЗУЛЬТАТ:
# URL http://localhost:8000/products/category/byd/
# теперь попадет на products_by_category view
# и отобразит additional_content с YouTube!