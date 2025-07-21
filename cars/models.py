# 📁 cars/models.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
# 🚗 Proxy-модели для работы с автомобилями
# ✅ ИСПРАВЛЕНО: Правильная фильтрация по category_type='cars'

from django.db import models
from products.models import Product, Category

# --- Менеджеры для фильтрации ---

class CarCategoryManager(models.Manager):
    """
    🚗 Менеджер для фильтрации категорий автомобилей.
    ✅ ИСПРАВЛЕНО: Используем category_type='cars' вместо type='auto'
    """
    def get_queryset(self):
        return super().get_queryset().filter(category_type='cars')

class CarProductManager(models.Manager):
    """
    🚗 Менеджер для фильтрации товаров-автомобилей.
    ✅ ИСПРАВЛЕНО: Используем правильное поле для фильтрации
    """
    def get_queryset(self):
        # Фильтруем товары, которые принадлежат к категориям автомобилей
        return super().get_queryset().filter(category__category_type='cars')

# --- Proxy-модели ---

class CarCategory(Category):
    """
    🚗 Proxy-модель для категорий автомобилей.
    Не создает новую таблицу в БД, а предоставляет интерфейс
    к существующей модели Category, отфильтрованный по типу 'cars'.
    """
    objects = CarCategoryManager()

    def save(self, *args, **kwargs):
        """🔒 Автоматически устанавливаем тип 'cars' при сохранении"""
        self.category_type = 'cars'
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = '🚗 Категория авто'
        verbose_name_plural = '🚗 Категории авто'

class CarProduct(Product):
    """
    🚗 Proxy-модель для товаров-автомобилей.
    Не создает новую таблицу в БД, а предоставляет интерфейс
    к существующей модели Product, отфильтрованный для автомобилей.
    """
    objects = CarProductManager()

    def save(self, *args, **kwargs):
        """
        🔒 Проверяем, что товар относится к категории авто при сохранении
        """
        if self.category and self.category.category_type != 'cars':
            raise ValueError("Товар может быть сохранен только в категории автомобилей")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = '🚗 Товар (авто)'
        verbose_name_plural = '🚗 Товары (авто)'