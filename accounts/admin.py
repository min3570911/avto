# 📁 accounts/admin.py - ИСПРАВЛЕННАЯ админка БЕЗ ошибки list_editable

from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    """📦 Товары в корзине"""
    model = CartItem
    extra = 0
    verbose_name = "Товар в корзине"
    verbose_name_plural = "Товары в корзине"
    readonly_fields = (
        'product', 'kit_variant', 'carpet_color',
        'border_color', 'has_podpyatnik', 'quantity', 'get_price'
    )
    fields = (
        'product', 'kit_variant', 'carpet_color', 'border_color',
        'has_podpyatnik', 'quantity', 'get_price'
    )

    def get_price(self, obj):
        """💰 Отображение цены товара"""
        return f"{obj.get_product_price():.2f} BYN"

    get_price.short_description = "Стоимость"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """🛒 Анонимные корзины"""
    list_display = ('get_cart_info', 'get_items_count', 'get_total', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('session_id', 'user__username')
    readonly_fields = ('user', 'session_id', 'coupon', 'is_paid', 'get_total')
    inlines = [CartItemInline]
    date_hierarchy = 'created_at'

    def get_cart_info(self, obj):
        """🆔 Информация о корзине"""
        if obj.user:
            return f"👤 {obj.user.username}"
        return f"👥 Анонимная ({obj.session_id[:12]}...)"

    get_cart_info.short_description = "Корзина"

    def get_items_count(self, obj):
        """📊 Количество товаров"""
        return obj.cart_items.count()

    get_items_count.short_description = "Товаров"

    def get_total(self, obj):
        """💰 Общая стоимость"""
        return f"{obj.get_cart_total():.2f} BYN"

    get_total.short_description = "Сумма"

    fieldsets = (
        ('🛒 Информация о корзине', {
            'fields': ('user', 'session_id', 'is_paid', 'get_total')
        }),
        ('🎫 Скидки', {
            'fields': ('coupon',),
            'classes': ('collapse',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    """📋 Товары в заказе"""
    model = OrderItem
    extra = 0
    verbose_name = "Товар в заказе"
    verbose_name_plural = "Товары в заказе"
    readonly_fields = (
        'product', 'kit_variant', 'carpet_color',
        'border_color', 'has_podpyatnik', 'quantity', 'product_price'
    )
    fields = (
        'product', 'kit_variant', 'carpet_color', 'border_color',
        'has_podpyatnik', 'quantity', 'product_price'
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """📦 ИСПРАВЛЕННАЯ админка заказов"""
    # 🔧 ИСПРАВЛЕНО: payment_status добавлен в list_display для возможности редактирования
    list_display = (
        'order_id',
        'customer_name',
        'customer_phone',
        'customer_city',
        'get_delivery_display',
        'payment_status',  # ✅ ДОБАВЛЕНО: теперь payment_status в list_display
        'grand_total',
        'order_date'
    )

    list_filter = ('payment_status', 'delivery_method', 'customer_city', 'order_date')
    search_fields = ('order_id', 'customer_name', 'customer_phone', 'customer_city')

    readonly_fields = (
        'user', 'customer_name', 'customer_phone', 'customer_email', 'customer_city',
        'delivery_method', 'shipping_address', 'order_notes',
        'order_id', 'order_date', 'order_total_price', 'coupon', 'grand_total',
        'get_telegram_resend'
    )

    # ✅ ТЕПЕРЬ РАБОТАЕТ: payment_status есть в list_display, поэтому можно редактировать
    list_editable = ('payment_status',)

    inlines = [OrderItemInline]
    date_hierarchy = 'order_date'

    fieldsets = (
        ('📞 Контактные данные', {
            'fields': ('customer_name', 'customer_phone', 'customer_email', 'customer_city'),
            'description': '📱 Основная информация для связи с клиентом'
        }),
        ('🚚 Доставка', {
            'fields': ('delivery_method', 'shipping_address', 'order_notes'),
            'description': '📦 Способ и адрес доставки заказа'
        }),
        ('📦 Детали заказа', {
            'fields': ('order_id', 'order_date', 'payment_status', 'payment_mode'),
            'description': '🎯 Основная информация о заказе'
        }),
        ('💰 Расчеты', {
            'fields': ('order_total_price', 'coupon', 'grand_total'),
            'description': '💳 Стоимость заказа и примененные скидки'
        }),
        ('🤖 Уведомления', {
            'fields': ('get_telegram_resend',),
            'description': '📱 Повторная отправка уведомлений',
            'classes': ('collapse',)
        }),
    )

    def get_delivery_display(self, obj):
        """🚚 Отображение информации о доставке"""
        if obj.shipping_address:
            return format_html(
                '<span style="color: #007cba;">🚚 {}</span>',
                obj.get_delivery_method_display()  # ✅ Стандартный метод Django
            )
        return format_html('<span style="color: #28a745;">🏪 Самовывоз</span>')

    get_delivery_display.short_description = "Доставка"

    def get_telegram_resend(self, obj):
        """🤖 Кнопка повторной отправки Telegram уведомления"""
        if obj.pk:
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<p><strong>🤖 Повторная отправка в Telegram:</strong></p>'
                '<p style="color: #6c757d; font-size: 12px;">Для повторной отправки уведомления используйте Django shell:</p>'
                '<code style="background: #e9ecef; padding: 5px; border-radius: 3px; display: block; margin: 5px 0;">'
                'python manage.py shell<br>'
                'from accounts.views import send_telegram_notification<br>'
                'from accounts.models import Order<br>'
                'order = Order.objects.get(id={})<br>'
                'send_telegram_notification(order)'
                '</code>'
                '</div>',
                obj.id
            )
        return "Сохраните заказ для получения инструкций"

    get_telegram_resend.short_description = "Telegram уведомления"

    def get_queryset(self, request):
        """🔍 Оптимизация запросов"""
        return super().get_queryset(request).select_related('coupon').prefetch_related('order_items')

    # 🔧 Массовые действия для заказов
    actions = ['mark_as_paid', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']

    def mark_as_paid(self, request, queryset):
        """💰 Отметить как оплаченные"""
        count = queryset.update(payment_status='Оплачен')
        self.message_user(request, f"✅ Отмечено как оплаченные: {count} заказов")

    def mark_as_processing(self, request, queryset):
        """⚙️ Отметить как в обработке"""
        count = queryset.update(payment_status='В обработке')
        self.message_user(request, f"⚙️ Отмечено как в обработке: {count} заказов")

    def mark_as_shipped(self, request, queryset):
        """📮 Отметить как отправленные"""
        count = queryset.update(payment_status='Отправлен')
        self.message_user(request, f"📮 Отмечено как отправленные: {count} заказов")

    def mark_as_delivered(self, request, queryset):
        """✅ Отметить как доставленные"""
        count = queryset.update(payment_status='Доставлен')
        self.message_user(request, f"✅ Отмечено как доставленные: {count} заказов")

    mark_as_paid.short_description = "💰 Отметить как оплаченные"
    mark_as_processing.short_description = "⚙️ Отметить как в обработке"
    mark_as_shipped.short_description = "📮 Отметить как отправленные"
    mark_as_delivered.short_description = "✅ Отметить как доставленные"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """👤 Профили пользователей (только для админов)"""
    list_display = ('user', 'get_user_full_name', 'is_email_verified', 'created_at')
    list_filter = ('is_email_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('user', 'email_token', 'created_at', 'updated_at')

    def get_user_full_name(self, obj):
        """📝 Полное имя пользователя"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or "Не указано"

    get_user_full_name.short_description = "Полное имя"

    fieldsets = (
        ('👤 Пользователь', {
            'fields': ('user', 'is_email_verified', 'email_token')
        }),
        ('📝 Профиль', {
            'fields': ('profile_image', 'bio')
        }),
        ('📅 Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# 🎨 Настройка заголовков админки
admin.site.site_header = "🛒 Автоковрики - Админ-панель"
admin.site.site_title = "Автоковрики"
admin.site.index_title = "Управление интернет-магазином"

# 🎯 Дополнительные настройки
admin.site.empty_value_display = '(Не заполнено)'

# 🔧 ИСПРАВЛЕНИЯ:
# ✅ payment_status добавлен в list_display для возможности редактирования в списке
# ✅ Убран метод get_status_display из list_display (заменен на payment_status)
# ✅ Сохранены все остальные функции админки
# ✅ Добавлены детальные комментарии для понимания

# 💡 ПРИМЕЧАНИЕ:
# Теперь в списке заказов можно редактировать статус напрямую,
# кликнув на поле payment_status в таблице