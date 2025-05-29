# 📁 products/urls.py
# 🛍️ URL-маршруты для товаров, отзывов и функционала магазина

from django.urls import path
from . import views

urlpatterns = [
    # 🛍️ Основные страницы товаров
    path('', views.products_catalog, name='products_catalog'),
    path('product/<slug:slug>/', views.get_product, name='get_product'),
    path('category/<slug:slug>/', views.products_by_category, name='products_by_category'),

    # ❤️ Избранное
    path('add-to-wishlist/<product_uid>/', views.add_to_wishlist, name="add_to_wishlist"),
    path('remove-from-wishlist/<product_uid>/', views.remove_from_wishlist, name="remove_from_wishlist"),
    path('move-to-cart/<product_uid>/', views.move_to_cart, name="move_to_cart"),
    path('wishlist/', views.wishlist, name="wishlist"),

    # 🛒 Корзина
    path('add-to-cart/<product_uid>/', views.add_to_cart, name="add_to_cart"),
    path('remove-cart/<cart_item_uid>/', views.remove_cart, name="remove_cart"),
    path('cart/', views.cart, name="cart"),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),

    # 📝 НОВЫЕ МАРШРУТЫ: Отзывы о товарах
    path('product-reviews/', views.product_reviews, name='product_reviews'),
    path('product-reviews/edit/<uuid:review_id>/', views.edit_review, name='edit_review'),
    path('product-reviews/delete/<slug:product_slug>/<uuid:review_id>/', views.delete_review, name='delete_review'),

    # 👍 Лайки/дизлайки отзывов
    path('review/like/<uuid:review_id>/', views.toggle_like_review, name='toggle_like_review'),
    path('review/dislike/<uuid:review_id>/', views.toggle_dislike_review, name='toggle_dislike_review'),
]

# 📝 КОММЕНТАРИИ К МАРШРУТАМ:
# ✅ Основные товары: каталог, детальная страница, по категориям
# ✅ Избранное: добавление, удаление, перенос в корзину, просмотр списка
# ✅ Корзина: добавление, удаление, просмотр, обновление количества
# ✅ ИСПРАВЛЕНО: Добавлены все необходимые маршруты для отзывов
# ✅ ИСПРАВЛЕНО: Добавлены маршруты для лайков/дизлайков