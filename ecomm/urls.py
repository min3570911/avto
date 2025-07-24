# 📁 ecomm/urls.py - ПОЛНОЕ ИСПРАВЛЕНИЕ для активных ссылок
# 🔗 Теперь все ссылки в админке будут работать

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

    # 🛍️ Товары и каталог (общие функции: импорт, экспорт, избранное, отзывы)
    path('references/', include('references.urls')),

    # 🚗 Раздел "Автомобили" (ОБЯЗАТЕЛЬНО должен быть)
    path('cars/', include('cars.urls')),

    # 🛥️ Раздел "Лодки" (ОБЯЗАТЕЛЬНО должен быть)
    path('boats/', include('boats.urls')),

    # 📝 Блог - статьи
    path('blog/', include('blog.urls')),

    # 🏠 Главная страница и статические страницы (должно быть последним)
    path('', include('home.urls')),
]

# 📁 Медиа и статические файлы
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ✅ КРИТИЧНО: Порядок URL имеет значение!
# - Специфичные URL (cars/, boats/) должны быть ДО общих ('')
# - Иначе home.urls перехватит все запросы

# 🔗 РЕЗУЛЬТАТ: Теперь ссылки будут работать:
# - /boats/product/lodka-challenger/ → boats.views.boat_product_detail
# - /cars/product/bmw-x5/ → cars.views.car_product_detail