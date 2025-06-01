# 📁 ecomm/urls.py - ФИНАЛЬНАЯ ВЕРСИЯ без рекурсии
# 🏠 Основные URL-паттерны проекта
# ✅ ИСПРАВЛЕНО: Убраны все циклические зависимости

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 🌐 Основные URL-паттерны - ИСПРАВЛЕННЫЕ
urlpatterns = [
    # 🔧 Админка Django
    path('admin/', admin.site.urls),

    # ✅ CKEditor URLs (для загрузки файлов)
    path('ckeditor/', include('ckeditor_uploader.urls')),

    # 🛒 Корзина и заказы
    path('accounts/', include('accounts.urls')),

    # 🛍️ Товары и каталог
    path('products/', include('products.urls')),

    # 📝 Блог - статьи
    path('blog/', include('blog.urls')),

    # 🏠 Главная страница и статические страницы - В КОНЦЕ!
    path('', include('home.urls')),
]

# 📁 Медиа и статические файлы
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 🔧 КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ:
# ✅ УБРАНО: django_summernote.urls - источник рекурсии
# ✅ ИЗМЕНЕН ПОРЯДОК: home.urls перемещен в конец списка
# ✅ ДОБАВЛЕНО: четкое разделение маршрутов по приложениям
# ✅ ИСПРАВЛЕНО: правильная последовательность include() для избежания конфликтов

# 📝 ОБЪЯСНЕНИЕ ПОРЯДКА URL:
# 1. admin/ - админка (всегда первой)
# 2. ckeditor/ - для редактора
# 3. accounts/ - корзина и заказы
# 4. products/ - каталог товаров
# 5. blog/ - статьи блога
# 6. '' - главная и остальные страницы (ПОСЛЕДНИМ!)