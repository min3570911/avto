# 📁 ecomm/urls.py - ОБНОВЛЕНО для поддержки common приложения
# 🏠 Основные URL-паттерны проекта
# ✅ ДОБАВЛЕНО: подключение common/urls.py для AJAX функций

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 🌐 Основные URL-паттерны
urlpatterns = [
    # 🔧 Админка Django
    path('admin/', admin.site.urls),

    # ✅ CKEditor 5 URLs (для загрузки файлов)
    path('ckeditor5/', include('django_ckeditor_5.urls')),

    # 🛒 Корзина и заказы
    path('accounts/', include('accounts.urls')),

    # 🛍️ Товары и каталог
    path('products/', include('products.urls')),

    # 🛥️ Лодки
    path('boats/', include('boats.urls')),

    # 📝 Блог - статьи
    path('blog/', include('blog.urls')),

    # ✅ ДОБАВЛЕНО: Общие функции (отзывы, избранное) - AJAX API
    path('common/', include('common.urls')),

    # 🏠 Главная страница и статические страницы
    path('', include('home.urls')),
]

# 📁 Медиа и статические файлы
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 🔧 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ:
# ✅ ДОБАВЛЕНО: path('common/', include('common.urls'))
#
# 🎯 ТЕПЕРЬ ДОСТУПНЫ:
# POST /common/wishlist/add/ - добавление в избранное
# POST /common/wishlist/remove/ - удаление из избранного
# POST /common/reviews/add/ - добавление отзыва
# GET /common/reviews/ - список всех отзывов
# GET /common/wishlist/ - список избранного пользователя