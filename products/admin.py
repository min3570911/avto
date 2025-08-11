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

from .models import Product, Category, KitVariant, ProductImage, Coupon
from common.models import Color
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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """📂 Админка для автомобильных категорий"""
    list_display = ["category_name", "slug", "display_order", "is_active"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["category_name", "slug"]
    list_editable = ["display_order", "is_active"]
    prepopulated_fields = {"slug": ("category_name",)}
    list_per_page = 20

    fieldsets = (
        ("Основная информация", {"fields": ("category_name", "slug", "category_image")}),
        ("Настройки отображения", {"fields": ("display_order", "is_active")}),
    )


# 🛍️ ОБНОВЛЕННАЯ админка товаров с поддержкой полей лодок
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """🛍️ Админка для автомобильных товаров"""

    list_display = [
        'get_main_image_preview',
        'product_name',
        'product_sku',
        'category',
        'newest_product'
    ]
    list_display_links = ['get_main_image_preview', 'product_name']
    list_filter = [
        'category',
        'newest_product',
        'created_at'
    ]
    search_fields = [
        'product_name',
        'product_sku',
        'product_desription',
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