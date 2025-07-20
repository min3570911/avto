# 📁 products/proxy_admin.py - Новые админки с бизнес-группировкой
# 🎯 ЦЕЛЬ: Создать удобные группы в админке, сохранив всю функциональность
# ✅ БЕЗОПАСНО: Наследует от существующих админок, добавляет только фильтрацию

from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html

# 🔗 Импорт Proxy моделей
from .proxy_models import (
    # 🛥️ Лодки
    CategoryBoats, ProductBoats,
    # 🚗 Автомобили
    CategoryCars, ProductCars,
    # 💼 Продажи
    SalesCart, SalesOrder, SalesProfile,
    # 🏠 Контент главной страницы
    ContentContactInfo, ContentFAQ, ContentBanner,
    ContentTestimonial, ContentHeroSection, ContentCompanyDescription,
    # 📝 Блог
    ContentBlogCategory, ContentBlogArticle
)

# 🔗 Импорт существующих админок для наследования
from .admin import CategoryAdmin, ProductAdmin
from accounts.admin import CartAdmin, OrderAdmin, ProfileAdmin
from home.admin import (
    ContactInfoAdmin, FAQAdmin, BannerAdmin,
    TestimonialAdmin, HeroSectionAdmin, CompanyDescriptionAdmin
)
from blog.admin import CategoryAdmin as BlogCategoryAdmin, ArticleAdmin as BlogArticleAdmin


# 📦 ТОВАРЫ И КАТАЛОГ - Группа 1: ЛОДКИ 🛥️

@admin.register(CategoryBoats)
class CategoryBoatsAdmin(CategoryAdmin):
    """🛥️ Админка категорий лодок - наследует всю функциональность CategoryAdmin"""

    # 🎯 Добавляем специфическую фильтрацию только для лодок
    def get_queryset(self, request):
        """📊 Показываем только категории лодок"""
        return super().get_queryset(request).filter(category_type='boats')

    # 🎨 Настраиваем заголовки для лодок
    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для лодок"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '🛥️ Категории лодок',
            'subtitle': 'Управление категориями лодочных ковриков'
        })
        return super().changelist_view(request, extra_context)

    # 🛠️ ИСПРАВЛЕНИЕ ОШИБКИ storage_info
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


@admin.register(ProductBoats)
class ProductBoatsAdmin(ProductAdmin):
    """🛥️ Админка товаров лодок - наследует всю функциональность ProductAdmin"""

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

    # 🔍 Добавляем поиск по размерам лодок
    search_fields = [
        'product_name',
        'product_sku',
        'product_desription',
        'boat_mat_length',  # 🛥️ Поиск по длине
        'boat_mat_width'  # 🛥️ Поиск по ширине
    ]

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


# 📦 ТОВАРЫ И КАТАЛОГ - Группа 2: АВТОМОБИЛИ 🚗

@admin.register(CategoryCars)
class CategoryCarsAdmin(CategoryAdmin):
    """🚗 Админка категорий автомобилей - наследует всю функциональность CategoryAdmin"""

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

    # 🛠️ ИСПРАВЛЕНИЕ ОШИБКИ storage_info
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


@admin.register(ProductCars)
class ProductCarsAdmin(ProductAdmin):
    """🚗 Админка товаров автомобилей - наследует всю функциональность ProductAdmin"""

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
            'fields': ('page_title', 'meta_title', 'meta_description'),
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


# 💼 ПРОДАЖИ И ЗАКАЗЫ - Группа 3: SALES 💰

@admin.register(SalesCart)
class SalesCartAdmin(CartAdmin):
    """🛒 Админка корзин в разделе продаж - наследует всю функциональность CartAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для продаж"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '🛒 Корзины',
            'subtitle': 'Управление корзинами покупателей'
        })
        return super().changelist_view(request, extra_context)


@admin.register(SalesOrder)
class SalesOrderAdmin(OrderAdmin):
    """📦 Админка заказов в разделе продаж - наследует всю функциональность OrderAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для продаж"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '📦 Заказы',
            'subtitle': 'Управление заказами покупателей'
        })
        return super().changelist_view(request, extra_context)


@admin.register(SalesProfile)
class SalesProfileAdmin(ProfileAdmin):
    """👤 Админка профилей в разделе продаж - наследует всю функциональность ProfileAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для продаж"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '👤 Профили пользователей',
            'subtitle': 'Управление профилями покупателей'
        })
        return super().changelist_view(request, extra_context)


# 🌐 КОНТЕНТ САЙТА - Группа 4: ГЛАВНАЯ СТРАНИЦА 🏠

@admin.register(ContentContactInfo)
class ContentContactInfoAdmin(ContactInfoAdmin):
    """📞 Админка контактов в разделе контента - наследует всю функциональность ContactInfoAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для контента"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '📞 Контактная информация',
            'subtitle': 'Управление контактными данными'
        })
        return super().changelist_view(request, extra_context)


@admin.register(ContentFAQ)
class ContentFAQAdmin(FAQAdmin):
    """❓ Админка FAQ в разделе контента - наследует всю функциональность FAQAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для контента"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '❓ Частые вопросы',
            'subtitle': 'Управление вопросами и ответами'
        })
        return super().changelist_view(request, extra_context)


@admin.register(ContentBanner)
class ContentBannerAdmin(BannerAdmin):
    """🎨 Админка баннеров в разделе контента - наследует всю функциональность BannerAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для контента"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '🎨 Баннеры',
            'subtitle': 'Управление баннерами главной страницы'
        })
        return super().changelist_view(request, extra_context)


@admin.register(ContentTestimonial)
class ContentTestimonialAdmin(TestimonialAdmin):
    """💬 Админка отзывов в разделе контента - наследует всю функциональность TestimonialAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для контента"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '💬 Отзывы клиентов',
            'subtitle': 'Управление отзывами покупателей'
        })
        return super().changelist_view(request, extra_context)


@admin.register(ContentHeroSection)
class ContentHeroSectionAdmin(HeroSectionAdmin):
    """🎬 Админка hero-секции в разделе контента - наследует всю функциональность HeroSectionAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для контента"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '🎬 Hero-секции',
            'subtitle': 'Управление главными блоками страницы'
        })
        return super().changelist_view(request, extra_context)


@admin.register(ContentCompanyDescription)
class ContentCompanyDescriptionAdmin(CompanyDescriptionAdmin):
    """📝 Админка описания компании в разделе контента - наследует всю функциональность CompanyDescriptionAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для контента"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '📝 Описание компании',
            'subtitle': 'Управление информацией о компании'
        })
        return super().changelist_view(request, extra_context)


# 🌐 КОНТЕНТ САЙТА - Группа 5: БЛОГ 📝

@admin.register(ContentBlogCategory)
class ContentBlogCategoryAdmin(BlogCategoryAdmin):
    """📂 Админка категорий блога в разделе контента - наследует всю функциональность CategoryAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для контента"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '📂 Категории статей',
            'subtitle': 'Управление категориями блога'
        })
        return super().changelist_view(request, extra_context)


@admin.register(ContentBlogArticle)
class ContentBlogArticleAdmin(BlogArticleAdmin):
    """📝 Админка статей блога в разделе контента - наследует всю функциональность ArticleAdmin"""

    def changelist_view(self, request, extra_context=None):
        """📝 Добавляем контекст для контента"""
        extra_context = extra_context or {}
        extra_context.update({
            'title': '📝 Статьи блога',
            'subtitle': 'Управление статьями и публикациями'
        })
        return super().changelist_view(request, extra_context)

# 🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:
#
# ✅ СОХРАНЕНО:
# - Вся функциональность существующих админок
# - Все методы, действия, фильтры, инлайны
# - SEO оптимизация, экспорт, импорт
# - Валидация и обработка изображений
#
# ✅ ДОБАВЛЕНО:
# - Логическая группировка по бизнес-задачам
# - Автоматическая фильтрация по типам
# - Специфические поля для лодок/автомобилей
# - Удобные заголовки для каждой группы
#
# ✅ БЕЗОПАСНОСТЬ:
# - Не изменяет основные модели
# - Не ломает существующий код
# - Использует стандартные Django подходы
# - Легко откатить при необходимости
#
# 🛠️ ИСПРАВЛЕНО:
# - Добавлены методы storage_info для CategoryBoatsAdmin и CategoryCarsAdmin
# - Исправлены ошибки admin.E035