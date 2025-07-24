# 📁 boats/models.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
# 🛥️ Proxy-модели для работы с лодками
# 🔧 ИСПРАВЛЕНО: Правильные названия классов и импорты

from django.db import models
from products.models import Product, Category  # ⚠️ ВРЕМЕННО: пока есть products, потом заменим на references

# --- Менеджеры для фильтрации ---

class BoatCategoryManager(models.Manager):
    """
    🛥️ Менеджер для фильтрации категорий лодок.
    """
    def get_queryset(self):
        return super().get_queryset().filter(category_type='boats')

class BoatProductManager(models.Manager):
    """
    🛥️ Менеджер для фильтрации товаров-лодок.
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

    def get_boat_dimensions(self):
        """
        🛥️ Получаем размеры лодочного коврика
        Специальный метод для лодок
        """
        if self.boat_mat_length and self.boat_mat_width:
            return f"{self.boat_mat_length}×{self.boat_mat_width} см"
        elif self.boat_mat_length:
            return f"Длина: {self.boat_mat_length} см"
        elif self.boat_mat_width:
            return f"Ширина: {self.boat_mat_width} см"
        return None

    class Meta:
        proxy = True
        verbose_name = '🛥️ Товар (лодка)'
        verbose_name_plural = '🛥️ Товары (лодки)'