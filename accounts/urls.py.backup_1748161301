# 📁 accounts/urls.py - ФИНАЛЬНЫЕ УПРОЩЕННЫЕ URL-ы
# 🛍️ Только функции интернет-магазина (без регистрации пользователей)

from django.urls import path
from accounts.views import (
    cart,
    update_cart_item,
    remove_cart,
    remove_coupon,
    place_order,
    success,
    check_cart_item,
)

urlpatterns = [
    # 🛒 Корзина и покупки (анонимные)
    path('cart/', cart, name="cart"),
    path('update_cart_item/', update_cart_item, name='update_cart_item'),
    path('remove-cart/<uid>/', remove_cart, name="remove_cart"),
    path('remove-coupon/<cart_id>/', remove_coupon, name="remove_coupon"),
    path('check-cart-item/<str:product_id>/', check_cart_item, name="check_cart_item"),

    # 📦 Оформление заказа
    path('place-order/', place_order, name="place_order"),
    path('success/', success, name="success"),
    path('success/<str:order_id>/', success, name="success"),
]

# ℹ️ ПРИМЕЧАНИЯ:
#
# 🔐 Для входа в админку используется стандартный Django:
#     /admin/ - вход для администраторов
#
# 🗑️ УДАЛЕНО (не нужно):
# - login/ register/ logout/ - регистрация пользователей
# - activate/<email_token>/ - активация email
# - profile/<username>/ - профили пользователей
# - change-password/ - смена пароля
# - shipping-address/ - адреса доставки
# - password_reset/ - сброс пароля
# - order-history/ - история заказов
# - order-details/ - детали заказов
# - download/ - скачивание PDF
# - delete-account/ - удаление аккаунтов
#
# ✅ ВСЕ ЭТО ДОСТУПНО В СТАНДАРТНОЙ DJANGO АДМИНКЕ!