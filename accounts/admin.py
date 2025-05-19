from django.contrib import admin
from .models import Profile, Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = (
    'product', 'color_variant', 'kit_variant', 'carpet_color', 'border_color', 'has_podpyatnik', 'quantity')


class CartAdmin(admin.ModelAdmin):
    list_display = ('uid', 'user', 'session_id', 'coupon', 'is_paid', 'created_at')  # Заменили 'id' на 'uid'
    list_filter = ('is_paid', 'coupon')
    search_fields = ('user__username', 'session_id')
    readonly_fields = (
    'user', 'session_id', 'coupon', 'is_paid', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_payment_signature')
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
    'product', 'kit_variant', 'color_variant', 'carpet_color', 'border_color', 'has_podpyatnik', 'quantity',
    'product_price')


class OrderAdmin(admin.ModelAdmin):
    list_display = (
    'order_id', 'customer_name', 'customer_phone', 'payment_status', 'delivery_method', 'grand_total', 'order_date')
    list_filter = ('payment_status', 'delivery_method')
    search_fields = ('order_id', 'customer_name', 'customer_phone', 'customer_email')
    readonly_fields = (
    'user', 'customer_name', 'customer_phone', 'customer_email', 'delivery_method', 'shipping_address',
    'order_notes', 'order_id', 'order_date', 'order_total_price', 'coupon', 'grand_total')
    inlines = [OrderItemInline]
    date_hierarchy = 'order_date'

    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('user', 'customer_name', 'customer_phone', 'customer_email')
        }),
        ('Информация о доставке', {
            'fields': ('delivery_method', 'shipping_address', 'order_notes')
        }),
        ('Информация о заказе', {
            'fields': ('order_id', 'order_date', 'payment_status', 'payment_mode', 'tracking_code')
        }),
        ('Информация о стоимости', {
            'fields': ('order_total_price', 'coupon', 'grand_total')
        }),
    )


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_email_verified')
    list_filter = ('is_email_verified',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'email_token', 'created_at', 'updated_at')


# Register your models here.
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)