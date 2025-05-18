from django.contrib import admin
from .models import *


# Register your models here.

class ProductImageAdmin(admin.StackedInline):
    model = ProductImage
    verbose_name = "Изображение товара"
    verbose_name_plural = "Изображения товара"


class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'category', 'price', 'newest_product']
    list_filter = ['category', 'newest_product']
    search_fields = ['product_name', 'product_desription']
    inlines = [ProductImageAdmin]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'slug']
    prepopulated_fields = {'slug': ('category_name',)}


@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ['color_name', 'price']
    model = ColorVariant


@admin.register(KitVariant)
class KitVariantAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'price_modifier', 'order', 'is_option']
    list_filter = ['is_option']
    search_fields = ['name', 'code']
    model = KitVariant


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_type', 'hex_code', 'color_preview', 'is_available', 'display_order']
    list_filter = ['color_type', 'is_available']
    list_editable = ['display_order', 'is_available']
    search_fields = ['name']
    ordering = ['color_type', 'display_order']

    def color_preview(self, obj):
        """Показывает цветной квадрат с цветом в админке"""
        return mark_safe(
            f'<div style="width:20px; height:20px; background-color:{obj.hex_code}; border:1px solid #666;"></div>')

    color_preview.short_description = "Цвет"

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'hex_code', 'color_type', 'display_order')
        }),
        ('Изображения', {
            'fields': ('carpet_image', 'border_image', 'carpet_preview', 'border_preview'),
            'description': 'Загрузите изображения для визуализации цвета в зависимости от типа применения.'
        }),
        ('Доступность', {
            'fields': ('is_available',),
            'description': 'Если материал недоступен, отключите этот флаг'
        }),
    )

    readonly_fields = ['carpet_preview', 'border_preview']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['coupon_code', 'discount_amount', 'minimum_amount', 'is_expired']
    list_filter = ['is_expired']
    list_editable = ['is_expired', 'discount_amount', 'minimum_amount']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'stars', 'date_added']
    list_filter = ['stars', 'date_added']
    search_fields = ['content', 'user__username', 'product__product_name']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'kit_variant', 'added_on']
    list_filter = ['added_on', 'has_podpyatnik']
    search_fields = ['user__username', 'product__product_name']


admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)