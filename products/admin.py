# 📁 products/admin.py - ОБНОВЛЕННАЯ ВЕРСИЯ с импортом и главными изображениями
# 🛍️ Админка для системы интернет-магазина автоковриков

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


# 🖼️ УЛУЧШЕННАЯ инлайн админка для изображений товаров
class ProductImageInline(admin.TabularInline):
    """🖼️ Инлайн админка для изображений товаров с поддержкой главного изображения"""

    model = ProductImage
    verbose_name = "Изображение товара"
    verbose_name_plural = "Изображения товара"
    extra = 1  # 📸 Одна пустая форма для добавления

    # 🎯 Поля для отображения и редактирования
    fields = ('image', 'img_preview', 'is_main')
    readonly_fields = ('img_preview',)

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

    # 🎯 Кастомизация формы для радиокнопок главного изображения
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'is_main':
            kwargs['widget'] = forms.RadioSelect(choices=[(True, 'Главное'), (False, 'Обычное')])
        return super().formfield_for_dbfield(db_field, request, **kwargs)


# 📂 Расширенная админка категорий (без изменений из оригинала)
class CategoryAdminForm(forms.ModelForm):
    """📝 Форма с валидацией SEO-полей категории"""

    class Meta:
        model = Category
        fields = "__all__"

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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """📂 Админка категорий товаров с SEO, предпросмотром и валидацией"""

    form = CategoryAdminForm

    # 📊 Список
    list_display = [
        "category_name",
        "category_sku",
        "slug",
        "get_products_count",
        "display_order",
        "is_active",
        "image_preview_small",
        "seo_status",
    ]
    list_filter = ["is_active", "created_at", "updated_at"]
    search_fields = ["category_name", "slug", "category_sku", "meta_title"]
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
                "category_image",
                "image_preview",
            ),
            "description": "🏷️ Базовая информация о категории",
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
            "description": "🕐 Даты создания и обновления",
        }),
    )

    # 🔒 Только-чтение
    readonly_fields = [
        "image_preview",
        "meta_title_length",
        "meta_description_length",
        "google_preview",
        "created_at",
        "updated_at",
    ]

    # ---------- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ----------

    def get_products_count(self, obj):
        count = obj.products.count()
        if count == 0:
            return mark_safe('<span style="color:red;">🚫 Нет товаров</span>')
        if count < 5:
            return mark_safe(f'<span style="color:orange;">📦 {count} тов.</span>')
        return mark_safe(f'<span style="color:green;">📦 {count} тов.</span>')

    get_products_count.short_description = "Товары"

    def image_preview(self, obj):
        if obj.category_image:
            return mark_safe(
                f'<img src="{obj.category_image.url}" '
                f'style="max-height:200px;max-width:400px;object-fit:contain;'
                f'border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);"/>'
            )
        return "📷 Изображение не загружено"

    image_preview.short_description = "Превью"

    def image_preview_small(self, obj):
        if obj.category_image:
            return mark_safe(
                f'<img src="{obj.category_image.url}" '
                f'style="height:40px;width:40px;object-fit:cover;border-radius:4px;"/>'
            )
        return "—"

    image_preview_small.short_description = "Фото"

    def meta_title_length(self, obj):
        if obj.meta_title:
            length = len(obj.meta_title)
            color = "green" if length <= 60 else "red"
            return mark_safe(f'<span style="color:{color};">{length}/60</span>')
        return "—"

    meta_title_length.short_description = "Длина"

    def meta_description_length(self, obj):
        if obj.meta_description:
            length = len(obj.meta_description)
            color = "green" if length <= 160 else "red"
            return mark_safe(f'<span style="color:{color};">{length}/160</span>')
        return "—"

    meta_description_length.short_description = "Длина"

    def seo_status(self, obj):
        has_title = bool(obj.meta_title)
        has_desc = bool(obj.meta_description)
        has_image = bool(obj.category_image)
        if has_title and has_desc and has_image:
            return mark_safe('<span style="color:green;">✅ Полная</span>')
        if has_title or has_desc:
            return mark_safe('<span style="color:orange;">⚠️ Частичная</span>')
        return mark_safe('<span style="color:red;">❌ Нет</span>')

    seo_status.short_description = "SEO"

    def google_preview(self, obj):
        title = obj.get_meta_title()[:60]
        description = obj.get_meta_description()[:160]
        url = f"example.com/products/category/{obj.slug}/"
        return mark_safe(f"""
        <div style="font-family:Arial;max-width:600px;border:1px solid #ddd;
                    padding:15px;border-radius:8px;background:#f9f9f9;">
            <div style="color:#1a0dab;font-size:18px;margin-bottom:3px;">{title}</div>
            <div style="color:#006621;font-size:14px;margin-bottom:5px;">{url}</div>
            <div style="color:#545454;font-size:13px;line-height:1.4;">{description}</div>
        </div>""")

    google_preview.short_description = "Google preview"

    # 🎯 Массовые действия
    actions = ["activate_categories", "deactivate_categories", "optimize_seo"]

    def activate_categories(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"✅ Активировано: {updated}")

    activate_categories.short_description = "✅ Активировать"

    def deactivate_categories(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"🚫 Деактивировано: {updated}")

    deactivate_categories.short_description = "🚫 Деактивировать"

    def optimize_seo(self, request, queryset):
        optimized = 0
        for category in queryset:
            changed = False
            if not category.meta_title:
                category.meta_title = (
                                          f"{category.category_name} – купить в интернет-магазине"
                                      )[:60]
                changed = True
            if not category.meta_description:
                category.meta_description = (
                                                f"Большой выбор {category.category_name.lower()}. "
                                                f"Доставка по РБ. Гарантия качества."
                                            )[:160]
                changed = True
            if changed:
                category.save()
                optimized += 1
        self.message_user(request, f"🔍 SEO оптимизировано для {optimized} категорий")

    optimize_seo.short_description = "🔍 Оптимизировать SEO"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("products")


# 🛍️ ОБНОВЛЕННАЯ админка товаров с импортом и главными изображениями
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """🛍️ Админка для товаров с поддержкой импорта и главных изображений"""

    list_display = [
        'get_main_image_preview',  # 🆕 Превью главного изображения
        'product_name',
        'product_sku',  # 🆕 SKU товара
        'category',
        'display_price',
        'has_main_image_status',  # 🆕 Статус главного изображения
        'newest_product'
    ]
    list_filter = ['category', 'newest_product', 'created_at']
    search_fields = ['product_name', 'product_sku', 'product_desription']
    list_editable = ['newest_product']
    list_per_page = 25

    # 🖼️ Инлайн для изображений с поддержкой главного изображения
    inlines = [ProductImageInline]

    # 📝 Группировка полей в админке
    fieldsets = (
        ('🛍️ Основная информация', {
            'fields': ('product_sku', 'product_name', 'slug', 'category', 'price')
        }),
        ('📝 Описание товара', {
            'fields': ('product_desription',),
            'description': '🎨 Подробное описание товара для покупателей',
            'classes': ('wide',)
        }),
        ('🔍 SEO настройки', {
            'fields': ('page_title', 'meta_description'),
            'description': '🎯 Настройки для поисковых систем',
            'classes': ('collapse',)
        }),
        ('⚙️ Настройки', {
            'fields': ('newest_product',),
            'classes': ('collapse',)
        }),
    )

    # 🔒 Поля только для чтения
    readonly_fields = ['get_main_image_display']

    # 🆕 НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ГЛАВНЫМИ ИЗОБРАЖЕНИЯМИ

    def get_main_image_preview(self, obj):
        """🖼️ Превью главного изображения в списке товаров"""
        main_image = obj.get_main_image()
        if main_image and main_image.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 5px; border: 2px solid #f39c12;">',
                main_image.image.url
            )
        return format_html(
            '<div style="width: 60px; height: 60px; background: #f8f9fa; border: 1px dashed #ddd; border-radius: 5px; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #6c757d;">📷<br>Нет</div>'
        )

    get_main_image_preview.short_description = "Фото"
    get_main_image_preview.admin_order_field = 'product_images'

    def has_main_image_status(self, obj):
        """✅ Статус наличия главного изображения"""
        if obj.has_main_image():
            return mark_safe('<span style="color: green;">✅ Есть</span>')
        else:
            return mark_safe('<span style="color: red;">❌ Нет</span>')

    has_main_image_status.short_description = "Главное фото"
    has_main_image_status.admin_order_field = 'product_images'

    def get_main_image_display(self, obj):
        """🖼️ Отображение главного изображения в форме редактирования"""
        main_image = obj.get_main_image()
        if main_image and main_image.image:
            return format_html(
                '<div style="text-align: center; margin: 10px 0;">'
                '<p><strong>🌟 Главное изображение:</strong></p>'
                '<img src="{}" style="max-width: 300px; max-height: 300px; object-fit: contain; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'
                '</div>',
                main_image.image.url
            )
        return format_html(
            '<div style="text-align: center; margin: 10px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">'
            '<p style="color: #6c757d;">📷 Главное изображение не установлено</p>'
            '<small>Добавьте изображения ниже и отметьте одно как главное</small>'
            '</div>'
        )

    get_main_image_display.short_description = "Главное изображение"

    # 🆕 КНОПКА ИМПОРТА В АДМИНКЕ
    def changelist_view(self, request, extra_context=None):
        """📊 Переопределяем представление списка для добавления кнопки импорта"""
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        extra_context['import_url'] = reverse('admin:products_import')
        return super().changelist_view(request, extra_context)

    # 🎯 Массовые действия для товаров
    actions = ['mark_as_new', 'mark_as_regular', 'set_first_image_as_main', 'generate_missing_slugs']

    def mark_as_new(self, request, queryset):
        """🆕 Отметить как новые товары"""
        updated = queryset.update(newest_product=True)
        self.message_user(request, f"✅ Отмечено как новые: {updated} товаров")

    def mark_as_regular(self, request, queryset):
        """📦 Убрать отметку 'новый товар'"""
        updated = queryset.update(newest_product=False)
        self.message_user(request, f"✅ Убрана отметка 'новый': {updated} товаров")

    def set_first_image_as_main(self, request, queryset):
        """🖼️ Установить первое изображение как главное"""
        updated = 0
        for product in queryset:
            if not product.has_main_image():
                first_image = product.product_images.first()
                if first_image:
                    first_image.is_main = True
                    first_image.save()
                    updated += 1
        self.message_user(request, f"🖼️ Установлено главных изображений: {updated}")

    def generate_missing_slugs(self, request, queryset):
        """🔗 Генерация отсутствующих slug"""
        updated = 0
        for product in queryset:
            if not product.slug:
                from django.utils.text import slugify
                product.slug = slugify(product.product_name)
                product.save()
                updated += 1
        self.message_user(request, f"🔗 Сгенерировано slug: {updated}")

    mark_as_new.short_description = "🆕 Отметить как новые товары"
    mark_as_regular.short_description = "📦 Убрать отметку 'новый'"
    set_first_image_as_main.short_description = "🖼️ Установить первое фото как главное"
    generate_missing_slugs.short_description = "🔗 Сгенерировать отсутствующие slug"

    # 🔧 КАСТОМНЫЕ URL для импорта
    def get_urls(self):
        """🔗 Добавляем URL для импорта"""
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_view), name='products_import'),
        ]
        return custom_urls + urls

    def import_view(self, request):
        """📊 Представление для импорта товаров"""
        # Перенаправляем на отдельное приложение импорта
        from django.urls import reverse
        return HttpResponseRedirect(reverse('products:import_products'))


# 🔧 ОСТАЛЬНЫЕ АДМИНКИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ

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
            'description': '📸 Загрузите изображения для визуализации цвета'
        }),
        ('✅ Доступность', {
            'fields': ('is_available',),
            'description': '🔓 Если материал недоступен, отключите этот флаг'
        }),
    )

    readonly_fields = ['carpet_preview', 'border_preview']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """🎫 Админка для купонов и скидок"""
    list_display = ['coupon_code', 'discount_amount', 'minimum_amount', 'is_expired', 'get_status']
    list_filter = ['is_expired', 'created_at']
    list_editable = ['is_expired', 'discount_amount', 'minimum_amount']
    search_fields = ['coupon_code']

    def get_status(self, obj):
        """🔍 Статус купона с цветовой индикацией"""
        if obj.is_expired:
            return mark_safe('<span style="color: red;">❌ Неактивен</span>')
        else:
            return mark_safe('<span style="color: green;">✅ Активен</span>')

    get_status.short_description = "Статус"


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """📝 Админка для отзывов о товарах"""
    list_display = ['product', 'user', 'stars', 'get_content_preview', 'date_added', 'get_likes_info']
    list_filter = ['stars', 'date_added']
    search_fields = ['content', 'user__username', 'product__product_name']
    readonly_fields = ['likes', 'dislikes', 'date_added']

    def get_content_preview(self, obj):
        """📝 Предпросмотр содержания отзыва"""
        if obj.content:
            preview = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
            return preview
        return "📝 Без комментария"

    def get_likes_info(self, obj):
        """👍 Информация о лайках/дизлайках"""
        likes = obj.like_count()
        dislikes = obj.dislike_count()
        return f"👍 {likes} / 👎 {dislikes}"

    get_content_preview.short_description = "Комментарий"
    get_likes_info.short_description = "Реакции"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """❤️ Админка для списка избранных товаров"""
    list_display = ['user', 'product', 'kit_variant', 'get_colors_info', 'has_podpyatnik', 'added_on']
    list_filter = ['added_on', 'has_podpyatnik', 'kit_variant']
    search_fields = ['user__username', 'product__product_name']
    readonly_fields = ['added_on', 'get_total_price']

    def get_colors_info(self, obj):
        """🎨 Информация о выбранных цветах"""
        colors = []
        if obj.carpet_color:
            colors.append(f"🧽 {obj.carpet_color.name}")
        if obj.border_color:
            colors.append(f"🖼️ {obj.border_color.name}")
        return " | ".join(colors) if colors else "🎨 Цвета не выбраны"

    get_colors_info.short_description = "Цвета"

    fieldsets = (
        ('❤️ Основная информация', {
            'fields': ('user', 'product', 'kit_variant', 'added_on')
        }),
        ('🎨 Цветовые настройки', {
            'fields': ('carpet_color', 'border_color'),
            'classes': ('collapse',)
        }),
        ('🔧 Дополнительные опции', {
            'fields': ('has_podpyatnik', 'get_total_price'),
            'classes': ('collapse',)
        }),
    )


# 🎨 Настройки админки
admin.site.site_header = "🛒 Автоковрики - Админ-панель"
admin.site.site_title = "Автоковрики"
admin.site.index_title = "Управление интернет-магазином"

# 🔧 ИЗМЕНЕНИЯ:
# ✅ ДОБАВЛЕНО: Поддержка главных изображений в ProductImageInline
# ✅ ДОБАВЛЕНО: Методы для работы с главными изображениями в ProductAdmin
# ✅ ДОБАВЛЕНО: Кнопка импорта в админке товаров
# ✅ ДОБАВЛЕНО: Новые поля product_sku, page_title, meta_description в fieldsets
# ✅ ДОБАВЛЕНО: Массовые действия для установки главных изображений
# ✅ СОХРАНЕНО: Вся существующая функциональность админки