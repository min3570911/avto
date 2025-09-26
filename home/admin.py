# 📁 home/admin.py - ФИНАЛЬНАЯ ВЕРСИЯ с CompanyDescriptionAdmin
# 🆕 ДОБАВЛЕНО: Админка для CompanyDescription (синглтон)
# ✅ СОХРАНЕНО: Все существующие админки без изменений

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ContactInfo, FAQ, Banner, Testimonial, HeroSection, HeroAdvantage, CompanyDescription, ContactMessage, DeliveryOption


# 🆕 НОВОЕ: Инлайн админка для преимуществ hero-секции
class HeroAdvantageInline(admin.TabularInline):
    """🎯 Инлайн админка для преимуществ hero-секции"""
    model = HeroAdvantage
    extra = 1
    fields = ('icon_file', 'get_icon_preview', 'icon', 'title', 'description', 'order')
    readonly_fields = ('get_icon_preview',)
    ordering = ('order',)

    def get_icon_preview(self, obj):
        """👁️ Предпросмотр иконки"""
        if obj.icon_file:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; object-fit: contain;" title="{}">',
                obj.icon_file.url,
                obj.title
            )
        elif obj.icon:
            return format_html('<span style="font-size: 24px;">{}</span>', obj.icon)
        return "❌ Нет иконки"

    get_icon_preview.short_description = "Предпросмотр"


# 🔧 Существующие админки (без изменений)

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    """📞 Админка для контактной информации"""
    list_display = ('phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('phone', 'email', 'address')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('📞 Основная информация', {
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


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """❓ Админка для часто задаваемых вопросов"""
    list_display = ('question', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('is_active', 'order')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('❓ Содержимое', {
            'fields': ('question', 'answer')
        }),
        ('⚙️ Настройки', {
            'fields': ('is_active', 'order')
        }),
        ('📅 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """🎨 Админка для баннеров"""
    list_display = ('title', 'get_image_preview', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'subtitle')
    list_editable = ('is_active', 'order')
    readonly_fields = ('created_at', 'updated_at', 'get_image_preview')

    def get_image_preview(self, obj):
        """👁️ Предпросмотр изображения"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 50px; object-fit: cover; border-radius: 5px;" title="{}">',
                obj.image.url,
                obj.title
            )
        return "❌ Нет изображения"

    get_image_preview.short_description = "Предпросмотр"

    fieldsets = (
        ('🎨 Содержимое', {
            'fields': ('title', 'subtitle', 'image', 'get_image_preview')
        }),
        ('🔗 Ссылка', {
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


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """💬 Админка для отзывов клиентов"""
    list_display = ('name', 'get_avatar_preview', 'rating', 'featured', 'is_active', 'created_at')
    list_filter = ('rating', 'featured', 'is_active', 'created_at')
    search_fields = ('name', 'position', 'text')
    list_editable = ('featured', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'get_avatar_preview')

    def get_avatar_preview(self, obj):
        """👁️ Предпросмотр аватара"""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 50%;" title="{}">',
                obj.avatar.url,
                obj.name
            )
        return "👤 Нет фото"

    get_avatar_preview.short_description = "Фото"

    fieldsets = (
        ('💬 Отзыв', {
            'fields': ('name', 'position', 'text', 'rating')
        }),
        ('👤 Фото', {
            'fields': ('avatar', 'get_avatar_preview'),
            'classes': ('collapse',)
        }),
        ('⚙️ Настройки', {
            'fields': ('is_active', 'featured')
        }),
        ('📅 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    """🎬 Админка для hero-секции главной страницы"""
    list_display = ('title', 'get_video_info', 'get_advantages_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'subtitle')
    readonly_fields = ('created_at', 'updated_at', 'get_video_preview')
    inlines = [HeroAdvantageInline]

    def get_video_info(self, obj):
        """🎥 Информация о видео"""
        if obj.video:
            return "✅ Есть видео"
        elif obj.fallback_image:
            return "🖼️ Только изображение"
        return "❌ Нет медиа"

    get_video_info.short_description = "Медиа"

    def get_advantages_count(self, obj):
        """🎯 Количество преимуществ"""
        count = obj.advantages.count()
        if count > 0:
            return f"🎯 {count} преимуществ"
        return "❌ Нет преимуществ"

    get_advantages_count.short_description = "Преимущества"

    def get_video_preview(self, obj):
        """👁️ Предпросмотр медиа"""
        if obj.video:
            return format_html(
                '<div style="margin: 10px 0;">'
                '<video width="200" height="112" controls style="border-radius: 5px;">'
                '<source src="{}" type="video/mp4">'
                'Ваш браузер не поддерживает видео.'
                '</video>'
                '</div>',
                obj.video.url
            )
        elif obj.fallback_image:
            return format_html(
                '<img src="{}" style="width: 200px; height: 112px; object-fit: cover; border-radius: 5px;" title="Изображение-заглушка">',
                obj.fallback_image.url
            )
        return "❌ Медиа контент не загружен"

    get_video_preview.short_description = "Предпросмотр"

    fieldsets = (
        ('🎬 Содержимое hero-секции', {
            'fields': ('title', 'subtitle')
        }),
        ('🎥 Медиа контент', {
            'fields': ('video', 'get_video_preview', 'fallback_image'),
            'description': 'Фоновое видео и изображение-заглушка для hero-блока'
        }),
        ('🎯 Кнопка действия', {
            'fields': ('button_text', 'button_link'),
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


# 🆕 НОВАЯ АДМИНКА: CompanyDescription (синглтон)
@admin.register(CompanyDescription)
class CompanyDescriptionAdmin(admin.ModelAdmin):
    """📝 Админка для описания компании (только один экземпляр)"""

    # 🚫 Синглтон логика в админке
    def has_add_permission(self, request):
        """🚫 Запретить создание новых записей, если уже есть описание"""
        return not CompanyDescription.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """⚠️ Разрешить удаление (чтобы можно было пересоздать при необходимости)"""
        return True

    def changelist_view(self, request, extra_context=None):
        """📝 Если нет записи, перенаправляем на создание"""
        if not CompanyDescription.objects.exists():
            return self.add_view(request)
        return super().changelist_view(request, extra_context)

    # 🎨 Группировка полей в админке
    fieldsets = (
        ('📝 Описание компании', {
            'fields': ('title', 'content'),
            'description': 'Заголовок и текст описания компании для главной страницы'
        }),
    )

# 🆕 НОВАЯ АДМИНКА: ContactMessage для сообщений обратной связи
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """📧 Админка для сообщений обратной связи"""

    list_display = (
        'get_status_icon',
        'get_name_link',  # Сделаем имя кликабельным
        'email',
        'get_subject_short',
        'get_message_preview',
        'is_processed',
        'created_at',
        'get_reply_status'
    )

    list_filter = (
        'is_processed',
        'created_at',
        'replied_at'
    )

    search_fields = (
        'name',
        'email',
        'subject',
        'message'
    )

    list_editable = ('is_processed',)

    readonly_fields = ('created_at', 'updated_at', 'replied_at')

    ordering = ('-created_at',)

    # Группировка полей
    fieldsets = (
        ('👤 Информация о клиенте', {
            'fields': ('name', 'email', 'phone')
        }),
        ('📝 Сообщение', {
            'fields': ('subject', 'message')
        }),
        ('💬 Ответ администратора', {
            'fields': ('admin_reply', 'is_processed'),
            'classes': ('collapse',)
        }),
        ('📅 Служебная информация', {
            'fields': ('created_at', 'updated_at', 'replied_at'),
            'classes': ('collapse',)
        }),
    )

    def get_status_icon(self, obj):
        """📊 Иконка статуса"""
        if obj.is_processed:
            return "✅"
        else:
            return "⏳"
    get_status_icon.short_description = "Статус"

    def get_subject_short(self, obj):
        """📝 Короткая тема"""
        if obj.subject:
            return obj.subject[:30] + "..." if len(obj.subject) > 30 else obj.subject
        return "Без темы"
    get_subject_short.short_description = "Тема"

    def get_message_preview(self, obj):
        """👁️ Превью сообщения"""
        preview = obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
        return format_html('<span title="{}">{}</span>', obj.message, preview)
    get_message_preview.short_description = "Сообщение"

    def get_name_link(self, obj):
        """👤 Имя как ссылка для перехода к сообщению"""
        from django.urls import reverse
        url = reverse('admin:home_contactmessage_change', args=[obj.uid])
        return format_html('<a href="{}" style="font-weight: bold;">{}</a>', url, obj.name)
    get_name_link.short_description = "Имя"

    def get_reply_status(self, obj):
        """💬 Статус ответа"""
        if obj.admin_reply:
            return format_html(
                '<span style="color: green;">✅ Отвечено</span>'
            )
        else:
            return format_html(
                '<span style="color: orange;">⏳ Нет ответа</span>'
            )
    get_reply_status.short_description = "Ответ"

    # Дополнительные действия в админке
    actions = ['mark_as_processed', 'mark_as_unprocessed']

    def mark_as_processed(self, request, queryset):
        """✅ Отметить как обработанные"""
        queryset.update(is_processed=True)
        self.message_user(request, f"Отмечено как обработанные: {queryset.count()} сообщений")
    mark_as_processed.short_description = "Отметить как обработанные"

    def mark_as_unprocessed(self, request, queryset):
        """⏳ Отметить как необработанные"""
        queryset.update(is_processed=False)
        self.message_user(request, f"Отмечено как необработанные: {queryset.count()} сообщений")
    mark_as_unprocessed.short_description = "Отметить как необработанные"


# 🚚 НОВАЯ АДМИНКА: DeliveryOption для способов доставки
@admin.register(DeliveryOption)
class DeliveryOptionAdmin(admin.ModelAdmin):
    """🚚 Админка для способов доставки и оплаты"""

    list_display = (
        'get_icon_display',
        'title',
        'get_price_short',
        'get_delivery_time_short',
        'coverage_area',
        'is_active',
        'order',
        'created_at'
    )

    list_filter = (
        'is_active',
        'created_at'
    )

    search_fields = (
        'title',
        'description',
        'coverage_area',
        'price_info'
    )

    list_editable = ('is_active', 'order')

    readonly_fields = ('created_at', 'updated_at')

    ordering = ('order', 'title')

    fieldsets = (
        ('📋 Основная информация', {
            'fields': ('title', 'description', 'icon')
        }),
        ('💰 Стоимость и сроки', {
            'fields': ('price_info', 'delivery_time')
        }),
        ('🌍 Зона покрытия и оплата', {
            'fields': ('coverage_area', 'payment_methods')
        }),
        ('📝 Дополнительная информация', {
            'fields': ('additional_info',),
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

    def get_icon_display(self, obj):
        """🎨 Отображение иконки"""
        if obj.icon:
            if "fa" in obj.icon:
                return format_html('<i class="{}" style="font-size: 1.2rem;"></i>', obj.icon)
            else:
                return format_html('<span style="font-size: 1.2rem;">{}</span>', obj.icon)
        return "❌"
    get_icon_display.short_description = "Иконка"

    def get_price_short(self, obj):
        """💰 Краткая информация о цене"""
        if obj.price_info:
            return obj.price_info[:30] + "..." if len(obj.price_info) > 30 else obj.price_info
        return "Не указано"
    get_price_short.short_description = "Стоимость"

    def get_delivery_time_short(self, obj):
        """⏱️ Краткая информация о сроках"""
        if obj.delivery_time:
            return obj.delivery_time
        return "Не указано"
    get_delivery_time_short.short_description = "Сроки"

    # Дополнительные действия
    actions = ['activate_delivery_options', 'deactivate_delivery_options']

    def activate_delivery_options(self, request, queryset):
        """✅ Активировать способы доставки"""
        queryset.update(is_active=True)
        self.message_user(request, f"Активировано: {queryset.count()} способов доставки")
    activate_delivery_options.short_description = "Активировать выбранные способы доставки"

    def deactivate_delivery_options(self, request, queryset):
        """❌ Деактивировать способы доставки"""
        queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано: {queryset.count()} способов доставки")
    deactivate_delivery_options.short_description = "Деактивировать выбранные способы доставки"


# 🔧 ИТОГОВЫЕ ИЗМЕНЕНИЯ В ФАЙЛЕ:
# ✅ ДОБАВЛЕНО: CompanyDescriptionAdmin с синглтон логикой
# ✅ ДОБАВЛЕНО: ContactMessageAdmin для сообщений обратной связи
# ✅ ФУНКЦИИ:
#    - Простая админка с заголовком и содержимым
#    - Синглтон логика (только один экземпляр)
#    - Автоматическое перенаправление на создание
#    - Полнофункциональная админка для обратной связи
#    - Превью сообщений, статусы, фильтры
#    - Массовые действия для обработки сообщений
# ✅ ИСПРАВЛЕНО: Убран конфликт fields и fieldsets
# ✅ СОХРАНЕНО: Все существующие админки без изменений