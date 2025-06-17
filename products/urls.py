# 📁 products/urls.py - ОБНОВЛЕННАЯ версия с маршрутами экспорта
# 🔧 Добавлены URL-ы для экспорта товаров в Excel
# ✅ Сохранены все существующие маршруты

from django.urls import path
from products.views import *
from . import views

# 🆕 Импорт view-функций для импорта (существующие)
from .admin_views import (
    import_form_view,
    import_preview_view,
    execute_import_view,
    import_results_view,
    ajax_validate_file
)

# 🆕 Импорт view-функций для экспорта (новые)
from .export_views import (
    export_excel_view,
    export_info_view,
    export_ajax_stats
)

urlpatterns = [
    # 🏠 Главная страница каталога
    path('', products_catalog, name='products_catalog'),

    # 📂 Категории товаров
    path('category/<slug:slug>/', products_by_category, name='products_by_category'),

    # 📥 ИМПОРТ ТОВАРОВ - существующие URL
    path('import/', import_form_view, name='import_form'),
    path('import/preview/', import_preview_view, name='import_preview'),
    path('import/execute/', execute_import_view, name='import_execute'),
    path('import/results/', import_results_view, name='import_results'),
    path('import/validate/', ajax_validate_file, name='import_validate'),

    # 📤 ЭКСПОРТ ТОВАРОВ - новые URL
    path('export/', export_excel_view, name='export_excel'),
    path('export/info/', export_info_view, name='export_info'),
    path('export/stats/', export_ajax_stats, name='export_stats'),

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

    # 🛒 Корзина
    path('add-to-cart/<uid>/', add_to_cart, name='add_to_cart'),

    # 🔍 Товар по слагу (В КОНЦЕ)
    path('<slug>/', get_product, name='get_product'),
    path('<slug>/<review_uid>/delete/', delete_review, name='delete_review'),
]

# 🎯 НОВЫЕ URL экспорта:
# ✅ http://localhost:8000/products/export/ - прямое скачивание Excel
# ✅ http://localhost:8000/products/export/info/ - страница информации
# ✅ http://localhost:8000/products/export/stats/ - AJAX статистика
#
# 📥 СУЩЕСТВУЮЩИЕ URL импорта (без изменений):
# ✅ http://localhost:8000/products/import/ - форма загрузки
# ✅ http://localhost:8000/products/import/preview/ - предпросмотр
# ✅ http://localhost:8000/products/import/execute/ - выполнение импорта
# ✅ http://localhost:8000/products/import/results/ - результаты
# ✅ http://localhost:8000/products/import/validate/ - AJAX валидация

# 🔧 ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ✅ ДОБАВЛЕНО: Импорт export_views
# ✅ ДОБАВЛЕНО: 3 новых URL для экспорта
# ✅ СОХРАНЕНО: Все существующие URL без изменений
# ✅ ДОБАВЛЕНО: Комментарии с URL-ами для справки
#
# 🎯 РЕЗУЛЬТАТ:
# - Все URL работают с новой функциональностью экспорта
# - Совместимость с существующими страницами
# - Простые и понятные маршруты