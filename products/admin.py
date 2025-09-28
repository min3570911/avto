# 📁 products/admin.py - ОБНОВЛЕННАЯ версия с поддержкой лодок
# 🛥️ ДОБАВЛЕНО: Поля category_type, parent для Category + boat_mat_length, boat_mat_width для Product
# ✅ СОХРАНЕНО: Вся существующая функциональность SEO, экспорта, валидации без изменений

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


# 🖼️ СУЩЕСТВУЮЩАЯ инлайн админка для изображений товаров (без изменений)
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
        return "❌ Файл не загружен"

    storage_info.short_description = "Хранилище"


# 🆕 ОБНОВЛЕННАЯ форма для CategoryAdmin с поддержкой лодок
class CategoryAdminForm(forms.ModelForm):
    """📝 Кастомная форма для категорий с валидацией SEO и иерархии лодок"""

    class Meta:
        model = Category
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🛥️ НОВОЕ: Фильтрация родительских категорий по типу
        if 'parent' in self.fields:
            # Если редактируем существующую категорию
            if self.instance and self.instance.pk:
                category_type = self.instance.category_type
                # Показываем только категории того же типа, исключая себя
                self.fields['parent'].queryset = Category.objects.filter(
                    category_type=category_type
                ).exclude(pk=self.instance.pk)
            else:
                # При создании новой категории показываем все
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
        """🛥️ НОВОЕ: Валидация иерархии лодок"""
        cleaned_data = super().clean()
        category_type = cleaned_data.get('category_type')
        parent = cleaned_data.get('parent')

        # Проверяем соответствие типов родителя и ребенка
        if parent and parent.category_type != category_type:
            raise ValidationError({
                'parent': f"Родительская категория должна иметь тот же тип: {category_type}"
            })

        return cleaned_data


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """📂 Админка категорий товаров с SEO, предпросмотром, валидацией и поддержкой лодок"""

    form = CategoryAdminForm

    # 📊 Список с новыми полями для лодок
    list_display = [
        "get_category_hierarchy",  # 🆕 НОВОЕ: Показ иерархии с иконками
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
        "category_type",  # 🆕 НОВОЕ: Фильтр по типу (авто/лодки)
        "is_active",
        "created_at",
        "updated_at"
    ]
    search_fields = [
        "category_name",
        "slug",
        "category_sku",
        "meta_title",
        "parent__category_name"  # 🆕 НОВОЕ: Поиск по родительской категории
    ]
    list_editable = ["display_order", "is_active", "category_sku"]
    prepopulated_fields = {"slug": ("category_name",)}
    list_per_page = 20

    # 🗂️ Секции формы с новыми полями
    fieldsets = (
        ("📋 Основная информация", {
            "fields": (
                "category_name",
                "category_sku",
                "slug",
                ("category_type", "parent"),  # 🆕 НОВОЕ: Поля лодок в одной строке
                "category_image",
                "image_preview",
                "storage_info",
            ),
            "description": "🏷️ Базовая информация о категории. Для лодок укажите тип и родительскую категорию.",
        }),
        ("📝 Контент категории", {
            "fields": ("description", "additional_content"),
            "classes": ("wide",),
            "description": "✍️ Текстовое содержимое страницы",
        }),
        ("🔍 SEO-настройки", {
            "fields": (
                "page_title",
                ("meta_title", "meta_title_length"),
                ("meta_description", "meta_description_length"),
                "google_preview",
            ),
            "description": "🎯 Оптимизация для поисковых систем",
        }),
        ("⚙️ Настройки отображения", {
            "fields": ("display_order", "is_active"),
            "classes": ("collapse",),
            "description": "🔧 Порядок и видимость",
        }),
        ("📊 Служебная информация", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = (
        'image_preview', 'storage_info', 'meta_title_length',
        'meta_description_length', 'google_preview', 'created_at', 'updated_at'
    )

    # 🆕 НОВЫЕ МЕТОДЫ для поддержки лодок
    def get_category_hierarchy(self, obj):
        """🛥️ Отображение иерархии с иконками типа"""
        type_icon = "🛥️" if obj.category_type == 'boats' else "🚗"

        if obj.parent:
            hierarchy = f" → {obj.category_name}"
            return format_html(
                '<span title="Тип: {}">{}</span> <span style="color: #666;">{}</span>',
                obj.get_category_type_display(),
                type_icon,
                hierarchy
            )
        else:
            return format_html(
                '<span title="Тип: {}"><strong>{} {}</strong></span>',
                obj.get_category_type_display(),
                type_icon,
                obj.category_name
            )

    get_category_hierarchy.short_description = "Категория"
    get_category_hierarchy.admin_order_field = "category_name"

    # ВСЕ СУЩЕСТВУЮЩИЕ МЕТОДЫ СОХРАНЕНЫ БЕЗ ИЗМЕНЕНИЙ
    def get_products_count(self, obj):
        """📊 Количество товаров в категории"""
        count = obj.products.count()
        if count > 0:
            url = reverse('admin:products_product_changelist') + f'?category__id__exact={obj.uid}'
            return format_html('<a href="{}" title="Перейти к товарам">{} товаров</a>', url, count)
        return "0 товаров"

    get_products_count.short_description = "Товары"

    def image_preview_small(self, obj):
        """🖼️ Миниатюра изображения категории"""
        if obj.category_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" title="{}">',
                obj.category_image.url,
                obj.category_name
            )
        return "❌"

    image_preview_small.short_description = "Фото"

    def storage_status(self, obj):
        """💾 Статус хранилища изображения"""
        if obj.category_image:
            storage_type = obj.category_image.storage.__class__.__name__
            if storage_type == 'OverwriteStorage':
                return format_html('<span style="color: green; font-weight: bold;">✅</span>')
            else:
                return format_html('<span style="color: orange;">⚠️</span>')
        return "❌"

    storage_status.short_description = "Хранилище"

    def seo_status(self, obj):
        """🔍 Статус SEO оптимизации"""
        score = 0
        if obj.meta_title:
            score += 1
        if obj.meta_description:
            score += 1
        if obj.page_title:
            score += 1

        if score == 3:
            return format_html('<span style="color: green;">✅ 100%</span>')
        elif score == 2:
            return format_html('<span style="color: orange;">⚠️ 67%</span>')
        elif score == 1:
            return format_html('<span style="color: red;">❌ 33%</span>')
        return format_html('<span style="color: red;">❌ 0%</span>')

    seo_status.short_description = "SEO"

    def image_preview(self, obj):
        """🖼️ Предпросмотр изображения в форме"""
        if obj.category_image:
            return format_html(
                '<div style="margin: 10px 0;">'
                '<img src="{}" style="max-width: 300px; max-height: 200px; object-fit: contain; border: 1px solid #ddd; border-radius: 5px;">'
                '<br><small>Размер файла: ~{:.1f} KB</small>'
                '</div>',
                obj.category_image.url,
                obj.category_image.size / 1024 if hasattr(obj.category_image, 'size') else 0
            )
        return "📷 Изображение не загружено"

    image_preview.short_description = "Предпросмотр"

    def storage_info(self, obj):
        """💾 Детальная информация о хранилище"""
        if obj.category_image:
            storage_type = obj.category_image.storage.__class__.__name__
            file_name = obj.category_image.name.split('/')[-1]
            if storage_type == 'OverwriteStorage':
                return format_html(
                    '<div style="padding: 8px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;">'
                    '<strong>✅ OverwriteStorage</strong><br>'
                    '<small>Файл: {}</small>'
                    '</div>',
                    file_name
                )
            else:
                return format_html(
                    '<div style="padding: 8px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px;">'
                    '<strong>⚠️ {}</strong><br>'
                    '<small>Файл: {}</small>'
                    '</div>',
                    storage_type,
                    file_name
                )
        return "❌ Файл не загружен"

    storage_info.short_description = "Информация о хранилище"

    def meta_title_length(self, obj):
        """📏 Длина мета-заголовка"""
        if obj.meta_title:
            length = len(obj.meta_title)
            color = "green" if length <= 60 else "red"
            return format_html('<span style="color: {};">{}/60</span>', color, length)
        return "0/60"

    meta_title_length.short_description = "Длина"

    def meta_description_length(self, obj):
        """📏 Длина мета-описания"""
        if obj.meta_description:
            length = len(obj.meta_description)
            color = "green" if length <= 160 else "red"
            return format_html('<span style="color: {};">{}/160</span>', color, length)
        return "0/160"

    meta_description_length.short_description = "Длина"

    def google_preview(self, obj):
        """🔍 Предпросмотр в стиле Google"""
        title = obj.meta_title or obj.page_title or obj.category_name
        description = obj.meta_description or "Описание не заполнено"

        return format_html(
            '<div style="border: 1px solid #dadce0; border-radius: 8px; padding: 12px; max-width: 500px; font-family: Arial, sans-serif;">'
            '<div style="color: #1a0dab; font-size: 18px; line-height: 1.3; margin-bottom: 4px;">{}</div>'
            '<div style="color: #006621; font-size: 14px; margin-bottom: 4px;">https://site.by/category/{}/</div>'
            '<div style="color: #545454; font-size: 14px; line-height: 1.4;">{}</div>'
            '</div>',
            title,
            obj.slug or 'category-slug',
            description
        )

    google_preview.short_description = "Предпросмотр Google"

    # СУЩЕСТВУЮЩИЕ ДЕЙСТВИЯ СОХРАНЕНЫ
    actions = ['optimize_seo', 'check_storage']

    def optimize_seo(self, request, queryset):
        """🔍 Автоматическая SEO оптимизация категорий"""
        optimized = 0
        for category in queryset:
            changed = False
            if not category.meta_title:
                category.meta_title = f"ЭВА коврики {category.category_name} - купить в интернет-магазине"[:60]
                changed = True
            if not category.meta_description:
                category.meta_description = (f"Качественные ЭВА коврики для {category.category_name}. "
                                             f"Доставка по РБ. Гарантия качества."
                                             )[:160]
                changed = True
            if changed:
                category.save()
                optimized += 1
        self.message_user(request, f"🔍 SEO оптимизировано для {optimized} категорий")

    optimize_seo.short_description = "🔍 Оптимизировать SEO"

    def check_storage(self, request, queryset):
        """🆕 НОВОЕ ДЕЙСТВИЕ: Проверка типа хранилища"""
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


# 🛍️ ОБНОВЛЕННАЯ админка товаров с поддержкой полей лодок
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """🛍️ Админка для товаров с поддержкой импорта, экспорта, информацией о хранилище и полями лодок"""

    list_display = [
        'get_main_image_preview',
        'product_name',
        'product_sku',
        'category',
        'display_price',
        'get_boat_dimensions',  # 🆕 НОВОЕ: Размеры лодочных ковриков
        'has_main_image_status',
        'storage_status',
        'newest_product'
    ]
    list_display_links = ['get_main_image_preview', 'product_name']
    list_filter = [
        'category__category_type',  # 🆕 НОВОЕ: Фильтр по типу категории (авто/лодки)
        'category',
        'newest_product',
        'created_at'
    ]
    search_fields = [
        'product_name',
        'product_sku',
        'product_desription',
        'boat_mat_length',  # 🆕 НОВОЕ: Поиск по размерам лодок
        'boat_mat_width'  # 🆕 НОВОЕ: Поиск по размерам лодок
    ]
    list_editable = ['newest_product']
    list_per_page = 25

    # 🖼️ Инлайн для изображений с поддержкой OverwriteStorage
    inlines = [ProductImageInline]

    # 📝 Группировка полей в админке с новой секцией для лодок
    fieldsets = (
        ('🛍️ Основная информация', {
            'fields': ('product_sku', 'product_name', 'slug', 'category', 'price')
        }),
        ('🛥️ Размеры лодочного коврика', {  # 🆕 НОВАЯ СЕКЦИЯ
            'fields': ('boat_mat_length', 'boat_mat_width'),
            'description': '📏 Размеры коврика в сантиметрах. Заполняется только для товаров категорий типа "Лодки".',
            'classes': ('collapse',),  # Сворачиваемая секция
        }),
        ('📝 Описание товара', {
            'fields': ('product_desription',),
            'classes': ('wide',)
        }),
        ('🔍 SEO-настройки', {
            'fields': ('page_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('⚙️ Настройки отображения', {
            'fields': ('newest_product',)
        }),
        ('📊 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    # 🆕 НОВЫЙ МЕТОД для отображения размеров лодок
    def get_boat_dimensions(self, obj):
        """📏 Отображение размеров для лодочных товаров"""
        if hasattr(obj.category, 'category_type') and obj.category.category_type == 'boats':
            if obj.boat_mat_length and obj.boat_mat_width:
                return format_html(
                    '<span style="background: #e3f2fd; padding: 2px 6px; border-radius: 3px; font-size: 12px;">'
                    '📏 {}×{}см'
                    '</span>',
                    obj.boat_mat_length,
                    obj.boat_mat_width
                )
            else:
                return format_html('<span style="color: orange;">⚠️ Не указаны</span>')
        return "-"  # Прочерк для автомобилей

    get_boat_dimensions.short_description = "Размеры коврика"
    get_boat_dimensions.admin_order_field = "boat_mat_length"

    # ВСЕ СУЩЕСТВУЮЩИЕ МЕТОДЫ СОХРАНЕНЫ БЕЗ ИЗМЕНЕНИЙ
    def get_main_image_preview(self, obj):
        """🖼️ Предпросмотр главного изображения товара"""
        main_image = obj.product_images.filter(is_main=True).first()
        if main_image and main_image.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 5px; border: 2px solid #f39c12;" title="{}">',
                main_image.image.url,
                obj.product_name
            )

        # Если нет главного, берем первое доступное
        first_image = obj.product_images.first()
        if first_image and first_image.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 5px; border: 1px solid #ddd;" title="{}">',
                first_image.image.url,
                obj.product_name
            )

        return "📷"

    get_main_image_preview.short_description = "Фото"

    def display_price(self, obj):
        """💰 Отображение цены в удобном формате"""
        if obj.price:
            return f"{obj.price:,} руб.".replace(',', ' ')
        return "Цена не указана"

    display_price.short_description = "Цена"
    display_price.admin_order_field = "price"

    def has_main_image_status(self, obj):
        """🖼️ Статус наличия главного изображения"""
        main_image = obj.product_images.filter(is_main=True).first()
        if main_image:
            return format_html('<span style="color: green;">✅</span>')
        elif obj.product_images.exists():
            return format_html(
                '<span style="color: orange;" title="Есть изображения, но не назначено главное">⚠️</span>')
        return format_html('<span style="color: red;" title="Нет изображений">❌</span>')

    has_main_image_status.short_description = "Главное фото"

    def storage_status(self, obj):
        """💾 Общий статус хранилища для всех изображений товара"""
        images = obj.product_images.all()
        if not images:
            return "❌"

        overwrite_count = 0
        total_count = len(images)

        for image in images:
            if image.image:
                storage_type = image.image.storage.__class__.__name__
                if storage_type == 'OverwriteStorage':
                    overwrite_count += 1

        if overwrite_count == total_count:
            return format_html('<span style="color: green;">✅ {}/{}</span>', overwrite_count, total_count)
        elif overwrite_count > 0:
            return format_html('<span style="color: orange;">⚠️ {}/{}</span>', overwrite_count, total_count)
        return format_html('<span style="color: red;">❌ 0/{}</span>', total_count)

    storage_status.short_description = "Хранилище"

    # СУЩЕСТВУЮЩИЕ ДЕЙСТВИЯ СОХРАНЕНЫ
    actions = [
        'mark_as_new', 'mark_as_regular', 'set_first_image_as_main',
        'generate_missing_slugs', 'check_images_storage'
    ]

    def mark_as_new(self, request, queryset):
        """🆕 Отметить выбранные товары как новые"""
        updated = queryset.update(newest_product=True)
        self.message_user(request, f"✅ Отмечено как новые: {updated} товаров")

    def mark_as_regular(self, request, queryset):
        """📦 Убрать отметку 'новый товар' с выбранных товаров"""
        updated = queryset.update(newest_product=False)
        self.message_user(request, f"✅ Убрана отметка 'новый': {updated} товаров")

    def set_first_image_as_main(self, request, queryset):
        """🖼️ Установить первое изображение как главное для товаров без главного фото"""
        updated = 0
        for product in queryset:
            if not product.product_images.filter(is_main=True).exists():
                first_image = product.product_images.first()
                if first_image:
                    # Сбрасываем все главные фото для товара
                    product.product_images.update(is_main=False)
                    # Устанавливаем первое как главное
                    first_image.is_main = True
                    first_image.save()
                    updated += 1
        self.message_user(request, f"🖼️ Установлено главных изображений: {updated}")

    def generate_missing_slugs(self, request, queryset):
        """🔗 Генерация slug для товаров без него"""
        updated = 0
        for product in queryset.filter(slug__isnull=True):
            product.save()  # save() метод автоматически генерирует slug
            updated += 1
        self.message_user(request, f"🔗 Сгенерировано slug: {updated}")

    def check_images_storage(self, request, queryset):
        """💾 Проверка типа хранилища для изображений товаров"""
        total_images = 0
        overwrite_images = 0
        standard_images = 0

        for product in queryset:
            for image in product.product_images.all():
                total_images += 1
                storage_type = image.image.storage.__class__.__name__
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

    # 🆕 ДОБАВЛЯЕМ КОНТЕКСТ ЭКСПОРТА В АДМИНКУ ТОВАРОВ
    def changelist_view(self, request, extra_context=None):
        """🎨 Переопределяем представление списка для добавления контекста экспорта"""
        # 📊 Получаем контекст экспорта
        export_context = get_export_context()

        # 🎨 Добавляем контекст экспорта (кнопка добавляется через шаблон)
        extra_context = extra_context or {}
        extra_context.update({
            'export_context': export_context,
            'has_export_permission': request.user.is_staff,
        })

        return super().changelist_view(request, extra_context=extra_context)


# 🔧 ВСЕ ОСТАЛЬНЫЕ АДМИНКИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ

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
            'fields': ('name', 'hex_code', 'color_type', 'display_order')
        }),
        ('🖼️ Изображения', {
            'fields': ('carpet_image', 'border_image', 'carpet_preview', 'border_preview'),
            'description': '📸 Загрузите изображения цветов для отображения на сайте'
        }),
        ('⚙️ Настройки', {
            'fields': ('is_available',)
        }),
    )

    readonly_fields = ('carpet_preview', 'border_preview')

    def carpet_preview(self, obj):
        """🧽 Предпросмотр изображения коврика"""
        if obj.carpet_image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: contain; border-radius: 5px;">',
                obj.carpet_image.url
            )
        return "Изображение не загружено"

    carpet_preview.short_description = "Превью коврика"

    def border_preview(self, obj):
        """🖼️ Предпросмотр изображения окантовки"""
        if obj.border_image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: contain; border-radius: 5px;">',
                obj.border_image.url
            )
        return "Изображение не загружено"

    border_preview.short_description = "Превью окантовки"


# 🎨 Настройки админки
admin.site.site_header = "🛒 Автоковрики - Админ-панель (Авто + Лодки)"  # 🆕 ОБНОВЛЕНО
admin.site.site_title = "Автоковрики"
admin.site.index_title = "Управление интернет-магазином автомобильных и лодочных ковриков"  # 🆕 ОБНОВЛЕНО

# 🔧 КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# 🛥️ ДОБАВЛЕНО ДЛЯ КАТЕГОРИЙ:
# ✅ ПОЛЯ: category_type, parent в fieldsets
# ✅ МЕТОДЫ: get_category_hierarchy() - показ иерархии с иконками
# ✅ ФИЛЬТРЫ: category_type в list_filter
# ✅ ПОИСК: parent__category_name в search_fields
# ✅ ВАЛИДАЦИЯ: проверка соответствия типов в CategoryAdminForm.clean()
#
# 🛥️ ДОБАВЛЕНО ДЛЯ ТОВАРОВ:
# ✅ СЕКЦИЯ: "Размеры лодочного коврика" в fieldsets
# ✅ ПОЛЯ: boat_mat_length, boat_mat_width
# ✅ МЕТОДЫ: get_boat_dimensions() - отображение размеров только для лодок
# ✅ ФИЛЬТРЫ: category__category_type в list_filter
# ✅ ПОИСК: размеры лодок в search_fields
#
# 🔧 СОХРАНЕНО БЕЗ ИЗМЕНЕНИЙ:
# ✅ Все существующие методы отображения
# ✅ SEO функциональность и валидация
# ✅ Система экспорта товаров
# ✅ Обработка изображений с OverwriteStorage
# ✅ Все остальные админки (Color, KitVariant) остались
#
# ❌ УБРАНО: Дублирующие админки (Coupon, ProductReview, Wishlist)
#    - Эти админки уже зарегистрированы в проекте ранее
#    - Оставлена только новая функциональность для лодок
#
# 🎯 РЕЗУЛЬТАТ:
# - Админка поддерживает создание и редактирование лодочных категорий и товаров
# - Автоматическое условное отображение полей размеров только для лодок
# - Сохранена полная совместимость с существующими автомобильными товарами
# - Умная фильтрация и поиск по типам товаров
# - Валидация иерархии категорий лодок
# - Никаких конфликтов с существующими админками


# 📝 НОВАЯ АДМИНКА: AutoCatalogDescription (синглтон)
@admin.register(AutoCatalogDescription)
class AutoCatalogDescriptionAdmin(admin.ModelAdmin):
    """📝 Админка для описания каталога автоковриков (только один экземпляр)"""

    # 🚫 Синглтон логика в админке
    def has_add_permission(self, request):
        """🚫 Запретить создание новых записей, если уже есть описание"""
        return not AutoCatalogDescription.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """⚠️ Разрешить удаление (чтобы можно было пересоздать при необходимости)"""
        return True

    def changelist_view(self, request, extra_context=None):
        """📝 Если нет записи, перенаправляем на создание"""
        if not AutoCatalogDescription.objects.exists():
            return self.add_view(request)
        return super().changelist_view(request, extra_context)

    # 🎨 Группировка полей в админке
    fieldsets = (
        ('📝 Описание каталога автоковриков', {
            'fields': ('title', 'description'),
            'description': 'Заголовок и основное описание каталога автоковриков'
        }),
        ('🎬 Дополнительный контент', {
            'fields': ('additional_content',),
            'classes': ('collapse',),
            'description': 'YouTube видео или дополнительный HTML контент'
        }),
        ('🔍 SEO', {
            'fields': ('meta_description',),
            'classes': ('collapse',),
            'description': 'Мета-описание для поисковых систем'
        }),
    )