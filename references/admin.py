# 📁 products/admin.py - КЛАССИЧЕСКАЯ АДМИНКА БЕЗ PROXY-МОДЕЛЕЙ
# 🎯 ЦЕЛЬ: Простая, понятная админка для всех основных моделей
# ✅ УБРАНО: Все сложные proxy-модели и группировки
# ✅ ДОБАВЛЕНО: Прямая регистрация всех моделей

from django.contrib import admin
from django.utils.html import mark_safe, format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django import forms
from django.core.exceptions import ValidationError
from django.db import models

from .models import Category, Product, ProductImage, Color, KitVariant, Coupon, ProductReview, Wishlist
from .forms import ProductImportForm

# 🆕 ИМПОРТ: Функции экспорта
from .export_views import get_export_button_html, get_export_context


# ============================================================================
# 🖼️ INLINE АДМИНКИ
# ============================================================================

class ProductImageInline(admin.TabularInline):
    """🖼️ Изображения товаров"""
    model = ProductImage
    verbose_name = "Изображение товара"
    verbose_name_plural = "Изображения товара"
    extra = 1
    fields = ('image', 'img_preview', 'is_main')
    readonly_fields = ('img_preview',)

    def img_preview(self, obj):
        """👁️ Предпросмотр изображения"""
        if obj.image:
            main_badge = '<span style="color: #f39c12; font-weight: bold;">🌟 ГЛАВНОЕ</span>' if obj.is_main else ''
            return format_html(
                '<div style="text-align: center; padding: 5px;">'
                '<img src="{}" style="max-width: 120px; max-height: 120px; object-fit: contain; border-radius: 5px; border: 2px solid {};">'
                '<br><small>{}</small>'
                '</div>',
                obj.image.url,
                '#f39c12' if obj.is_main else '#ddd',
                main_badge
            )
        return "📷 Изображение не загружено"

    img_preview.short_description = "Предпросмотр"


# ============================================================================
# 📂 АДМИНКА КАТЕГОРИЙ
# ============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """📂 Админка категорий товаров"""

    list_display = [
        'get_category_icon',
        'category_name',
        'category_type',
        'parent',
        'get_products_count',
        'display_order',
        'is_active'
    ]

    list_filter = [
        'category_type',
        'is_active',
        'parent',
        'created_at'
    ]

    search_fields = ['category_name', 'description']
    list_editable = ['display_order', 'is_active']
    list_per_page = 25
    prepopulated_fields = {'slug': ('category_name',)}

    fieldsets = (
        ('📂 Основная информация', {
            'fields': ('category_name', 'slug', 'category_type', 'parent')
        }),
        ('📝 Описание и контент', {
            'fields': ('description', 'additional_content', 'category_image'),
            'classes': ('collapse',)
        }),
        ('🔍 SEO оптимизация', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('⚙️ Настройки', {
            'fields': ('display_order', 'is_active')
        }),
    )

    def get_category_icon(self, obj):
        """🎯 Иконка типа категории"""
        icons = {
            'cars': '🚗',
            'boats': '🛥️'
        }
        icon = icons.get(obj.category_type, '📁')
        return f"{icon} {obj.category_name}"

    get_category_icon.short_description = "Категория"

    def get_products_count(self, obj):
        """📊 Количество товаров в категории"""
        count = obj.products.count()
        if count > 0:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 12px; font-size: 11px;">{} товаров</span>',
                count
            )
        return format_html('<span style="color: #6c757d;">Пусто</span>')

    get_products_count.short_description = "Товары"


# ============================================================================
# 🛍️ АДМИНКА ТОВАРОВ
# ============================================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """🛍️ Админка товаров"""

    inlines = [ProductImageInline]

    list_display = [
        'get_main_image_preview',
        'product_name',
        'product_sku',
        'get_category_info',
        'display_price',
        'get_boat_dimensions',
        'newest_product'
    ]

    list_filter = [
        'category__category_type',
        'category',
        'newest_product',
        'created_at'
    ]

    search_fields = [
        'product_name',
        'product_sku',
        'product_desription',
        'category__category_name'
    ]

    list_editable = ['newest_product']
    list_per_page = 25
    prepopulated_fields = {'slug': ('product_name',)}

    fieldsets = (
        ('🛍️ Основная информация', {
            'fields': ('product_sku', 'product_name', 'slug', 'category', 'price')
        }),
        ('📝 Описание', {
            'fields': ('product_desription',),
            'classes': ('collapse',)
        }),
        ('🛥️ Параметры лодок', {
            'fields': ('boat_mat_length', 'boat_mat_width'),
            'classes': ('collapse',),
            'description': 'Заполняется только для лодочных товаров'
        }),
        ('🔍 SEO оптимизация', {
            'fields': ('page_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('⚙️ Настройки', {
            'fields': ('newest_product',)
        }),
    )

    def get_main_image_preview(self, obj):
        """🖼️ Предпросмотр главного изображения"""
        main_image = obj.product_images.filter(is_main=True).first()
        if main_image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: cover; border-radius: 6px; border: 2px solid #f39c12;" title="Главное изображение">',
                main_image.image.url
            )

        first_image = obj.product_images.first()
        if first_image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: cover; border-radius: 6px; border: 2px solid #ddd;" title="Первое изображение">',
                first_image.image.url
            )

        return "📷 Нет фото"

    get_main_image_preview.short_description = "Фото"

    def get_category_info(self, obj):
        """📂 Информация о категории с иконкой"""
        if obj.category:
            icon = '🚗' if obj.category.category_type == 'cars' else '🛥️'
            return f"{icon} {obj.category.category_name}"
        return "❌ Без категории"

    get_category_info.short_description = "Категория"

    def display_price(self, obj):
        """💰 Отображение цены"""
        if obj.price:
            try:
                formatted_price = f"{obj.price:,}".replace(',', ' ')
                return format_html(
                    '<span style="color: green; font-weight: bold;">💰 {} BYN</span>',
                    formatted_price
                )
            except (ValueError, TypeError):
                return format_html('<span style="color: red;">❌ Некорректная цена</span>')
        return format_html('<span style="color: orange;">💰 Цена не указана</span>')

    display_price.short_description = "Цена"

    def get_boat_dimensions(self, obj):
        """📐 Размеры для лодок"""
        if obj.boat_mat_length or obj.boat_mat_width:
            length = obj.boat_mat_length or '?'
            width = obj.boat_mat_width or '?'
            return format_html(
                '<span style="background: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">📐 {}×{} см</span>',
                length, width
            )
        return "—"

    get_boat_dimensions.short_description = "Размеры лодки"

    # 🔧 Дополнительные URL для импорта/экспорта
    def get_urls(self):
        """🔗 Дополнительные URL для админки"""
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_view), name='products_product_import'),
            path('export/', self.admin_site.admin_view(self.export_view), name='products_product_export'),
        ]
        return custom_urls + urls

    def import_view(self, request):
        """📥 Перенаправление на импорт"""
        return redirect('import_form')

    def export_view(self, request):
        """📤 Перенаправление на экспорт"""
        return redirect('export_excel')

    def changelist_view(self, request, extra_context=None):
        """📊 Добавляем кнопки импорта/экспорта"""
        extra_context = extra_context or {}
        extra_context.update(get_export_context())
        return super().changelist_view(request, extra_context)


# ============================================================================
# 🎨 АДМИНКА ЦВЕТОВ
# ============================================================================

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    """🎨 Админка цветов"""

    list_display = ['name', 'color_type', 'hex_code', 'color_preview', 'is_available', 'display_order']
    list_filter = ['color_type', 'is_available']
    list_editable = ['display_order', 'is_available']
    search_fields = ['name']
    ordering = ['color_type', 'display_order']

    def color_preview(self, obj):
        """🎨 Предпросмотр цвета"""
        return mark_safe(
            f'<div style="width:20px; height:20px; background-color:{obj.hex_code}; border:1px solid #666; border-radius:3px; display:inline-block;"></div>'
        )

    color_preview.short_description = "Цвет"

    fieldsets = (
        ('🎨 Основная информация', {
            'fields': ('name', 'color_type', 'hex_code')
        }),
        ('⚙️ Настройки отображения', {
            'fields': ('display_order', 'is_available')
        }),
    )


# ============================================================================
# 📦 АДМИНКА КОМПЛЕКТАЦИЙ
# ============================================================================

@admin.register(KitVariant)
class KitVariantAdmin(admin.ModelAdmin):
    """📦 Админка комплектаций"""

    list_display = ['name', 'code', 'price_modifier', 'order', 'is_option']
    list_filter = ['is_option']
    list_editable = ['order', 'is_option']
    search_fields = ['name', 'code']
    ordering = ['order', 'name']

    fieldsets = (
        ('📦 Основная информация', {
            'fields': ('name', 'code', 'price_modifier')
        }),
        ('⚙️ Настройки', {
            'fields': ('order', 'is_option', 'image')
        }),
    )

    actions = ['make_option', 'make_kit']

    def make_option(self, request, queryset):
        """🔧 Превратить в опции"""
        queryset.update(is_option=True, order=100)
        self.message_user(request, f"✅ Превращено в опции: {queryset.count()} записей")

    def make_kit(self, request, queryset):
        """📦 Превратить в комплектации"""
        queryset.update(is_option=False)
        self.message_user(request, f"✅ Превращено в комплектации: {queryset.count()} записей")

    make_option.short_description = "🔧 Сделать опциями"
    make_kit.short_description = "📦 Сделать комплектациями"


# ============================================================================
# 🎟️ АДМИНКА КУПОНОВ
# ============================================================================

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """🎟️ Админка купонов"""

    list_display = ['coupon_code', 'is_expired', 'discount_amount', 'minimum_amount', 'get_usage_info']
    list_filter = ['is_expired', 'created_at']
    search_fields = ['coupon_code']

    fieldsets = (
        ('🎟️ Основная информация', {
            'fields': ('coupon_code', 'discount_amount', 'minimum_amount')
        }),
        ('⚙️ Настройки', {
            'fields': ('is_expired',)
        }),
    )

    def get_usage_info(self, obj):
        """📊 Информация об использовании"""
        # Здесь можно добавить подсчет использования купона
        return "Статистика использования"

    get_usage_info.short_description = "Использование"


# ============================================================================
# ⭐ АДМИНКА ОТЗЫВОВ
# ============================================================================

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """⭐ Админка отзывов"""

    list_display = ['get_product_name', 'get_user_info', 'stars', 'get_review_preview', 'date_added']
    list_filter = ['stars', 'date_added']
    search_fields = ['content', 'product__product_name', 'user__username']

    def get_product_name(self, obj):
        """🛍️ Название товара"""
        if obj.product:
            return obj.product.product_name
        return "❌ Товар удален"

    get_product_name.short_description = "Товар"

    def get_user_info(self, obj):
        """👤 Информация о пользователе"""
        if obj.user:
            return obj.user.username
        return "❌ Пользователь удален"

    get_user_info.short_description = "Пользователь"

    def get_review_preview(self, obj):
        """📝 Превью отзыва"""
        if obj.content:
            preview = obj.content[:100]
            if len(obj.content) > 100:
                preview += "..."
            return preview
        return "Без текста"

    get_review_preview.short_description = "Отзыв"


# ============================================================================
# ❤️ АДМИНКА ИЗБРАННОГО
# ============================================================================

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """❤️ Админка избранного"""

    list_display = ['get_user_info', 'get_product_name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__product_name']

    def get_user_info(self, obj):
        """👤 Информация о пользователе"""
        if obj.user:
            return obj.user.username
        return "❌ Пользователь удален"

    get_user_info.short_description = "Пользователь"

    def get_product_name(self, obj):
        """🛍️ Название товара"""
        if obj.product:
            return obj.product.product_name
        return "❌ Товар удален"

    get_product_name.short_description = "Товар"


# ============================================================================
# 🎯 НАСТРОЙКИ АДМИНКИ
# ============================================================================

# 🎨 Заголовки админки
admin.site.site_header = "🛒 Автоковрики - Админ-панель"
admin.site.site_title = "Автоковрики"
admin.site.index_title = "Управление интернет-магазином"

# 📝 Настройка пустых значений
admin.site.empty_value_display = '(Не заполнено)'

# ============================================================================
# 📝 КОММЕНТАРИИ ДЛЯ РАЗРАБОТЧИКА
# ============================================================================

# 🔧 КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ:
# ✅ УБРАНО: Все proxy-модели и сложные группировки
# ✅ ДОБАВЛЕНО: Прямая регистрация всех основных моделей
# ✅ УПРОЩЕНО: Простая, понятная структура админки
# ✅ СОХРАНЕНО: Весь функционал импорта/экспорта
# ✅ УЛУЧШЕНО: Более информативные отображения полей

# 🎯 РЕЗУЛЬТАТ:
# - Простая админка без группировок
# - Все модели доступны напрямую
# - Удобный интерфейс для управления
# - Готовность к дальнейшему рефакторингу

# ⚠️ ВАЖНО:
# После применения этого файла нужно:
# 1. Удалить импорт admin_setup в старой админке
# 2. Перезапустить сервер Django
# 3. Проверить, что все модели отображаются корректно