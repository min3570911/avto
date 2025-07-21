from django.contrib import admin
from .models import BoatCategory, BoatProduct
from products.admin import ProductAdmin, CategoryAdmin

@admin.register(BoatCategory)
class BoatCategoryAdmin(CategoryAdmin):
    """
    Настройки админ-панели для категорий лодок.
    Наследует всю логику от основного CategoryAdmin.
    """
    pass

@admin.register(BoatProduct)
class BoatProductAdmin(ProductAdmin):
    """
    Настройки админ-панели для товаров-лодок.
    Наследует всю логику от основного ProductAdmin.
    """
    # Здесь можно будет добавлять специфичные для лодок поля в будущем,
    # например, отображение размеров в списке.
    pass