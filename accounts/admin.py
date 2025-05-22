# accounts/admin.py - замените полностью на этот код:

from django.contrib import admin
from .models import Profile, Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    verbose_name = "Товар в корзине"
    verbose_name_plural = "Товары в корзине"
    readonly_fields = (
        'product', 'color_variant', 'kit_variant', 'carpet_color',
        'border_color', 'has_podpyatnik', 'quantity'
    )
    fields = (
        'product', 'kit_variant', 'carpet_color', 'border_color',
        'has_podpyatnik', 'quantity'
    )


class CartAdmin(admin.ModelAdmin):
    list_display = ('get_cart_display', 'get_user_info', 'get_items_count', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'session_id')
    readonly_fields = (
        'user', 'session_id', 'coupon', 'is_paid', 'razorpay_order_id',
        'razorpay_payment_id', 'razorpay_payment_signature'
    )
    inlines = [CartItemInline]

    def get_cart_display(self, obj):
        """Отображение корзины"""
        return f"Корзина {str(obj.uid)[:8]}..."

    get_cart_display.short_description = "Корзина"

    def get_user_info(self, obj):
        """Информация о пользователе"""
        if obj.user:
            return f"{obj.user.username} ({obj.user.first_name} {obj.user.last_name})"
        return f"Анонимный (сессия: {obj.session_id[:8]}...)"

    get_user_info.short_description = "Пользователь"

    def get_items_count(self, obj):
        """Количество товаров"""
        return obj.cart_items.count()

    get_items_count.short_description = "Товаров"

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    verbose_name = "Товар в заказе"
    verbose_name_plural = "Товары в заказе"
    readonly_fields = (
        'product', 'kit_variant', 'color_variant', 'carpet_color',
        'border_color', 'has_podpyatnik', 'quantity', 'product_price'
    )
    fields = (
        'product', 'kit_variant', 'carpet_color', 'border_color',
        'has_podpyatnik', 'quantity', 'product_price'
    )


class OrderAdmin(admin.ModelAdmin):
    # 🔄 Список отображения БЕЗ email
    list_display = (
        'order_id',
        'customer_name',
        'customer_phone',
        'customer_city',
        'get_delivery_display',
        'payment_status',
        'grand_total',
        'order_date'
    )

    # 🔍 Фильтры на русском
    list_filter = ('payment_status', 'delivery_method', 'customer_city', 'order_date')

    # 🔍 Поиск БЕЗ email
    search_fields = ('order_id', 'customer_name', 'customer_phone', 'customer_city')

    # 📝 Readonly поля БЕЗ email
    readonly_fields = (
        'user', 'customer_name', 'customer_phone', 'customer_city',
        'delivery_method', 'shipping_address', 'order_notes',
        'order_id', 'order_date', 'order_total_price', 'coupon', 'grand_total'
    )

    # 📝 Редактируемые поля
    list_editable = ('payment_status',)

    inlines = [OrderItemInline]
    date_hierarchy = 'order_date'

    # 🎨 Группы полей БЕЗ email
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('user', 'customer_name', 'customer_phone', 'customer_city'),
            'description': 'Контактные данные клиента для связи'
        }),
        ('Информация о доставке', {
            'fields': ('delivery_method', 'shipping_address', 'order_notes'),
            'description': 'Способ доставки и адрес. Если адрес не указан - самовывоз'
        }),
        ('Данные заказа', {
            'fields': ('order_id', 'order_date', 'payment_status', 'payment_mode', 'tracking_code'),
            'description': 'Основная информация о заказе'
        }),
        ('Стоимость', {
            'fields': ('order_total_price', 'coupon', 'grand_total'),
            'description': 'Расчет стоимости заказа'
        }),
    )

    def get_delivery_display(self, obj):
        """🚚 Отображение информации о доставке"""
        if obj.shipping_address:
            return f"🚚 {obj.get_delivery_method_display()}"
        return "🏪 Самовывоз"

    get_delivery_display.short_description = "Доставка"
    get_delivery_display.admin_order_field = 'delivery_method'

    def get_queryset(self, request):
        """🔍 Оптимизация запросов"""
        return super().get_queryset(request).select_related('user', 'coupon')

    # 🎨 Цветовое выделение в зависимости от статуса
    def get_list_display_links(self, request, list_display):
        return ('order_id',)

    # 🔍 Действия для заказов
    actions = ['mark_as_paid', 'mark_as_processing', 'mark_as_shipped']

    def mark_as_paid(self, request, queryset):
        """Отметить как оплаченные"""
        queryset.update(payment_status='Оплачен')
        self.message_user(request, f"Отмечено как оплаченные: {queryset.count()} заказов")

    mark_as_paid.short_description = "Отметить как оплаченные"

    def mark_as_processing(self, request, queryset):
        """Отметить как в обработке"""
        queryset.update(payment_status='В обработке')
        self.message_user(request, f"Отмечено как в обработке: {queryset.count()} заказов")

    mark_as_processing.short_description = "Отметить как в обработке"

    def mark_as_shipped(self, request, queryset):
        """Отметить как отправленные"""
        queryset.update(payment_status='Отправлен')
        self.message_user(request, f"Отмечено как отправленные: {queryset.count()} заказов")

    mark_as_shipped.short_description = "Отметить как отправленные"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_user_full_name', 'is_email_verified', 'created_at')
    list_filter = ('is_email_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('user', 'email_token', 'created_at', 'updated_at')

    def get_user_full_name(self, obj):
        """Полное имя пользователя"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or "Не указано"

    get_user_full_name.short_description = "Полное имя"

    fieldsets = (
        ('Пользователь', {
            'fields': ('user', 'is_email_verified', 'email_token')
        }),
        ('Профиль', {
            'fields': ('profile_image', 'bio', 'shipping_address')
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


# 📝 Регистрируем модели с русскими названиями
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)

# 🎨 Настройка заголовков админки на русском
admin.site.site_header = "🛒 Управление интернет-магазином"
admin.site.site_title = "Админ-панель"
admin.site.index_title = "Добро пожаловать в панель управления"

# 🎨 Дополнительные настройки
admin.site.empty_value_display = '(Не заполнено)'