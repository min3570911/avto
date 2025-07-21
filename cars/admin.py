# 📁 cars/admin.py - ИСПРАВЛЕННЫЕ URL-паттерны для ссылок
# 🔗 Теперь используем правильные Django админ URL

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import CarCategory, CarProduct
from products.admin import ProductAdmin, CategoryAdmin


@admin.register(CarCategory)
class CarCategoryAdmin(CategoryAdmin):
    """🚗 Админка для категорий автомобилей"""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(category_type='cars')


@admin.register(CarProduct)
class CarProductAdmin(ProductAdmin):
    """🚗 Админка для товаров-автомобилей с ПРАВИЛЬНЫМИ ссылками"""

    # 🚗 Поля для отображения в списке
    list_display = [
        'get_main_image_preview',
        'get_product_name_link',  # ✅ ИСПРАВЛЕННАЯ ссылка
        'product_sku',
        'get_category_link',  # ✅ ИСПРАВЛЕННАЯ ссылка на категорию
        'display_price',
        'has_main_image_status',
        'newest_product'
    ]

    search_fields = [
        'product_name',
        'product_sku',
        'product_desription'
    ]

    list_filter = [
        'category',
        'newest_product',
        'created_at'
    ]

    fieldsets = (
        ('🚗 Основная информация', {
            'fields': ('product_name', 'slug', 'category', 'product_sku')
        }),
        ('💰 Цены', {
            'fields': ('price',)
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
        """🚗 Показываем только товары автомобилей"""
        return super().get_queryset(request).filter(category__category_type='cars')

    # 🔗 ИСПРАВЛЕННЫЕ МЕТОДЫ ДЛЯ АКТИВНЫХ ССЫЛОК

    def get_product_name_link(self, obj):
        """🔗 Активная ссылка на редактирование товара автомобиля"""
        # ✅ ИСПРАВЛЕНО: Используем правильный URL для cars админки
        url = reverse('admin:cars_carproduct_change', args=[obj.pk])
        return format_html('<a href="{}" style="font-weight: bold; color: #0066cc;">{}</a>',
                           url, obj.product_name)

    get_product_name_link.short_description = "НАЗВАНИЕ ТОВАРА"
    get_product_name_link.admin_order_field = 'product_name'

    def get_category_link(self, obj):
        """🔗 Активная ссылка на категорию автомобилей"""
        if obj.category:
            # ✅ ИСПРАВЛЕНО: Используем правильный URL для категорий авто
            url = reverse('admin:cars_carcategory_change', args=[obj.category.pk])
            return format_html('<a href="{}" style="color: #0066cc;">🚗 {}</a>',
                               url, obj.category.category_name)
        return "Нет категории"

    get_category_link.short_description = "КАТЕГОРИЯ"
    get_category_link.admin_order_field = 'category'