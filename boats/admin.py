# 📁 boats/admin.py - ИСПРАВЛЕННЫЕ URL-паттерны для ссылок
# 🔗 Теперь используем правильные Django админ URL

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import BoatCategory, BoatProduct
from products.admin import ProductAdmin, CategoryAdmin


@admin.register(BoatCategory)
class BoatCategoryAdmin(CategoryAdmin):
    """🛥️ Админка для категорий лодок"""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(category_type='boats')


@admin.register(BoatProduct)
class BoatProductAdmin(ProductAdmin):
    """🛥️ Админка для товаров-лодок с ПРАВИЛЬНЫМИ ссылками"""

    # 🛥️ Поля для отображения в списке
    list_display = [
        'get_main_image_preview',
        'get_product_name_link',  # ✅ ИСПРАВЛЕННАЯ ссылка
        'product_sku',
        'get_category_link',  # ✅ ИСПРАВЛЕННАЯ ссылка на категорию
        'display_price',
        'get_boat_dimensions_fixed',  # ✅ Размеры в см
        'has_main_image_status',
        'newest_product'
    ]

    search_fields = [
        'product_name',
        'product_sku',
        'product_desription',
        'boat_mat_width',
        'boat_mat_length'
    ]

    list_filter = [
        'category',
        'newest_product',
        'boat_mat_width',
        'boat_mat_length',
        'created_at'
    ]

    fieldsets = (
        ('🛥️ Основная информация', {
            'fields': ('product_name', 'slug', 'category', 'product_sku')
        }),
        ('💰 Цены', {
            'fields': ('price',)
        }),
        ('📐 Размеры лодки', {
            'fields': ('boat_mat_length', 'boat_mat_width'),
            'description': 'Укажите размеры коврика для лодки в сантиметрах'
        }),
        ('📝 Описание', {
            'fields': ('product_desription',)
        }),
        ('⚙️ Настройки', {
            'fields': ('newest_product',),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        """🛥️ Показываем только товары лодок"""
        return super().get_queryset(request).filter(category__category_type='boats')

    # 🔗 ИСПРАВЛЕННЫЕ МЕТОДЫ ДЛЯ АКТИВНЫХ ССЫЛОК

    def get_product_name_link(self, obj):
        """🔗 Активная ссылка на редактирование товара лодки"""
        # ✅ ИСПРАВЛЕНО: Используем правильный URL для boats админки
        url = reverse('admin:boats_boatproduct_change', args=[obj.pk])
        return format_html('<a href="{}" style="font-weight: bold; color: #0066cc;">{}</a>',
                           url, obj.product_name)

    get_product_name_link.short_description = "НАЗВАНИЕ ТОВАРА"
    get_product_name_link.admin_order_field = 'product_name'

    def get_category_link(self, obj):
        """🔗 Активная ссылка на категорию лодок"""
        if obj.category:
            # ✅ ИСПРАВЛЕНО: Используем правильный URL для категорий
            url = reverse('admin:boats_boatcategory_change', args=[obj.category.pk])
            return format_html('<a href="{}" style="color: #0066cc;">⛵ {}</a>',
                               url, obj.category.category_name)
        return "Нет категории"

    get_category_link.short_description = "КАТЕГОРИЯ"
    get_category_link.admin_order_field = 'category'

    def get_boat_dimensions_fixed(self, obj):
        """🛥️ Размеры лодочного коврика в САНТИМЕТРАХ"""
        if obj.boat_mat_length and obj.boat_mat_width:
            return format_html('<span style="color: #007cba; font-weight: bold;">📏 Д: {}см × Ш: {}см</span>',
                               obj.boat_mat_length, obj.boat_mat_width)
        elif obj.boat_mat_length:
            return format_html('<span style="color: #007cba;">📏 Д: {}см</span>', obj.boat_mat_length)
        elif obj.boat_mat_width:
            return format_html('<span style="color: #007cba;">📏 Ш: {}см</span>', obj.boat_mat_width)
        return format_html('<span style="color: #999;">📏 Размеры не указаны</span>')

    get_boat_dimensions_fixed.short_description = "РАЗМЕРЫ КОВРИКА"