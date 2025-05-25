# 📁 ecomm/urls.py - ИСПРАВЛЕННЫЕ основные URL
# 🏠 Главная страница через приложение home и исправление проблемы с шаблоном

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 🌐 Основные URL-паттерны
urlpatterns = [
    # 🔧 Админка
    path('admin/', admin.site.urls),

    # 🏠 Главная страница - используем представление из home.views
    path('', include('home.urls')),

    # 🛒 Корзина и заказы
    path('accounts/', include('accounts.urls')),

    # 🛍️ Товары и каталог
    path('products/', include('products.urls')),
]

# 📁 Медиа и статические файлы
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 🔧 ИСПРАВЛЕНИЯ:
# ✅ УДАЛЕНА: функция index_view (используем представление из home/views.py)
# ✅ ИЗМЕНЕНО: path('', include('home.urls')) для использования home.index
# ✅ ИСПРАВЛЕНА: проблема с отсутствующим шаблоном index.html
# ✅ ИСПРАВЛЕНА: структура URL без конфликтов
# ✅ СОХРАНЕНЫ: все существующие URL без изменений