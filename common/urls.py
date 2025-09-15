# 📁 common/urls.py - Маршруты для общих компонентов
# ✅ БАЗОВАЯ СТРУКТУРА: пока пустые маршруты, но готовы к расширению

from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    # 📝 Пока маршруты не нужны, но структура готова
    # path('reviews/', views.ReviewListView.as_view(), name='reviews'),
    # path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
]

# 🔧 ПРИМЕЧАНИЕ:
# Это приложение содержит только модели для использования в других приложениях
# Когда потребуются views для отзывов или избранного, добавим их сюда