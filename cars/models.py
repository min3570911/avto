from django.db import models
from products.models import Product, Category

# --- Менеджеры для фильтрации ---

class CarCategoryManager(models.Manager):
    """
    Менеджер для фильтрации категорий, которые относятся только к автомобилям.
    """
    def get_queryset(self):
        return super().get_queryset().filter(type='auto')

class CarProductManager(models.Manager):
    """
    Менеджер для фильтрации продуктов, которые относятся только к автомобилям.
    """
    def get_queryset(self):
        return super().get_queryset().filter(type='auto')

# --- Proxy-модели ---

class CarCategory(Category):
    """
    Proxy-модель для категорий автомобилей.
    Не создает новую таблицу в БД, а предоставляет интерфейс
    к существующей модели Category, отфильтрованный по типу 'auto'.
    """
    objects = CarCategoryManager()

    class Meta:
        proxy = True
        verbose_name = 'Категория авто'
        verbose_name_plural = '🚗 Категории авто'

class CarProduct(Product):
    """
    Proxy-модель для товаров-автомобилей.
    Не создает новую таблицу в БД, а предоставляет интерфейс
    к существующей модели Product, отфильтрованный по типу 'auto'.
    """
    objects = CarProductManager()

    class Meta:
        proxy = True
        verbose_name = 'Товар (авто)'
        verbose_name_plural = '🚗 Товары (авто)'