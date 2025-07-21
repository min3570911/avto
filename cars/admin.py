from django.contrib import admin
from .models import CarCategory, CarProduct
from products.admin import ProductAdmin, CategoryAdmin


@admin.register(CarCategory)
class CarCategoryAdmin(CategoryAdmin):
    """
    Админка для категорий автомобилей.
    Наследует всю логику от CategoryAdmin, но показывает только автомобили.
    """

    def get_queryset(self, request):
        # Показываем только категории с типом 'auto'
        return super().get_queryset(request).filter(type='auto')


@admin.register(CarProduct)
class CarProductAdmin(ProductAdmin):
    """
    Админка для товаров-автомобилей.
    Наследует всю логику от ProductAdmin, но показывает только автомобили.
    """
    # Убираем поля лодок из списка
    list_display = [
        'get_main_image_preview',
        'product_name',
        'product_sku',
        'category',
        'display_price',
        'has_main_image_status',
        'storage_status',
        'newest_product'
    ]

    # Убираем поля лодок из поиска
    search_fields = [
        'product_name',
        'product_sku',
        'product_desription'
    ]

    def get_queryset(self, request):
        # Показываем только товары с типом 'auto'
        return super().get_queryset(request).filter(type='auto')