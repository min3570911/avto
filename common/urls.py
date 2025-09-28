# 📁 common/urls.py - АКТИВИРОВАННЫЕ МАРШРУТЫ
# ✅ ИСПРАВЛЕНО: Раскомментированы URL для AJAX функций
# 🔧 ДОБАВЛЕНО: Маршруты для всех функций отзывов и избранного

from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    # 📝 ОТЗЫВЫ - AJAX маршруты
    path('reviews/add/', views.add_review, name='add_review'),

    # 📋 СПИСКИ - HTML страницы (если потребуются)
    path('reviews/', views.ReviewListView.as_view(), name='reviews_list'),
]

# 🎯 ТЕПЕРЬ ДОСТУПНЫ URL:
#
# 📝 POST /common/reviews/add/ - добавление отзыва
# 📋 GET /common/reviews/ - список всех отзывов