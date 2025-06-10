# 📁 products/urls.py - ОБНОВЛЕННЫЕ URL с системой импорта
# 🛍️ Все URL для товаров, категорий и функций каталога + импорт

from django.urls import path
from products.views import *
from products import admin_views  # 🆕 Импорт view-функций для админки
from . import views

# 🏷️ Указываем namespace для URL
app_name = 'products'

urlpatterns = [
    # 🏠 Главная страница каталога
    path('', products_catalog, name='products_catalog'),

    # 📂 Категории товаров
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

    # 🆕 СИСТЕМА ИМПОРТА - URL для админки
    path('admin/import/', admin_views.import_products_view, name='import_products'),
    path('admin/import/preview/<str:session_key>/', admin_views.import_preview_view, name='import_preview'),
    path('admin/import/process/<str:session_key>/', admin_views.import_process_view, name='import_process'),
    path('admin/import/results/<str:session_key>/', admin_views.import_results_view, name='import_results'),
    path('admin/import/progress/<str:session_key>/', admin_views.import_progress_ajax, name='import_progress'),
    path('admin/download-template/', admin_views.download_template_view, name='download_template'),

    # 🔍 Товар по слагу (должен быть В КОНЦЕ, чтобы не перехватывать другие URL)
    path('<slug>/', get_product, name='get_product'),
    path('<slug>/<review_uid>/delete/', delete_review, name='delete_review'),
]

# 🔧 СТРУКТУРА URL:
# /products/ → каталог всех товаров
# /products/category/byd/ → товары категории byd
# /products/some-product/ → конкретный товар
# /products/wishlist/ → избранное
# /products/admin/import/ → система импорта (только для админов)
# /products/admin/download-template/ → скачивание шаблонов
#
# 🆕 НОВЫЕ URL ДЛЯ ИМПОРТА:
# /products/admin/import/ → форма загрузки файла
# /products/admin/import/preview/<session_key>/ → предпросмотр данных
# /products/admin/import/process/<session_key>/ → обработка импорта
# /products/admin/import/results/<session_key>/ → результаты импорта
# /products/admin/import/progress/<session_key>/ → AJAX прогресс (для будущего)
# /products/admin/download-template/ → скачивание шаблонов Excel