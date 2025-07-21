from django.db import models
from products.models import Product, Category

# --- Менеджеры для фильтрации ---

class BoatCategoryManager(models.Manager):
    """
    Менеджер для фильтрации категорий, которые относятся только к лодкам.
    """
    def get_queryset(self):
        return super().get_queryset().filter(type='boat')

class BoatProductManager(models.Manager):
    """
    Менеджер для фильтрации продуктов, которые относятся только к лодкам.
    """
    def get_queryset(self):
        return super().get_queryset().filter(type='boat')

# --- Proxy-модели ---

class BoatCategory(Category):
    """
    Proxy-модель для категорий лодок.
    Не создает новую таблицу в БД, а предоставляет интерфейс
    к существующей модели Category, отфильтрованный по типу 'boat'.
    """
    objects = BoatCategoryManager()

    class Meta:
        proxy = True
        verbose_name = 'Категория лодок'
        verbose_name_plural = '⛵ Категории лодок'

class BoatProduct(Product):
    """
    Proxy-модель для товаров-лодок.
    Не создает новую таблицу в БД, а предоставляет интерфейс
    к существующей модели Product, отфильтрованный по типу 'boat'.
    """
    objects = BoatProductManager()

    class Meta:
        proxy = True
        verbose_name = 'Товар (лодка)'
        verbose_name_plural = '⛵ Товары (лодки)'