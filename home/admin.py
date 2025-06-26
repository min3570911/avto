# 📁 home/admin.py - ОБНОВЛЕНО с админкой для HeroSection
# 🆕 ДОБАВЛЕНО: Админка для HeroSection и HeroAdvantage
# ✅ СОХРАНЕНО: Все существующие админки (FAQ, Banner, Testimonial, ContactInfo)

from django.contrib import admin
from django.utils.html import format_html
from .models import ContactInfo, FAQ, Banner, Testimonial, HeroSection, HeroAdvantage


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


# 🆕 НОВОЕ: Админка для hero-секции
@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    """🎬 Админка для hero-секции главной страницы"""
    list_display = ('title', 'get_video_info', 'get_advantages_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'subtitle')
    readonly_fields = ('created_at', 'updated_at', 'get_video_preview')
    inlines = [HeroAdvantageInline]

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

    def get_video_info(self, obj):
        """🎥 Информация о видео файле"""
        if obj.video:
            try:
                file_size = obj.video.size / (1024 * 1024)  # Размер в MB
                return format_html(
                    '<span style="color: #28a745;">📹 {:.1f} MB</span>',
                    file_size
                )
            except:
                return "📹 Видео загружено"
        return format_html('<span style="color: #dc3545;">❌ Видео не загружено</span>')

    get_video_info.short_description = "Видео"

    def get_video_preview(self, obj):
        """👁️ Предпросмотр видео"""
        if obj.video:
            return format_html(
                '<video width="300" height="200" controls style="border-radius: 8px;">'
                '<source src="{}" type="video/mp4">'
                'Ваш браузер не поддерживает видео.'
                '</video>',
                obj.video.url
            )
        return "🎥 Видео не загружено"

    get_video_preview.short_description = "Предпросмотр видео"

    def get_advantages_count(self, obj):
        """🎯 Количество преимуществ"""
        count = obj.advantages.count()
        if count == 0:
            return format_html('<span style="color: #dc3545;">❌ Нет преимуществ</span>')
        elif count < 4:
            return format_html('<span style="color: #ffc107;">⚠️ {} из 4</span>', count)
        else:
            return format_html('<span style="color: #28a745;">✅ {} преимуществ</span>', count)

    get_advantages_count.short_description = "Преимущества"

    def has_add_permission(self, request):
        """🚫 Ограничиваем количество hero-секций до 3"""
        if HeroSection.objects.count() >= 3:
            return False
        return super().has_add_permission(request)


# ✅ СУЩЕСТВУЮЩИЕ АДМИНКИ (без изменений)

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
                '<img src="{}" style="max-width: 200px; max-height: 150px; object-fit: contain; border-radius: 5px;"/>',
                obj.image.url
            )
        return "🖼️ Изображение не загружено"

    get_image_preview.short_description = "Предпросмотр"


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """💬 Админка для отзывов клиентов"""
    list_display = ('name', 'position', 'get_stars', 'featured', 'is_active', 'created_at')
    list_filter = ('rating', 'featured', 'is_active', 'created_at')
    search_fields = ('name', 'position', 'text')
    list_editable = ('featured', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'get_avatar_preview')

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

    def get_stars(self, obj):
        """⭐ Отображение рейтинга звездочками"""
        return '⭐' * obj.rating

    get_stars.short_description = "Рейтинг"

    def get_avatar_preview(self, obj):
        """👤 Предпросмотр аватара"""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 50%;"/>',
                obj.avatar.url
            )
        return "👤 Аватар не загружен"

    get_avatar_preview.short_description = "Предпросмотр аватара"

# 💡 ПРИМЕЧАНИЯ ПО АДМИНКЕ:
# 🆕 HeroSectionAdmin:
#   - Поддержка инлайн редактирования преимуществ
#   - Предпросмотр видео прямо в админке
#   - Ограничение до 3 hero-секций максимум
#   - Автоматическая деактивация других секций при активации новой
#   - Информация о размере видео файла
#   - Подсчет количества преимуществ с цветовой индикацией
#
# ✅ Все существующие админки сохранены без изменений
# 🎯 FAQ админка готова для управления аккордеоном на главной странице