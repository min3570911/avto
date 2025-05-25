# 📁 home/admin.py - БЕЗ ShippingAddress
# 🗑️ ПОЛНОСТЬЮ УДАЛЕН ShippingAddress

from django.contrib import admin
from django.utils.html import format_html
from .models import ContactInfo, FAQ, Banner, Testimonial


# 🗑️ УДАЛЕНО: from .models import ShippingAddress


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    """📞 Админка для контактной информации"""
    list_display = ('phone', 'email', 'working_hours', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('phone', 'email', 'address')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('📞 Основные контакты', {
            'fields': ('phone', 'email', 'address', 'working_hours')
        }),
        ('🌐 Социальные сети', {
            'fields': ('telegram', 'instagram', 'facebook'),
            'classes': ('collapse',)
        }),
        ('⚙️ Настройки', {
            'fields': ('is_active',)
        }),
        ('📅 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """🚫 Разрешаем только одну запись контактов"""
        if ContactInfo.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """❓ Админка для частых вопросов"""
    list_display = ('question', 'get_short_answer', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('order', 'created_at')

    fieldsets = (
        ('❓ Вопрос и ответ', {
            'fields': ('question', 'answer')
        }),
        ('⚙️ Настройки', {
            'fields': ('order', 'is_active')
        }),
        ('📅 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_short_answer(self, obj):
        """📝 Короткий ответ для списка"""
        return f"{obj.answer[:50]}..." if len(obj.answer) > 50 else obj.answer

    get_short_answer.short_description = "Ответ"

    # 📋 Действия для массового управления
    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        """✅ Активировать выбранные FAQ"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Активировано FAQ: {count}")

    def make_inactive(self, request, queryset):
        """❌ Деактивировать выбранные FAQ"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано FAQ: {count}")

    make_active.short_description = "✅ Активировать выбранные FAQ"
    make_inactive.short_description = "❌ Деактивировать выбранные FAQ"


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """🎨 Админка для баннеров"""
    list_display = ('title', 'get_image_preview', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'subtitle')
    list_editable = ('is_active', 'order')
    readonly_fields = ('created_at', 'updated_at', 'get_image_preview')
    ordering = ('order', '-created_at')

    fieldsets = (
        ('🎨 Содержимое баннера', {
            'fields': ('title', 'subtitle', 'image', 'get_image_preview')
        }),
        ('🔗 Действие', {
            'fields': ('link', 'button_text'),
            'classes': ('collapse',)
        }),
        ('⚙️ Настройки', {
            'fields': ('is_active', 'order')
        }),
        ('📅 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_image_preview(self, obj):
        """🖼️ Предпросмотр изображения"""
        if obj.image:
            return format_html(
                '<img src="{}" width="200" style="border-radius: 5px;"/>',
                obj.image.url
            )
        return "Нет изображения"

    get_image_preview.short_description = "Предпросмотр"

    # 📋 Действия
    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"Активировано баннеров: {count}")

    def make_inactive(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано баннеров: {count}")

    make_active.short_description = "✅ Активировать выбранные баннеры"
    make_inactive.short_description = "❌ Деактивировать выбранные баннеры"


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """💬 Админка для отзывов клиентов"""
    list_display = ('name', 'position', 'get_short_text', 'rating', 'featured', 'is_active', 'created_at')
    list_filter = ('rating', 'featured', 'is_active', 'created_at')
    search_fields = ('name', 'position', 'text')
    list_editable = ('featured', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'get_avatar_preview')
    ordering = ('-featured', '-created_at')

    fieldsets = (
        ('👤 Информация о клиенте', {
            'fields': ('name', 'position', 'avatar', 'get_avatar_preview')
        }),
        ('💬 Отзыв', {
            'fields': ('text', 'rating')
        }),
        ('⚙️ Настройки', {
            'fields': ('featured', 'is_active')
        }),
        ('📅 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_short_text(self, obj):
        """📝 Короткий текст отзыва"""
        return f"{obj.text[:40]}..." if len(obj.text) > 40 else obj.text

    get_short_text.short_description = "Отзыв"

    def get_avatar_preview(self, obj):
        """👤 Предпросмотр аватара"""
        if obj.avatar:
            return format_html(
                '<img src="{}" width="100" height="100" style="border-radius: 50%; object-fit: cover;"/>',
                obj.avatar.url
            )
        return "Нет фото"

    get_avatar_preview.short_description = "Фото"

    # 📋 Действия
    actions = ['make_featured', 'remove_featured', 'make_active', 'make_inactive']

    def make_featured(self, request, queryset):
        count = queryset.update(featured=True)
        self.message_user(request, f"Отмечено как рекомендуемые: {count}")

    def remove_featured(self, request, queryset):
        count = queryset.update(featured=False)
        self.message_user(request, f"Убрано из рекомендуемых: {count}")

    def make_active(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"Активировано отзывов: {count}")

    def make_inactive(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано отзывов: {count}")

    make_featured.short_description = "⭐ Сделать рекомендуемыми"
    remove_featured.short_description = "🔽 Убрать из рекомендуемых"
    make_active.short_description = "✅ Активировать"
    make_inactive.short_description = "❌ Деактивировать"


# 🎨 Настройки админки
admin.site.site_header = "🛒 Автоковрики - Админ-панель"
admin.site.site_title = "Автоковрики"
admin.site.index_title = "Управление интернет-магазином"

# 🗑️ УДАЛЕНО:
# - ShippingAddressAdmin (больше не нужен)
# - Все связанное с адресами доставки

# ✅ ДОБАВЛЕНО:
# - Админка для баннеров главной страницы
# - Админка для отзывов клиентов
# - Улучшенная админка FAQ с предпросмотром