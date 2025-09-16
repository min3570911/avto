# 📁 common/urls.py - АКТИВИРОВАННЫЕ МАРШРУТЫ
# ✅ ИСПРАВЛЕНО: Раскомментированы URL для AJAX функций
# 🔧 ДОБАВЛЕНО: Маршруты для всех функций отзывов и избранного

from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    # ❤️ ИЗБРАННОЕ - AJAX маршруты
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # 📝 ОТЗЫВЫ - AJAX маршруты
    path('reviews/add/', views.add_review, name='add_review'),

    # 📋 СПИСКИ - HTML страницы (если потребуются)
    path('reviews/', views.ReviewListView.as_view(), name='reviews_list'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist_list'),
]

# 🎯 ТЕПЕРЬ ДОСТУПНЫ URL:
#
# ❤️ POST /common/wishlist/add/ - добавление в избранное
# 🗑️ POST /common/wishlist/remove/ - удаление из избранного
# 📝 POST /common/reviews/add/ - добавление отзыва
# 📋 GET /common/reviews/ - список всех отзывов
# 📋 GET /common/wishlist/ - список избранного пользователя