from django.contrib import admin
from .models import BoatCategory, BoatProduct
from products.admin import ProductAdmin, CategoryAdmin

@admin.register(BoatCategory)
class BoatCategoryAdmin(CategoryAdmin):
    """
    Админка для категорий лодок.
    Наследует всю логику от CategoryAdmin, но показывает только лодки.
    """
    def get_queryset(self, request):
        return super().get_queryset(request).filter(type='boat')

@admin.register(BoatProduct)
class BoatProductAdmin(ProductAdmin):
    """
    Админка для товаров-лодок.
    Наследует всю логику от ProductAdmin, но показывает только лодки
    и использует правильные поля для них.
    """
    # ИСПРАВЛЕНО: Используем метод get_boat_dimensions, как в оригинале
    list_display = [
        'get_main_image_preview',
        'product_name',
        'product_sku',
        'category',
        'display_price',
        'get_boat_dimensions',  # <-- ПРАВИЛЬНЫЙ МЕТОД
        'has_main_image_status',
        'newest_product'
    ]

    # ИСПРАВЛЕНО: Используем поля boat_mat_width и boat_mat_length для поиска
    search_fields = [
        'product_name',
        'product_sku',
        'product_desription',
        'boat_mat_width',   # <-- ПРАВИЛЬНОЕ ПОЛЕ
        'boat_mat_length'   # <-- ПРАВИЛЬНОЕ ПОЛЕ
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(type='boat')