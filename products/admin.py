from django.contrib import admin
from .models import *

# Register your models here.


admin.site.register(Category)
admin.site.register(Coupon)

class ProductImageAdmin(admin.StackedInline):
    model = ProductImage


class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'price']
    inlines = [ProductImageAdmin]


@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ['color_name', 'price']
    model = ColorVariant


@admin.register(KitVariant)
class KitVariantAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'price_modifier', 'order', 'image']
    list_filter = ['name']
    search_fields = ['name', 'code']
    model = KitVariant


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_code', 'display_order']
    model = Color


admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
admin.site.register(ProductReview)
admin.site.register(Wishlist)