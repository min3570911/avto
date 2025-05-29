# 📁 products/urls.py - ИСПРАВЛЕННЫЕ URL с каталогом товаров
# 🛍️ Добавлены отсутствующие URL для каталога и функций

from django.urls import path
from products.views import *
from . import views

urlpatterns = [
    # 🏠 ДОБАВЛЕНО: Главная страница каталога
    path('', products_catalog, name='products_catalog'),

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

    # 📂 ДОБАВЛЕНО: Каталог по категориям
    path('category/<slug:category_slug>/', products_by_category, name='products_by_category'),

    # 🔍 Товар по слагу (должен быть В КОНЦЕ, чтобы не перехватывать другие URL)
    path('<slug>/', get_product, name='get_product'),
    path('<slug>/<review_uid>/delete/', delete_review, name='delete_review'),
]

# 🔧 ИСПРАВЛЕНИЯ:
# ✅ ДОБАВЛЕН: path('', products_catalog) для /products/
# ✅ ДОБАВЛЕН: path('category/<slug:category_slug>/') для категорий
# ✅ ПЕРЕМЕЩЕН: <slug>/ в конец списка для правильного маршрутизации
# ✅ СОХРАНЕНЫ: все существующие URL без изменений