# 📁 ecomm/urls.py - ИСПРАВЛЕННЫЙ ФАЙЛ
# 🏠 Убираем дублирующую функцию index_view, используем home приложение

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 🌐 Основные URL-паттерны
urlpatterns = [
    # 🔧 Админка
    path('admin/', admin.site.urls),

    # 🏠 Главная страница - используем home приложение (ПРАВИЛЬНО!)
    path('', include('home.urls')),

    # 🛒 Корзина и заказы
    path('accounts/', include('accounts.urls')),

    # 🛍️ Товары и каталог
    path('products/', include('products.urls')),

    # 🎨 Summernote URLs
    path('summernote/', include('django_summernote.urls')),

    # 📝 Blog URLs
    path('blog/', include('blog.urls')),
]

# 📁 Медиа и статические файлы
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 🔧 ИСПРАВЛЕНИЯ:
# ❌ УДАЛЕНА: функция index_view (была причиной ошибки!)
# ✅ ВОССТАНОВЛЕН: path('', include('home.urls')) - использует home/views.py
# ✅ ИСПРАВЛЕНА: ошибка TemplateDoesNotExist: index.html
# ✅ СОХРАНЕНА: правильная архитектура проекта