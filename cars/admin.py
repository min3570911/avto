from django.contrib import admin
from .models import CarCategory, CarProduct
from products.admin import ProductAdmin, CategoryAdmin

@admin.register(CarCategory)
class CarCategoryAdmin(CategoryAdmin):
    """
    Настройки админ-панели для категорий автомобилей.
    Наследует всю логику от основного CategoryAdmin.
    """
    pass

@admin.register(CarProduct)
class CarProductAdmin(ProductAdmin):
    """
    Настройки админ-панели для товаров-автомобилей.
    Наследует всю логику от основного ProductAdmin,
    включая инлайны для изображений и комплектаций.
    """
    pass