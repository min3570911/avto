# 📁 products/admin.py - ИСПРАВЛЕННАЯ версия без дублирования регистрации
# 🛥️ УБРАНО: Дублирующая регистрация Proxy моделей (теперь только в proxy_admin.py)
# ✅ СОХРАНЕНО: Вся существующая функциональность SEO, экспорта, валидации для основных моделей

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
        """💾 Информация о хранилище файла"""
        if obj.image:
            # 🎯 Показываем информацию о OverwriteStorage
            storage_type = obj.image.storage.__class__.__name__
            if storage_type == 'OverwriteStorage':
                return format_html('<span style="color: green;">✅ OverwriteStorage</span>')
            else:
                return format_html('<span style="color: orange;">⚠️ DefaultStorage</span>')
        return "💾 Файл не загружен"

    storage_info.short_description = "Хранилище"


# 📋 СУЩЕСТВУЮЩАЯ форма валидации категорий
class CategoryAdminForm(forms.ModelForm):
    """📋 Форма для валидации категорий с проверкой SEO полей"""

    class Meta:
        model = Category
        fields = '__all__'

    def clean_meta_title(self):
        meta_title = self.cleaned_data.get("meta_title")
        if meta_title and len(meta_title) > 60:
            raise ValidationError(
                f"⚠️ SEO-заголовок слишком длинный ({len(meta_title)} симв.). "
                f"Максимум 60."
            )
        return meta_title

    def clean_meta_description(self):
        meta_description = self.cleaned_data.get("meta_description")
        if meta_description and len(meta_description) > 160:
            raise ValidationError(
                f"⚠️ SEO-описание слишком длинное ({len(meta_description)} симв.). "
                f"Максимум 160."
            )
        return meta_description

    def clean(self):
        """🛥️ Валидация иерархии лодок"""
        cleaned_data = super().clean()
        category_type = cleaned_data.get('category_type')
        parent = cleaned_data.get('parent')

        if parent and parent.category_type != category_type:
            raise ValidationError({
                'parent': f"Родительская категория должна иметь тот же тип: {category_type}"
            })

        return cleaned_data


class CategoryAdmin(admin.ModelAdmin):
    """📂 Базовая админка категорий (НЕ РЕГИСТРИРУЕТСЯ напрямую, используется для наследования)"""

    form = CategoryAdminForm

    # 📊 Список с полями для лодок
    list_display = [
        "get_category_hierarchy",
        "category_sku",
        "slug",
        "get_products_count",
        "display_order",
        "is_active",
        "image_preview_small",
        "storage_status",
        "seo_status",
    ]
    list_filter = [
        "category_type",
        "is_active",
        "created_at",
        "updated_at"
    ]
    search_fields = [
        "category_name",
        "slug",
        "category_sku",
        "meta_title",
        "parent__category_name"
    ]
    list_editable = ["display_order", "is_active", "category_sku"]
    prepopulated_fields = {"slug": ("category_name",)}
    list_per_page = 20

    # 🗂️ Секции формы
    fieldsets = (
        ("📋 Основная информация", {
            "fields": (
                "category_name",
                "category_sku",
                "slug",
                ("category_type", "parent"),
                "category_image",
                "image_preview",
                "storage_info",
            ),
            "description": "🏷️ Базовая информация о категории. Для лодок укажите тип и родительскую категорию."
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

    # 🔍 Поиск и фильтры
    list_filter = [
        'category',
        'newest_product',
        'created_at',
        'updated_at',
        'category__category_type'  # 🛥️ Фильтр по типу категории
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

    # 🎨 СУЩЕСТВУЮЩИЕ методы админки
    def get_main_image_preview(self, obj):
        """🖼️ Предпросмотр главного изображения товара"""
        main_image = obj.product_images.filter(is_main=True).first()  # Исправлено с obj.images на obj.product_images
        if main_image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: cover; border-radius: 6px; border: 2px solid #f39c12;" title="Главное изображение">',
                main_image.image.url
            )

        # Если нет главного, берём первое
        first_image = obj.images.first()
        if first_image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: cover; border-radius: 6px; border: 2px solid #ddd;" title="Первое изображение (не главное)">',
                first_image.image.url
            )

        return "📷 Нет фото"

    get_main_image_preview.short_description = "Фото"

    def display_price(self, obj):
        """💰 Отображение цены в красивом формате"""
        if obj.price:
            return format_html('<span style="color: green; font-weight: bold;">💰 {:,} руб.</span>', obj.price)
        return format_html('<span style="color: #999;">💰 Не указана</span>')

    display_price.short_description = "Цена"
    display_price.admin_order_field = 'price'

    def has_main_image_status(self, obj):
        """🖼️ Статус главного изображения"""
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return format_html('<span style="color: green;">🌟 Главное фото</span>')

        if obj.images.exists():
            return format_html('<span style="color: orange;">⚠️ Нет главного</span>')

        return format_html('<span style="color: red;">❌ Нет фото</span>')

    has_main_image_status.short_description = "Изображения"

    def storage_status(self, obj):
        """💾 Общий статус хранилища изображений"""
        images = obj.images.all()
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
        if hasattr(obj, 'boat_length') and obj.boat_length:
            dimensions = []
            if obj.boat_length:
                dimensions.append(f"Д: {obj.boat_length}м")
            if hasattr(obj, 'boat_width') and obj.boat_width:
                dimensions.append(f"Ш: {obj.boat_width}м")
            if hasattr(obj, 'boat_height') and obj.boat_height:
                dimensions.append(f"В: {obj.boat_height}м")

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
        """🖼️ Установить первое изображение как главное для товаров без главного"""
        updated_count = 0
        for product in queryset:
            main_image = product.images.filter(is_main=True).first()
            if not main_image:
                first_image = product.images.first()
                if first_image:
                    # Убираем главное у всех изображений товара
                    product.images.update(is_main=False)
                    # Устанавливаем первое как главное
                    first_image.is_main = True
                    first_image.save()
                    updated_count += 1

        self.message_user(request, f"✅ Установлено главное изображение для {updated_count} товаров")

    def generate_missing_slugs(self, request, queryset):
        """🔗 Генерация отсутствующих slug для товаров"""
        from django.utils.text import slugify
        updated_count = 0

        for product in queryset:
            if not product.slug:
                product.slug = slugify(product.product_name)
                product.save()
                updated_count += 1

        self.message_user(request, f"✅ Сгенерированы slug для {updated_count} товаров")

    def check_images_storage(self, request, queryset):
        """💾 Проверка хранилища изображений товаров"""
        overwrite_products = 0
        default_products = 0
        no_images_products = 0

        for product in queryset:
            images = product.images.all()
            if not images:
                no_images_products += 1
                continue

            has_overwrite = any(img.image.storage.__class__.__name__ == 'OverwriteStorage' for img in images)
            if has_overwrite:
                overwrite_products += 1
            else:
                default_products += 1

        message = f"💾 Анализ хранилища: OverwriteStorage: {overwrite_products}, DefaultStorage: {default_products}, Без изображений: {no_images_products}"
        self.message_user(request, message)

    # 🏷️ Названия действий
    mark_as_new.short_description = "⭐ Отметить как новые товары"
    mark_as_regular.short_description = "📦 Убрать отметку 'новый'"
    set_first_image_as_main.short_description = "🖼️ Установить первое фото как главное"
    generate_missing_slugs.short_description = "🔗 Сгенерировать отсутствующие slug"
    check_images_storage.short_description = "💾 Проверить хранилище изображений"

    def changelist_view(self, request, extra_context=None):
        """🎨 Переопределяем представление списка для добавления контекста экспорта"""
        export_context = get_export_context()
        extra_context = extra_context or {}
        extra_context.update({
            'export_context': export_context,
            'has_export_permission': request.user.is_staff,
        })
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        """🔗 Добавляем URL для импорта-экспорта"""
        urls = super().get_urls()
        from django.urls import path
        from .admin_views import import_form_view
        from .export_views import export_excel_view

        custom_urls = [
            path('import/', import_form_view,
                 name='%s_%s_import' % (self.model._meta.app_label, self.model._meta.model_name)),
            path('export/', export_excel_view,
                 name='%s_%s_export' % (self.model._meta.app_label, self.model._meta.model_name)),
        ]
        return custom_urls + urls


# ✅ РЕГИСТРИРУЕМ ТОЛЬКО ОСНОВНЫЕ МОДЕЛИ (без Proxy)
# Proxy модели регистрируются в proxy_admin.py через admin_setup.py

@admin.register(Category)
class CategoryMainAdmin(CategoryAdmin):
    """📂 Основная админка категорий (все типы вместе) - для совместимости и резерва"""
    pass


@admin.register(Product)
class ProductMainAdmin(ProductAdmin):
    """🛍️ Основная админка товаров (все типы вместе) - для совместимости и резерва"""

    # ✅ КАСТОМНЫЙ ШАБЛОН: Используем тот же шаблон с кнопками импорта/экспорта
    change_list_template = 'admin/products/product/change_list.html'


# 📦 ДОПОЛНИТЕЛЬНЫЕ МОДЕЛИ

@admin.register(KitVariant)
class KitVariantAdmin(admin.ModelAdmin):
    """📦 Админка для комплектаций товаров"""
    list_display = ['name', 'code', 'price_modifier', 'order', 'is_option', 'formatted_price']
    list_filter = ['is_option']
    search_fields = ['name', 'code']
    list_editable = ['price_modifier', 'order', 'is_option']
    ordering = ['is_option', 'order']

    def formatted_price(self, obj):
        """💰 Отображает цену в удобном формате"""
        return f"{obj.price_modifier} руб."

    formatted_price.short_description = "Цена"

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

# 🎯 АКТИВАЦИЯ ГРУППИРОВКИ
# ========================

# 🚀 ПОДКЛЮЧАЕМ ГРУППИРОВАННЫЕ АДМИНКИ
from .admin_setup import *

# 🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ ИСПРАВЛЕНИЯ:
#
# ✅ УБРАНО:
# - Двойная регистрация Proxy моделей (оставлена только в proxy_admin.py)
# - Код unregister оригинальных моделей
# - Конфликтующие админки в конце файла
#
# ✅ ДОБАВЛЕНО:
# - Импорт admin_setup.py для активации группировки
# - Полная функциональность импорта/экспорта в Proxy админках
#
# ✅ СОХРАНЕНО:
# - Все базовые классы CategoryAdmin и ProductAdmin для наследования
# - Основные админки Category и Product как резерв/совместимость
# - Вся функциональность импорта/экспорта
# - Все существующие методы, действия и валидация
#
# ✅ БЕЗОПАСНОСТЬ:
# - Не ломает существующий код
# - Не удаляет функциональность
# - Proxy админки работают через наследование от базовых классов
# - Легко откатить при необходимости