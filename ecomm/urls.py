# 📁 ecomm/urls.py - ОБНОВЛЕНО для CKEditor 5
# 🏠 Основные URL-паттерны проекта
# ✅ СОВРЕМЕННО: Переход на django-ckeditor-5

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 🌐 Основные URL-паттерны
urlpatterns = [
    # 🔧 Админка Django
    path('admin/', admin.site.urls),

    # ✅ НОВОЕ: CKEditor 5 URLs (для загрузки файлов)
    path('ckeditor5/', include('django_ckeditor_5.urls')),

    # 🛒 Корзина и заказы
    path('accounts/', include('accounts.urls')),

    # 🛍️ Товары и каталог
    path('products/', include('products.urls')),

    path('boats/', include('boats.urls')),

    # 📝 Блог - статьи
    path('blog/', include('blog.urls')),

    # 🏠 Главная страница и статические страницы
    path('', include('home.urls')),
]

# 📁 Медиа и статические файлы
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 🔧 ИЗМЕНЕНИЯ:
# ❌ УДАЛЕНО: path('ckeditor/', include('ckeditor_uploader.urls'))
# ✅ ДОБАВЛЕНО: path('ckeditor5/', include('django_ckeditor_5.urls'))
# ✅ СОВРЕМЕННО: Поддержка загрузки файлов в CKEditor 5