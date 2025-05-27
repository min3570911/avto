# 📁 products/admin.py - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ ОШИБОК
# 🛍️ Админка для системы интернет-магазина автоковриков с исправленными импортами

from django.contrib import admin
from django.utils.html import mark_safe
from .models import *

# 🔧 ОПЦИОНАЛЬНЫЙ ИМПОРТ: если используете django-summernote
try:
    from django_summernote.admin import SummernoteModelAdmin

    SUMMERNOTE_AVAILABLE = True
except ImportError:
    # 📝 Если Summernote не установлен, используем обычный ModelAdmin
    SummernoteModelAdmin = admin.ModelAdmin
    SUMMERNOTE_AVAILABLE = False
    print("⚠️ django-summernote не найден. Используется стандартный Django админ.")


# 🖼️ ИСПРАВЛЕНО: Определяем ProductImageAdmin ПЕРЕД ProductAdmin
class ProductImageAdmin(admin.StackedInline):
    """🖼️ Инлайн админка для изображений товаров"""
    model = ProductImage
    verbose_name = "Изображение товара"
    verbose_name_plural = "Изображения товара"
    extra = 1  # 📸 Количество пустых форм для добавления

    # 🎨 Дополнительные поля для удобства
    fields = ('image', 'img_preview')
    readonly_fields = ('img_preview',)

    def img_preview(self, obj):
        """👁️ Предпросмотр изображения при редактировании"""
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="150" style="border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"/>'
            )
        return "📷 Изображение не загружено"

    img_preview.short_description = "Предпросмотр"


# 🛍️ ИСПРАВЛЕНО: ProductAdmin теперь может использовать ProductImageAdmin
class ProductAdmin(SummernoteModelAdmin if SUMMERNOTE_AVAILABLE else admin.ModelAdmin):
    """🛍️ Админка для товаров с поддержкой Summernote (опционально)"""

    list_display = ['product_name', 'category', 'display_price', 'newest_product', 'get_images_count']
    list_filter = ['category', 'newest_product', 'created_at']
    search_fields = ['product_name', 'product_desription']
    list_editable = ['newest_product']  # ✏️ Быстрое редактирование

    # 🖼️ ИСПРАВЛЕНО: Теперь ProductImageAdmin определен выше
    inlines = [ProductImageAdmin]

    # 📝 Группировка полей в админке
    fieldsets = (
        ('🛍️ Основная информация', {
            'fields': ('product_name', 'slug', 'category', 'price')
        }),
        ('📝 Описание', {
            'fields': ('product_desription',),
            'description': '📝 Подробное описание товара для покупателей'
        }),
        ('⚙️ Настройки', {
            'fields': ('newest_product', 'parent'),
            'classes': ('collapse',)  # 📦 Сворачиваемый блок
        }),
    )

    # 🔧 ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ: Summernote для богатого текста
    if SUMMERNOTE_AVAILABLE:
        summernote_fields = ('product_desription',)

    def get_images_count(self, obj):
        """📊 Количество изображений у товара"""
        count = obj.product_images.count()
        if count == 0:
            return mark_safe('<span style="color: red;">❌ Нет изображений</span>')
        elif count < 3:
            return mark_safe(f'<span style="color: orange;">⚠️ {count} изображений</span>')
        else:
            return mark_safe(f'<span style="color: green;">✅ {count} изображений</span>')

    get_images_count.short_description = "Изображения"

    # 📊 Действия для массового управления
    actions = ['mark_as_new', 'mark_as_regular', 'duplicate_products']

    def mark_as_new(self, request, queryset):
        """🆕 Отметить как новые товары"""
        updated = queryset.update(newest_product=True)
        self.message_user(request, f"✅ Отмечено как новые: {updated} товаров")

    def mark_as_regular(self, request, queryset):
        """📦 Убрать отметку 'новый товар'"""
        updated = queryset.update(newest_product=False)
        self.message_user(request, f"✅ Убрана отметка 'новый': {updated} товаров")

    def duplicate_products(self, request, queryset):
        """📋 Дублировать выбранные товары"""
        duplicated = 0
        for product in queryset:
            # 🔄 Создаем копию товара
            product.pk = None
            product.product_name = f"{product.product_name} (копия)"
            product.slug = f"{product.slug}-copy"
            product.save()
            duplicated += 1

        self.message_user(request, f"✅ Создано копий: {duplicated}")

    mark_as_new.short_description = "🆕 Отметить как новые товары"
    mark_as_regular.short_description = "📦 Убрать отметку 'новый'"
    duplicate_products.short_description = "📋 Дублировать товары"


# 📂 РЕГИСТРАЦИЯ ВСЕХ МОДЕЛЕЙ
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """📂 Админка для категорий товаров"""
    list_display = ['category_name', 'slug', 'get_products_count']
    search_fields = ['category_name']
    prepopulated_fields = {'slug': ('category_name',)}

    def get_products_count(self, obj):
        """📊 Количество товаров в категории"""
        count = obj.products.count()
        return f"📦 {count} товаров" if count > 0 else "🚫 Нет товаров"

    get_products_count.short_description = "Товары в категории"

    def get_readonly_fields(self, request, obj=None):
        """⚠️ Предупреждение об устаревшей модели"""
        return self.readonly_fields + ('color_name', 'price')

    def has_add_permission(self, request):
        """🚫 Запрещаем добавление новых записей"""
        return False


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

    actions = ['make_option', 'make_kit', 'reset_prices']

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


# 🗑️ ИСПРАВЛЕНО: Убираем повторную регистрацию Product и ProductImage
admin.site.register(Product, ProductAdmin)
# admin.site.register(ProductImage)  # ❌ Не нужно, так как используется inline

# 🎯 Кастомизация заголовков админки
admin.site.site_header = "🛒 Админ-панель магазина автоковриков"
admin.site.site_title = "Автоковрики - Админка"
admin.site.index_title = "Управление магазином"