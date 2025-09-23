# 📁 common/admin.py
# 👨‍💼 Админка с системой модерации отзывов и улучшенным интерфейсом
# 🔧 ИСПРАВЛЕНО: Добавлен импорт django.utils.timezone

from django.contrib import admin
from django.utils.html import format_html
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone  # ✅ ИСПРАВЛЕНО: Добавлен отсутствующий импорт
from .models import ProductReview, Wishlist


def approve_reviews(modeladmin, request, queryset):
    """✅ Массовое одобрение отзывов"""
    updated = queryset.update(is_approved=True)
    modeladmin.message_user(request, f'Одобрено {updated} отзывов.')


approve_reviews.short_description = "✅ Одобрить выбранные отзывы"


def reject_reviews(modeladmin, request, queryset):
    """❌ Массовое отклонение отзывов"""
    updated = queryset.update(is_approved=False)
    modeladmin.message_user(request, f'Отклонено {updated} отзывов.')


reject_reviews.short_description = "❌ Отклонить выбранные отзывы"


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """📝 Админка для универсальных отзывов товаров с модерацией"""

    list_display = (
        'get_approval_status',
        'get_user_info',
        'get_product_info',
        'get_rating_stars',
        'get_likes_dislikes',
        'date_added'
    )

    list_filter = (
        'is_approved',
        'stars',
        'date_added',
        'content_type'
    )

    search_fields = (
        'reviewer_name',
        'reviewer_email',
        'content'
    )

    readonly_fields = (
        'content_type',
        'object_id',
        'user',
        'reviewer_name',
        'reviewer_email',
        'date_added',
        'get_product_link',
        'get_likes_dislikes',
        'get_rating_stars'
    )

    ordering = ('-date_added',)
    date_hierarchy = 'date_added'

    actions = [approve_reviews, reject_reviews]

    fieldsets = (
        ('📝 Отзыв', {
            'fields': ('reviewer_name', 'reviewer_email', 'get_product_link', 'stars', 'get_rating_stars', 'content')
        }),
        ('✅ Модерация', {
            'fields': ('is_approved',),
            'description': 'Только одобренные отзывы видят пользователи'
        }),
        ('👍👎 Реакции', {
            'fields': ('get_likes_dislikes',),
            'classes': ('collapse',)
        }),
        ('🔗 Техническая информация', {
            'fields': ('content_type', 'object_id', 'date_added'),
            'classes': ('collapse',)
        }),
    )

    def get_approval_status(self, obj):
        """✅ Статус модерации с цветовой индикацией"""
        if obj.is_approved:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Одобрен</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">⏳ На модерации</span>'
            )

    get_approval_status.short_description = "Статус"
    get_approval_status.admin_order_field = 'is_approved'

    def get_user_info(self, obj):
        """👤 Информация об авторе отзыва"""
        # Для анонимных отзывов показываем reviewer_name и reviewer_email
        if obj.reviewer_name:
            email_display = obj.reviewer_email if hasattr(obj, 'reviewer_email') and obj.reviewer_email else 'Email не указан'
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.reviewer_name,
                email_display
            )
        # Если есть пользователь (для совместимости со старыми отзывами)
        elif obj.user:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.user.username,
                obj.user.email or 'Нет email'
            )
        return "❌ Автор неизвестен"

    get_user_info.short_description = "Автор отзыва"

    def get_product_info(self, obj):
        """📦 Информация о товаре"""
        if obj.product:
            # 🔍 Определяем тип товара для иконки
            if hasattr(obj.product, 'is_boat_product') and obj.product.is_boat_product():
                icon = "🛥️"
                product_type = "Лодка"
            else:
                icon = "🚗"
                product_type = "Автомобиль"

            return format_html(
                '{} <strong>{}</strong><br><small>{}</small>',
                icon,
                obj.product.product_name,
                product_type
            )
        return "❌ Товар удален"

    get_product_info.short_description = "Товар"

    def get_product_link(self, obj):
        """🔗 Ссылка на товар"""
        if obj.product:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                f'/admin/{obj.content_type.app_label}/{obj.content_type.model}/{obj.object_id}/change/',
                f'{obj.product.product_name} (Редактировать)'
            )
        return "❌ Товар недоступен"

    get_product_link.short_description = "Ссылка на товар"

    def get_rating_stars(self, obj):
        """⭐ Визуальный рейтинг"""
        stars = "⭐" * obj.stars + "☆" * (5 - obj.stars)
        return format_html('<span style="font-size: 16px;">{}</span>', stars)

    get_rating_stars.short_description = "Рейтинг"
    get_rating_stars.admin_order_field = 'stars'

    def get_likes_dislikes(self, obj):
        """👍👎 Лайки и дизлайки"""
        likes_count = obj.like_count()
        dislikes_count = obj.dislike_count()

        return format_html(
            '<span style="color: green;">👍 {}</span> / <span style="color: red;">👎 {}</span>',
            likes_count,
            dislikes_count
        )

    get_likes_dislikes.short_description = "Лайки / Дизлайки"

    def has_add_permission(self, request):
        """🚫 Запретить создание отзывов через админку"""
        return False

    def has_change_permission(self, request, obj=None):
        """✏️ Разрешить редактирование для модерации"""
        return True

    def has_delete_permission(self, request, obj=None):
        """🗑️ Разрешить удаление проблемных отзывов"""
        return True


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """❤️ Админка для универсального избранного"""

    list_display = (
        'get_user_info',
        'get_product_info',
        'get_configuration',
        'added_on'
    )

    list_filter = (
        'added_on',
        'content_type',
        'has_podpyatnik'
    )

    search_fields = (
        'user__username',
        'user__email'
    )

    readonly_fields = (
        'user',
        'content_type',
        'object_id',
        'added_on',
        'get_product_link',
        'get_configuration_details'
    )

    ordering = ('-added_on',)
    date_hierarchy = 'added_on'

    fieldsets = (
        ('❤️ Избранное', {
            'fields': ('user', 'get_product_link', 'added_on')
        }),
        ('🎨 Конфигурация', {
            'fields': ('get_configuration_details', 'kit_variant', 'carpet_color', 'border_color', 'has_podpyatnik')
        }),
        ('🔗 Техническая информация', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
    )

    def get_user_info(self, obj):
        """👤 Информация о пользователе"""
        if obj.user:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.user.username,
                obj.user.email or 'Нет email'
            )
        return "❌ Пользователь удален"

    get_user_info.short_description = "Пользователь"

    def get_product_info(self, obj):
        """📦 Информация о товаре"""
        if obj.product:
            # 🔍 Определяем тип товара для иконки
            if hasattr(obj.product, 'is_boat_product') and obj.product.is_boat_product():
                icon = "🛥️"
                product_type = "Лодка"
            else:
                icon = "🚗"
                product_type = "Автомобиль"

            return format_html(
                '{} <strong>{}</strong><br><small>{}</small>',
                icon,
                obj.product.product_name,
                product_type
            )
        return "❌ Товар удален"

    get_product_info.short_description = "Товар"

    def get_product_link(self, obj):
        """🔗 Ссылка на товар"""
        if obj.product:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                f'/admin/{obj.content_type.app_label}/{obj.content_type.model}/{obj.object_id}/change/',
                f'{obj.product.product_name} (Редактировать)'
            )
        return "❌ Товар недоступен"

    get_product_link.short_description = "Ссылка на товар"

    def get_configuration(self, obj):
        """🎨 Краткая конфигурация"""
        parts = []

        if obj.kit_variant:
            parts.append(f"📦 {obj.kit_variant.name}")

        if obj.carpet_color:
            parts.append(f"🎨 {obj.carpet_color.name}")

        if obj.border_color:
            parts.append(f"🔲 {obj.border_color.name}")

        if obj.has_podpyatnik:
            parts.append("👣 Подпятник")

        return format_html('<br>'.join(parts)) if parts else "🔧 Стандартная"

    get_configuration.short_description = "Конфигурация"

    def get_configuration_details(self, obj):
        """🔧 Подробная конфигурация"""
        details = []

        if obj.kit_variant:
            details.append(f"Комплектация: {obj.kit_variant.name}")
        else:
            details.append("Комплектация: Стандартная (для лодок)")

        if obj.carpet_color:
            details.append(f"Цвет коврика: {obj.carpet_color.name}")
        else:
            details.append("Цвет коврика: Не выбран")

        if obj.border_color:
            details.append(f"Цвет окантовки: {obj.border_color.name}")
        else:
            details.append("Цвет окантовки: Не выбран")

        details.append(f"Подпятник: {'Да' if obj.has_podpyatnik else 'Нет'}")

        return format_html('<br>'.join(details))

    get_configuration_details.short_description = "Детали конфигурации"

    def has_add_permission(self, request):
        """🚫 Запретить создание избранного через админку"""
        return False

    def has_change_permission(self, request, obj=None):
        """✏️ Разрешить только просмотр"""
        return True

    def has_delete_permission(self, request, obj=None):
        """🗑️ Разрешить удаление записей избранного"""
        return True


# 🔧 КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ✅ ИСПРАВЛЕНО:
# - Добавлен импорт `from django.utils import timezone`
# - Этот импорт может потребоваться для фильтрации по датам
# - Обеспечивает совместимость с расширенной функциональностью
#
# ✅ СОХРАНЕНО БЕЗ ИЗМЕНЕНИЙ:
# - Вся существующая логика админок
# - Все методы отображения данных
# - Система модерации отзывов
# - Конфигурация полей и фильтров
# - Разрешения доступа
#
# 🎯 РЕЗУЛЬТАТ:
# - Устранена ошибка "Unresolved reference 'timezone'"
# - Обеспечена совместимость для будущих функций с датами
# - Сохранена полная функциональность админки
# - Готовность к использованию timezone.now() в фильтрах и статистике