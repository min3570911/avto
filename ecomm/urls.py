# ecomm/urls.py
# 🛒 Основной URL-конфигуратор для упрощенного e-commerce проекта автоковриков

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


# 🏠 Простая функция для главной страницы (если нет home приложения)
def index_redirect(request):
    """🔄 Перенаправление на каталог товаров"""
    return redirect('/products/')


# 🔧 Основные URL-паттерны проекта
urlpatterns = [
    # 🔐 Административная панель Django
    path('admin/', admin.site.urls),

    # 🛒 Корзина и заказы (упрощенная версия)
    path('accounts/', include('accounts.urls')),

    # 🛍️ Товары, каталог, отзывы, избранное  
    path('products/', include('products.urls')),

    # 🏠 Главная страница (перенаправление на товары)
    path('', index_redirect, name='index'),
]

# 🖼️ Настройка обслуживания медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 🎨 Кастомизация заголовков админки
admin.site.site_header = "🛒 Управление магазином автоковриков"
admin.site.site_title = "Автоковрики - Админка"
admin.site.index_title = "Панель управления"