# 📁 boats/models.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
# 🛥️ Proxy-модели для работы с лодками
# ✅ ИСПРАВЛЕНО: Правильная фильтрация по category_type='boats'

from django.db import models
from products.models import Product, Category

# --- Менеджеры для фильтрации ---

class BoatCategoryManager(models.Manager):
    """
    🛥️ Менеджер для фильтрации категорий лодок.
    ✅ ИСПРАВЛЕНО: Используем category_type='boats' вместо type='boat'
    """
    def get_queryset(self):
        return super().get_queryset().filter(category_type='boats')

class BoatProductManager(models.Manager):
    """
    🛥️ Менеджер для фильтрации товаров-лодок.
    ✅ ИСПРАВЛЕНО: Используем правильное поле для фильтрации
    """
    def get_queryset(self):
        # Фильтруем товары, которые принадлежат к категориям лодок
        return super().get_queryset().filter(category__category_type='boats')

# --- Proxy-модели ---

class BoatCategory(Category):
    """
    🛥️ Proxy-модель для категорий лодок.
    Не создает новую таблицу в БД, а предоставляет интерфейс
    к существующей модели Category, отфильтрованный по типу 'boats'.
    """
    objects = BoatCategoryManager()

    def save(self, *args, **kwargs):
        """🔒 Автоматически устанавливаем тип 'boats' при сохранении"""
        self.category_type = 'boats'
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = '🛥️ Категория лодок'
        verbose_name_plural = '🛥️ Категории лодок'

class BoatProduct(Product):
    """
    🛥️ Proxy-модель для товаров-лодок.
    Не создает новую таблицу в БД, а предоставляет интерфейс
    к существующей модели Product, отфильтрованный для лодок.
    """
    objects = BoatProductManager()

    def save(self, *args, **kwargs):
        """
        🔒 Проверяем, что товар относится к категории лодок при сохранении
        """
        if self.category and self.category.category_type != 'boats':
            raise ValueError("Товар может быть сохранен только в категории лодок")
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = '🛥️ Товар (лодка)'
        verbose_name_plural = '🛥️ Товары (лодки)'