# 📁 products/admin.py - ПОЛНЫЙ файл с простой группировкой лодок и автомобилей
# 🛥️ ДОБАВЛЕНО: Простая группировка товаров и категорий по типам
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

# 🆕 НОВЫЙ ИМПОРТ: Функции экспорта
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
                return format_html('<span style="color: orange;">⚠️ {}</span>', storage_type)
        return "💾 Хранилище не определено"

    storage_info.short_description = "Хранилище"


# 🆕 ФОРМА для CategoryAdmin с поддержкой лодок
class CategoryAdminForm(forms.ModelForm):
    """📝 Кастомная форма для категорий с валидацией SEO и иерархии лодок"""

    class Meta:
        model = Category
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🛥️ Фильтрация родительских категорий по типу
        if 'parent' in self.fields:
            if self.instance and self.instance.pk:
                category_type = self.instance.category_type
                self.fields['parent'].queryset = Category.objects.filter(
                    category_type=category_type
                ).exclude(pk=self.instance.pk)
            else:
                self.fields['parent'].queryset = Category.objects.all()

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
        ("📝 Контент категории", {
            "fields": ("description", "additional_content"),
            "classes": ("wide",),
            "description": "📄 Описание и дополнительный контент (видео, HTML)"
        }),
        ("🔍 SEO оптимизация", {
            "fields": ("page_title", "meta_title", "meta_description"),
            "classes": ("collapse",),
            "description": "🎯 Настройки для поисковых систем"
        }),
        ("⚙️ Настройки отображения", {
            "fields": ("display_order", "is_active"),
            "description": "📊 Порядок сортировки и видимость"
        }),
    )

    readonly_fields = ["image_preview", "storage_info"]

    # 🎨 Кастомные методы отображения
    def get_category_hierarchy(self, obj):
        """🎨 Иерархия с иконками типов"""
        type_icon = "🛥️" if obj.category_type == 'boats' else "🚗"
        hierarchy = f" → {obj.category_name}" if obj.parent else obj.category_name
        return f"{type_icon} {hierarchy}"

    get_category_hierarchy.short_description = "Категория"

    def get_products_count(self, obj):
        """📊 Количество товаров в категории"""
        count = obj.products.count()
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            'green' if count > 0 else 'gray',
            count
        )

    get_products_count.short_description = "Товаров"

    def image_preview_small(self, obj):
        """🖼️ Маленький предпросмотр изображения"""
        if obj.category_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 3px;" />',
                obj.category_image.url
            )
        return "❌"

    image_preview_small.short_description = "Фото"

    def image_preview(self, obj):
        """🖼️ Большой предпросмотр изображения"""
        if obj.category_image:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 300px; max-height: 200px; object-fit: contain; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />'
                '<br><small style="color: #666;">{}x{} пикселей</small>'
                '</div>',
                obj.category_image.url,
                obj.category_image.width if hasattr(obj.category_image, 'width') else '?',
                obj.category_image.height if hasattr(obj.category_image, 'height') else '?'
            )
        return "📷 Изображение не загружено"

    image_preview.short_description = "Предпросмотр изображения"

    def storage_status(self, obj):
        """💾 Статус хранилища"""
        if obj.category_image:
            storage_type = obj.category_image.storage.__class__.__name__
            if storage_type == 'OverwriteStorage':
                return format_html('<span style="color: green;">✅</span>')
            else:
                return format_html('<span style="color: orange;">⚠️</span>')
        return "❌"

    storage_status.short_description = "Хранилище"

    def storage_info(self, obj):
        """💾 Подробная информация о хранилище"""
        if obj.category_image:
            storage_type = obj.category_image.storage.__class__.__name__
            file_size = obj.category_image.size if hasattr(obj.category_image, 'size') else 0
            return format_html(
                '<div style="font-family: monospace; font-size: 12px;">'
                '<strong>Тип:</strong> {}<br>'
                '<strong>Размер:</strong> {} KB<br>'
                '<strong>Путь:</strong> {}'
                '</div>',
                storage_type,
                round(file_size / 1024, 1) if file_size else 0,
                obj.category_image.name
            )
        return "💾 Файл не загружен"

    storage_info.short_description = "Информация о файле"

    def seo_status(self, obj):
        """🔍 Статус SEO оптимизации"""
        score = 0
        if obj.meta_title: score += 1
        if obj.meta_description: score += 1
        if obj.page_title: score += 1

        colors = ['red', 'orange', 'orange', 'green']
        return format_html(
            '<span style="color: {};">{}/3</span>',
            colors[score],
            score
        )

    seo_status.short_description = "SEO"

    # 🎯 Действия
    actions = ['optimize_seo', 'check_storage']

    def optimize_seo(self, request, queryset):
        """🔍 Автоматическая SEO оптимизация"""
        optimized = 0
        for category in queryset:
            changed = False
            if not category.meta_title:
                category.meta_title = (f"Автоковрики для {category.category_name} | "
                                       f"Купить в интернет-магазине")[:60]
                changed = True
            if not category.meta_description:
                if category.category_type == 'boats':
                    category.meta_description = (f"Лодочные коврики для {category.category_name}. "
                                                 f"Высокое качество, точная посадка. "
                                                 f"Доставка по РБ. Гарантия качества.")[:160]
                else:
                    category.meta_description = (f"Автоковрики для {category.category_name}. "
                                                 f"3D и текстильные варианты. "
                                                 f"Доставка по РБ. Гарантия качества.")[:160]
                changed = True
            if changed:
                category.save()
                optimized += 1
        self.message_user(request, f"🔍 SEO оптимизировано для {optimized} категорий")

    optimize_seo.short_description = "🔍 Оптимизировать SEO"

    def check_storage(self, request, queryset):
        """💾 Проверка типа хранилища"""
        overwrite_count = 0
        standard_count = 0

        for category in queryset:
            if category.category_image:
                storage_type = category.category_image.storage.__class__.__name__
                if storage_type == 'OverwriteStorage':
                    overwrite_count += 1
                else:
                    standard_count += 1

        self.message_user(
            request,
            f"💾 Проверка хранилища: {overwrite_count} с OverwriteStorage, {standard_count} со стандартным"
        )

    check_storage.short_description = "💾 Проверить хранилище"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("products")


class ProductAdmin(admin.ModelAdmin):
    """🛍️ Базовая админка товаров (НЕ РЕГИСТРИРУЕТСЯ напрямую, используется для наследования)"""

    list_display = [
        'get_main_image_preview',
        'product_name',
        'product_sku',
        'category',
        'display_price',
        'get_boat_dimensions',
        'has_main_image_status',
        'storage_status',
        'newest_product'
    ]
    list_display_links = ['get_main_image_preview', 'product_name']
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
        'boat_mat_length',  # 🛥️ Поля УЖЕ существуют
        'boat_mat_width'  # 🛥️ Поля УЖЕ существуют
    ]
    list_editable = ['newest_product']
    list_per_page = 25

    # 🖼️ Инлайн для изображений
    inlines = [ProductImageInline]

    # 📝 Группировка полей в админке
    fieldsets = (
        ('🛍️ Основная информация', {
            'fields': ('product_sku', 'product_name', 'slug', 'category', 'price')
        }),
        ('🛥️ Размеры лодочного коврика', {
            'fields': ('boat_mat_length', 'boat_mat_width'),
            'description': '📏 Размеры коврика в сантиметрах. Заполняется только для товаров категорий типа "Лодки".',
            'classes': ('collapse',)  # 🆕 Скрываем секцию по умолчанию
        }),
        ('📝 Описание и контент', {
            'fields': ('product_desription',),
            'classes': ('collapse',)
        }),
        ('🔍 SEO оптимизация', {
            'fields': ('page_title', 'meta_description'),  # 🔧 ИСПРАВЛЕНО: убрал meta_title
            'classes': ('collapse',),
        }),
        ('⚙️ Настройки товара', {
            'fields': ('newest_product',)
        }),
    )

    prepopulated_fields = {'slug': ('product_name',)}

    # 🎨 Кастомные методы отображения
    def get_main_image_preview(self, obj):
        """🖼️ Предпросмотр главного изображения"""
        main_image = obj.product_images.filter(is_main=True).first()
        if main_image and main_image.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 5px; border: 2px solid #f39c12;" />',
                main_image.image.url
            )

        first_image = obj.product_images.first()
        if first_image and first_image.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 5px; border: 1px solid #ddd;" />',
                first_image.image.url
            )

        return "📷"

    get_main_image_preview.short_description = "Фото"

    def display_price(self, obj):
        """💰 Форматированная цена"""
        return f"{obj.price:.2f} BYN"

    display_price.short_description = "Цена"

    def get_boat_dimensions(self, obj):
        """🛥️ Размеры лодочного коврика (безопасная версия)"""
        if obj.category and obj.category.category_type == 'boats':
            # 🔍 Проверяем существование полей лодок
            if hasattr(obj, 'boat_mat_length') and hasattr(obj, 'boat_mat_width'):
                if obj.boat_mat_length and obj.boat_mat_width:
                    return f"{obj.boat_mat_length}x{obj.boat_mat_width} см"
                return "Не указано"
            else:
                return "Поля не созданы"  # 🔧 Отладочная информация
        return "-"

    get_boat_dimensions.short_description = "Размеры"

    def has_main_image_status(self, obj):
        """🖼️ Статус главного изображения"""
        if obj.product_images.filter(is_main=True).exists():
            return format_html('<span style="color: green;">✅</span>')
        elif obj.product_images.exists():
            return format_html('<span style="color: orange;">⚠️</span>')
        return format_html('<span style="color: red;">❌</span>')

    has_main_image_status.short_description = "Главное фото"

    def storage_status(self, obj):
        """💾 Статус хранилища изображений"""
        overwrite_count = 0
        total_count = 0

        for img in obj.product_images.all():
            if img.image:
                total_count += 1
                if img.image.storage.__class__.__name__ == 'OverwriteStorage':
                    overwrite_count += 1

        if total_count == 0:
            return "❌"
        elif overwrite_count == total_count:
            return format_html('<span style="color: green;">✅</span>')
        else:
            return format_html('<span style="color: orange;">⚠️</span>')

    storage_status.short_description = "Хранилище"

    # 🎯 Действия
    actions = [
        'mark_as_new',
        'mark_as_regular',
        'set_first_image_as_main',
        'generate_missing_slugs',
        'check_images_storage'
    ]

    def mark_as_new(self, request, queryset):
        """🆕 Отметить как новые товары"""
        queryset.update(newest_product=True)
        self.message_user(request, f"✅ Отмечено как новые: {queryset.count()} товаров")

    def mark_as_regular(self, request, queryset):
        """📦 Убрать отметку 'новый'"""
        queryset.update(newest_product=False)
        self.message_user(request, f"✅ Убрана отметка 'новый': {queryset.count()} товаров")

    def set_first_image_as_main(self, request, queryset):
        """🖼️ Установить первое фото как главное"""
        updated = 0
        for product in queryset:
            first_image = product.product_images.first()
            if first_image:
                product.product_images.update(is_main=False)
                first_image.is_main = True
                first_image.save()
                updated += 1
        self.message_user(request, f"✅ Обновлено главных изображений: {updated}")

    def generate_missing_slugs(self, request, queryset):
        """🔗 Сгенерировать отсутствующие slug"""
        from django.utils.text import slugify
        updated = 0
        for product in queryset.filter(slug__isnull=True):
            product.slug = slugify(product.product_name)
            product.save()
            updated += 1
        self.message_user(request, f"✅ Сгенерировано slug: {updated}")

    def check_images_storage(self, request, queryset):
        """💾 Проверить хранилище изображений"""
        total_images = 0
        overwrite_images = 0
        standard_images = 0

        for product in queryset:
            for img in product.product_images.all():
                if img.image:
                    total_images += 1
                    storage_type = img.image.storage.__class__.__name__
                    if storage_type == 'OverwriteStorage':
                        overwrite_images += 1
                    else:
                        standard_images += 1

        self.message_user(
            request,
            f"💾 Проверка изображений: {total_images} всего, "
            f"{overwrite_images} с OverwriteStorage, {standard_images} со стандартным"
        )

    mark_as_new.short_description = "🆕 Отметить как новые товары"
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

# 🆕 ПРОСТАЯ ГРУППИРОВКА ЛОДОК И АВТОМОБИЛЕЙ
# ============================================

# 🔄 ОТМЕНЯЕМ РЕГИСТРАЦИЮ оригинальных моделей
# Это позволит зарегистрировать Proxy модели без конфликтов
try:
    admin.site.unregister(Category)
    admin.site.unregister(Product)
except admin.sites.NotRegistered:
    # Если модели не были зарегистрированы, ничего страшного
    pass

# Импорт Proxy моделей
from .proxy_models import CategoryBoats, CategoryCars, ProductBoats, ProductCars


@admin.register(CategoryBoats)
class CategoryBoatsAdmin(CategoryAdmin):
    """🛥️ Админка категорий лодок"""

    def get_queryset(self, request):
        """📊 Показываем только категории лодок"""
        return super().get_queryset(request).filter(category_type='boats')

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для лодок"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '🛥️ Категории лодок',
            'subtitle': 'Управление категориями лодочных ковриков'
        })
        return super().changelist_view(request, extra_context)


@admin.register(CategoryCars)
class CategoryCarsAdmin(CategoryAdmin):
    """🚗 Админка категорий автомобилей"""

    def get_queryset(self, request):
        """📊 Показываем только категории автомобилей"""
        return super().get_queryset(request).filter(category_type='cars')

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для автомобилей"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '🚗 Категории автомобилей',
            'subtitle': 'Управление категориями автомобильных ковриков'
        })
        return super().changelist_view(request, extra_context)


@admin.register(ProductBoats)
class ProductBoatsAdmin(ProductAdmin):
    """🛥️ Админка товаров лодок"""

    # 🎯 Показываем поля размеров лодок в списке
    list_display = [
        'get_main_image_preview',
        'product_name',
        'product_sku',
        'category',
        'display_price',
        'get_boat_dimensions',  # 🛥️ Размеры лодочных ковриков важны!
        'has_main_image_status',
        'newest_product'
    ]

    # 🔍 Добавляем поиск по размерам лодок (если поля существуют)
    def get_search_fields(self, request):
        """🔍 Динамические поля поиска для лодок"""
        base_fields = [
            'product_name',
            'product_sku',
            'product_desription'
        ]

        # 🛥️ Добавляем поиск по размерам лодок если поля существуют
        if hasattr(Product, 'boat_mat_length') and hasattr(Product, 'boat_mat_width'):
            base_fields.extend(['boat_mat_length', 'boat_mat_width'])

        return base_fields

    def get_queryset(self, request):
        """📊 Показываем только товары лодок"""
        return super().get_queryset(request).filter(category__category_type='boats')

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для лодок"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '🛥️ Товары лодок',
            'subtitle': 'Управление лодочными ковриками с размерами'
        })
        return super().changelist_view(request, extra_context)


@admin.register(ProductCars)
class ProductCarsAdmin(ProductAdmin):
    """🚗 Админка товаров автомобилей"""

    # 🎯 Убираем поля лодок из списка для автомобилей
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

    # 🔍 Убираем поиск по размерам лодок
    search_fields = [
        'product_name',
        'product_sku',
        'product_desription'
    ]

    # 📝 Скрываем секцию размеров лодок для автомобилей
    fieldsets = (
        ('🛍️ Основная информация', {
            'fields': ('product_sku', 'product_name', 'slug', 'category', 'price')
        }),
        ('📝 Описание и контент', {
            'fields': ('product_desription',),
            'classes': ('collapse',)
        }),
        ('🔍 SEO оптимизация', {
            'fields': ('page_title', 'meta_description'),  # 🔧 ИСПРАВЛЕНО: убрал meta_title
            'classes': ('collapse',),
        }),
        ('⚙️ Настройки товара', {
            'fields': ('newest_product',)
        }),
    )

    def get_queryset(self, request):
        """📊 Показываем только товары автомобилей"""
        return super().get_queryset(request).filter(category__category_type='cars')

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для автомобилей"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '🚗 Товары автомобилей',
            'subtitle': 'Управление автомобильными ковриками'
        })
        return super().changelist_view(request, extra_context)

# 🎯 РЕЗУЛЬТАТ ПРОСТОЙ ГРУППИРОВКИ:
# В админке появятся ТОЛЬКО новые разделы:
# - ЛОДКИ 🛥️
#   ├── Категории лодок
#   └── Товары лодок
# - АВТОМОБИЛИ 🚗
#   ├── Категории автомобилей
#   └── Товары автомобилей
# - ОБЩИЕ СПРАВОЧНИКИ 📋
#   ├── Типы комплектаций
#   └── Цвета
#
# ⚠️ ВАЖНО: Старые разделы "Категории" и "Товары" УДАЛЕНЫ из админки!
# Теперь используются только группированные разделы.