# 📁 products/admin.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ версия
# ✅ ИСПРАВЛЕНО: Все ошибки с obj.images → obj.product_images и format_html
# ✅ СОХРАНЕНО: Вся существующая функциональность SEO, экспорта, валидации

from django.contrib import admin
from django.utils.html import mark_safe, format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django import forms
from django.core.exceptions import ValidationError
from django.db import models

from .models import *
from .forms import ProductImportForm

# 🆕 ИМПОРТ: Функции экспорта
from .export_views import get_export_button_html, get_export_context


# 🖼️ СУЩЕСТВУЮЩАЯ инлайн админка для изображений товаров
class ProductImageInline(admin.TabularInline):
    """🖼️ Инлайн админка для изображений товаров с поддержкой OverwriteStorage"""

    model = ProductImage
    verbose_name = "Изображение товара"
    verbose_name_plural = "Изображения товара"
    extra = 1

    # 🎯 Поля для отображения и редактирования
    fields = ('image', 'img_preview', 'is_main', 'storage_info')
    readonly_fields = ('img_preview', 'storage_info')

    # 🎨 Кастомные стили для админки
    class Media:
        css = {
            'all': ('admin/css/product_images.css',)
        }
        js = ('admin/js/product_images.js',)

    def img_preview(self, obj):
        """👁️ Предпросмотр изображения с индикатором главного"""
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

    def storage_info(self, obj):
        """💾 Информация о хранилище изображения"""
        if obj.image:
            storage_type = obj.image.storage.__class__.__name__
            if storage_type == 'OverwriteStorage':
                return format_html('<span style="color: green;">✅ OverwriteStorage</span>')
            else:
                return format_html('<span style="color: orange;">⚠️ DefaultStorage</span>')
        return "💾 Файл не загружен"

    storage_info.short_description = "Хранилище"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """📂 Админка категорий товаров с SEO и группировкой"""

    # 📊 Отображение в списке
    list_display = [
        "get_category_hierarchy",
        "image_preview_small",
        "get_products_count",
        "storage_status",
        "seo_status",
        "is_active",
        "display_order"
    ]

    # 🔍 Фильтры и поиск
    list_filter = ["category_type", "is_active", "parent", "created_at"]
    search_fields = ["category_name", "meta_title", "meta_description"]
    list_editable = ["is_active", "display_order"]

    # 📝 Группировка полей в форме
    fieldsets = (
        ("📂 Основная информация", {
            "fields": ("category_name", "slug", "category_image", "image_preview"),
            "description": "🎯 Основные данные категории и изображение"
        }),
        ("🛥️ Тип и иерархия", {
            "fields": ("category_type", "parent"),
            "description": "🎯 Для автомобилей выберите тип 'Автомобили'. "
                           "Для лодок укажите тип и родительскую категорию."
        }),
        ("📝 Описание и контент", {
            "fields": ("description",),
            "classes": ("collapse",),
        }),
        ("🔍 SEO оптимизация", {
            "fields": ("meta_title", "meta_description"),
            "classes": ("collapse",),
            "description": "🎯 Настройки для поисковых систем (Title до 60 символов, Description до 160)"
        }),
        ("⚙️ Настройки отображения", {
            "fields": ("display_order", "is_active"),
        }),
    )

    readonly_fields = ["image_preview", "storage_info"]

    # 🎨 СУЩЕСТВУЮЩИЕ методы админки
    def get_category_hierarchy(self, obj):
        """📊 Показывает иерархию категории с отступами"""
        if obj.parent:
            return format_html(
                '<span style="margin-left: 20px;">└─ {} ({})</span>',
                obj.category_name,
                obj.get_category_type_display()
            )
        return format_html(
            '<strong>{} ({})</strong>',
            obj.category_name,
            obj.get_category_type_display()
        )

    get_category_hierarchy.short_description = "📂 Категория"
    get_category_hierarchy.admin_order_field = 'category_name'

    def get_products_count(self, obj):
        """📊 Показывает количество товаров"""
        count = obj.products.count()
        if count > 0:
            return format_html('<span style="color: green;">📦 {} товаров</span>', count)
        return format_html('<span style="color: #999;">📦 Пусто</span>')

    get_products_count.short_description = "Товары"

    def image_preview_small(self, obj):
        """🖼️ Маленький предпросмотр изображения категории"""
        if obj.category_image:
            return mark_safe(
                f'<img src="{obj.category_image.url}" style="max-width: 50px; max-height: 50px; object-fit: cover; border-radius: 4px;" />')
        return "📷 Нет изображения"

    image_preview_small.short_description = "Фото"

    def storage_status(self, obj):
        """💾 Статус хранилища изображения"""
        if obj.category_image:
            storage_type = obj.category_image.storage.__class__.__name__
            if storage_type == 'OverwriteStorage':
                return format_html('<span style="color: green;">✅ Safe</span>')
            else:
                return format_html('<span style="color: orange;">⚠️ Default</span>')
        return "💾 Нет файла"

    storage_status.short_description = "Хранилище"

    def seo_status(self, obj):
        """🔍 Статус SEO оптимизации"""
        has_title = bool(obj.meta_title)
        has_description = bool(obj.meta_description)

        if has_title and has_description:
            return format_html('<span style="color: green;">🔍 Полное SEO</span>')
        elif has_title or has_description:
            return format_html('<span style="color: orange;">🔍 Частичное SEO</span>')
        else:
            return format_html('<span style="color: red;">🔍 Нет SEO</span>')

    seo_status.short_description = "SEO"

    def image_preview(self, obj):
        """🖼️ Предпросмотр изображения в форме"""
        if obj.category_image:
            return mark_safe(
                f'<img src="{obj.category_image.url}" style="max-width: 300px; max-height: 200px; object-fit: contain; border: 1px solid #ddd; border-radius: 8px;" />')
        return "📷 Изображение не загружено"

    image_preview.short_description = "Предпросмотр"

    def storage_info(self, obj):
        """💾 Информация о хранилище файла категории"""
        if obj.category_image:
            storage_type = obj.category_image.storage.__class__.__name__
            if storage_type == 'OverwriteStorage':
                return format_html('<span style="color: green;">✅ OverwriteStorage</span>')
            else:
                return format_html('<span style="color: orange;">⚠️ DefaultStorage</span>')
        return "💾 Файл не загружен"

    storage_info.short_description = "Хранилище"


class ProductAdmin(admin.ModelAdmin):
    """🛍️ Базовая админка товаров (НЕ РЕГИСТРИРУЕТСЯ напрямую, используется для наследования)"""

    # 🖼️ Подключаем инлайн изображения
    inlines = [ProductImageInline]

    # 📊 Поля списка
    list_display = [
        'get_main_image_preview',
        'product_name',
        'product_sku',
        'category',
        'display_price',
        'has_main_image_status',
        'storage_status',
        'newest_product'
    ]

    # 🔍 ✅ ИСПРАВЛЕННЫЕ фильтры (только реальные поля модели)
    list_filter = [
        'category',  # ✅ ForeignKey поле
        'newest_product',  # ✅ BooleanField поле
        'created_at',  # ✅ DateTimeField поле
        'updated_at',  # ✅ DateTimeField поле
        'category__category_type'  # ✅ Связанное поле (cars/boats)
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

    # 🗂️ Секции формы
    fieldsets = (
        ('🛍️ Основная информация', {
            'fields': ('product_sku', 'product_name', 'slug', 'category', 'price')
        }),
        ('📝 Описание и контент', {
            'fields': ('product_desription',),
            'classes': ('collapse',)
        }),
        ('🔍 SEO оптимизация', {
            'fields': ('page_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('⚙️ Настройки товара', {
            'fields': ('newest_product',)
        }),
    )

    # 🎨 ✅ ИСПРАВЛЕННЫЕ методы админки
    def get_main_image_preview(self, obj):
        """🖼️ Предпросмотр главного изображения товара - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        # ✅ ИСПРАВЛЕНО: Используем product_images вместо images
        main_image = obj.product_images.filter(is_main=True).first()
        if main_image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: cover; border-radius: 6px; border: 2px solid #f39c12;" title="Главное изображение">',
                main_image.image.url
            )

        # Если нет главного, берём первое
        # ✅ ИСПРАВЛЕНО: Используем product_images вместо images
        first_image = obj.product_images.first()
        if first_image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: cover; border-radius: 6px; border: 2px solid #ddd;" title="Первое изображение (не главное)">',
                first_image.image.url
            )

        return "📷 Нет фото"

    get_main_image_preview.short_description = "Фото"

    def display_price(self, obj):
        """💰 Отображение цены в красивом формате - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        if obj.price:
            # ✅ ИСПРАВЛЕНО: Предварительно форматируем число, затем используем format_html
            try:
                formatted_price = f"{obj.price:,}".replace(',', ' ')  # Используем пробелы вместо запятых
                return format_html(
                    '<span style="color: green; font-weight: bold;">💰 {} руб.</span>',
                    formatted_price
                )
            except (ValueError, TypeError):
                return format_html(
                    '<span style="color: green; font-weight: bold;">💰 {} руб.</span>',
                    obj.price
                )
        return format_html('<span style="color: #999;">💰 Не указана</span>')

    display_price.short_description = "Цена"
    display_price.admin_order_field = 'price'

    def has_main_image_status(self, obj):
        """🖼️ Статус главного изображения - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        # ✅ ИСПРАВЛЕНО: Используем product_images вместо images
        main_image = obj.product_images.filter(is_main=True).first()
        if main_image:
            return format_html('<span style="color: green;">🌟 Главное фото</span>')

        # ✅ ИСПРАВЛЕНО: Используем product_images вместо images
        if obj.product_images.exists():
            return format_html('<span style="color: orange;">⚠️ Нет главного</span>')

        return format_html('<span style="color: red;">❌ Нет фото</span>')

    has_main_image_status.short_description = "Изображения"

    def storage_status(self, obj):
        """💾 Общий статус хранилища изображений - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        # ✅ ИСПРАВЛЕНО: Используем product_images вместо images
        images = obj.product_images.all()
        if not images:
            return "💾 Нет файлов"

        overwrite_count = sum(1 for img in images if img.image.storage.__class__.__name__ == 'OverwriteStorage')
        total_count = len(images)

        if overwrite_count == total_count:
            return format_html('<span style="color: green;">✅ Все Safe</span>')
        elif overwrite_count > 0:
            return format_html('<span style="color: orange;">⚠️ Смешанное</span>')
        else:
            return format_html('<span style="color: red;">❌ Default</span>')

    storage_status.short_description = "Хранилище"

    def get_boat_dimensions(self, obj):
        """🛥️ Отображение размеров лодочного коврика"""
        if hasattr(obj, 'boat_mat_length') and obj.boat_mat_length:
            dimensions = []
            if obj.boat_mat_length:
                dimensions.append(f"Д: {obj.boat_mat_length}м")
            if hasattr(obj, 'boat_mat_width') and obj.boat_mat_width:
                dimensions.append(f"Ш: {obj.boat_mat_width}м")

            if dimensions:
                return format_html('<span style="color: #007cba;">🛥️ {}</span>', " × ".join(dimensions))

        return format_html('<span style="color: #999;">🛥️ Не указаны</span>')

    get_boat_dimensions.short_description = "Размеры коврика"

    # 🔧 СУЩЕСТВУЮЩИЕ действия админки
    actions = [
        'mark_as_new',
        'mark_as_regular',
        'set_first_image_as_main',
        'generate_missing_slugs',
        'check_images_storage'
    ]

    def mark_as_new(self, request, queryset):
        """⭐ Отметить выбранные товары как новые"""
        updated = queryset.update(newest_product=True)
        self.message_user(request, f"✅ Отмечено как новые: {updated} товаров")

    def mark_as_regular(self, request, queryset):
        """📦 Убрать отметку 'новый' с выбранных товаров"""
        updated = queryset.update(newest_product=False)
        self.message_user(request, f"✅ Убрана отметка 'новый': {updated} товаров")

    def set_first_image_as_main(self, request, queryset):
        """🖼️ Установить первое изображение как главное для выбранных товаров"""
        updated_count = 0
        for product in queryset:
            # ✅ ИСПРАВЛЕНО: Используем product_images вместо images
            first_image = product.product_images.first()
            if first_image and not first_image.is_main:
                # Сбросить все главные
                product.product_images.update(is_main=False)
                # Установить первое как главное
                first_image.is_main = True
                first_image.save()
                updated_count += 1

        self.message_user(request, f"✅ Обновлено главных изображений: {updated_count}")

    def generate_missing_slugs(self, request, queryset):
        """🔗 Генерировать отсутствующие слаги"""
        from django.utils.text import slugify
        updated_count = 0
        for product in queryset.filter(slug__isnull=True):
            product.slug = slugify(product.product_name)
            product.save(update_fields=['slug'])
            updated_count += 1

        self.message_user(request, f"✅ Сгенерировано слагов: {updated_count}")

    def check_images_storage(self, request, queryset):
        """🔍 Проверить хранилище изображений"""
        stats = {'overwrite': 0, 'default': 0, 'no_images': 0}

        for product in queryset:
            # ✅ ИСПРАВЛЕНО: Используем product_images вместо images
            images = product.product_images.all()
            if not images:
                stats['no_images'] += 1
            else:
                for img in images:
                    if img.image.storage.__class__.__name__ == 'OverwriteStorage':
                        stats['overwrite'] += 1
                    else:
                        stats['default'] += 1

        self.message_user(
            request,
            f"📊 Статистика: OverwriteStorage: {stats['overwrite']}, "
            f"DefaultStorage: {stats['default']}, Без фото: {stats['no_images']}"
        )

    mark_as_new.short_description = "⭐ Отметить как новые"
    mark_as_regular.short_description = "📦 Убрать отметку 'новый'"
    set_first_image_as_main.short_description = "🖼️ Установить первое фото главным"
    generate_missing_slugs.short_description = "🔗 Генерировать слаги"
    check_images_storage.short_description = "🔍 Проверить хранилище изображений"


@admin.register(KitVariant)
class KitVariantAdmin(admin.ModelAdmin):
    """📦 Админка комплектаций товаров"""
    list_display = ['name', 'code', 'formatted_price', 'order', 'is_option']
    list_filter = ['is_option']
    list_editable = ['order', 'is_option']
    search_fields = ['name', 'code']
    ordering = ['order', 'name']

    def formatted_price(self, obj):
        """💰 Отображение модификатора цены - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        if obj.price_modifier:
            try:
                # ✅ ИСПРАВЛЕНО: Предварительно форматируем число
                formatted_modifier = f"{abs(obj.price_modifier):,}".replace(',', ' ')
                if obj.price_modifier > 0:
                    return format_html(
                        '<span style="color: green;">💰 +{} руб.</span>',
                        formatted_modifier
                    )
                elif obj.price_modifier < 0:
                    return format_html(
                        '<span style="color: red;">💰 -{} руб.</span>',
                        formatted_modifier
                    )
            except (ValueError, TypeError):
                return format_html('<span style="color: #999;">💰 {}</span>', obj.price_modifier)

        return format_html('<span style="color: #999;">💰 Без изменений</span>')

    formatted_price.short_description = "Модификатор цены"
    formatted_price.admin_order_field = 'price_modifier'

    fieldsets = (
        ('📦 Основная информация', {
            'fields': ('name', 'code', 'price_modifier')
        }),
        ('⚙️ Настройки отображения', {
            'fields': ('order', 'is_option', 'image')
        }),
    )

    actions = ['make_option', 'make_kit']

    def make_option(self, request, queryset):
        """🔧 Превратить выбранные элементы в опции"""
        queryset.update(is_option=True, order=100)
        self.message_user(request, f"✅ Превращено в опции: {queryset.count()} записей")

    def make_kit(self, request, queryset):
        """📦 Превратить выбранные элементы в комплектации"""
        queryset.update(is_option=False)
        self.message_user(request, f"✅ Превращено в комплектации: {queryset.count()} записей")

    make_option.short_description = "🔧 Сделать опциями"
    make_kit.short_description = "📦 Сделать комплектациями"


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    """🎨 Админка для цветов ковриков и окантовки"""
    list_display = ['name', 'color_type', 'hex_code', 'color_preview', 'is_available', 'display_order']
    list_filter = ['color_type', 'is_available']
    list_editable = ['display_order', 'is_available']
    search_fields = ['name']
    ordering = ['color_type', 'display_order']

    def color_preview(self, obj):
        """🎨 Показывает цветной квадрат с цветом в админке"""
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


# 🎯 Настройки заголовков админки
admin.site.site_header = "🛒 Автоковрики и лодочные коврики - Админ-панель"
admin.site.site_title = "Автоковрики"
admin.site.index_title = "Управление интернет-магазином"

# 📝 Настройка пустых значений
admin.site.empty_value_display = '(Не заполнено)'

# 🎨 ДОПОЛНИТЕЛЬНЫЕ АДМИНКИ (не регистрируем, только определяем для наследования)

# Эти модели регистрируются только если не используются proxy-модели из других приложений:
# - Coupon (купоны)
# - ProductReview (отзывы)
# - Wishlist (избранное)
# - ProductImage (изображения - через inline)

# 🔧 ПРИМЕЧАНИЕ:
# ProductAdmin НЕ регистрируется напрямую - используется только для наследования
# в boats.admin.BoatProductAdmin и cars.admin.CarProductAdmin