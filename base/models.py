# 📁 base/models.py - Абстрактные базовые модели
# 🔧 Общие поля и методы для всех моделей проекта

import uuid
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


class BaseModel(models.Model):
    """
    🔧 Абстрактная базовая модель со стандартными полями

    Содержит общие поля которые есть у ВСЕХ моделей в проекте
    """
    uid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Уникальный ID"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения"
    )

    class Meta:
        abstract = True  # ✅ Не создает таблицу!


class BaseCategory(BaseModel):
    """
    🔧 Абстрактная модель категории для автомобилей и лодок

    Общие поля для всех типов категорий
    """
    category_name = models.CharField(
        max_length=200,
        verbose_name="Название категории",
        help_text="Основное название категории"
    )

    slug = models.SlugField(
        unique=True,
        max_length=255,
        verbose_name="URL-адрес",
        help_text="Автоматически генерируется из названия"
    )

    # 📝 SEO поля
    page_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="SEO заголовок",
        help_text="Заголовок страницы для поисковиков"
    )

    meta_description = models.TextField(
        blank=True,
        max_length=160,
        verbose_name="SEO описание",
        help_text="Описание страницы для поисковиков (до 160 символов)"
    )

    # 📊 Управление отображением
    display_order = models.IntegerField(
        default=0,
        verbose_name="Порядок сортировки",
        help_text="Меньше число = выше в списке"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
        help_text="Показывать категорию на сайте"
    )

    def save(self, *args, **kwargs):
        """💾 Автогенерация slug при сохранении"""
        if not self.slug:
            self.slug = slugify(self.category_name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """🌐 URL категории - переопределяется в дочерних моделях"""
        raise NotImplementedError("Переопределите get_absolute_url в дочерней модели")

    class Meta:
        abstract = True  # ✅ Не создает таблицу!
        ordering = ['display_order', 'category_name']


class BaseProduct(BaseModel):
    """
    🔧 Абстрактная модель товара для автомобилей и лодок

    Содержит ВСЕ общие поля товаров любого типа
    """
    # 🏷️ Основная информация
    product_name = models.CharField(
        max_length=200,
        verbose_name="Название товара",
        help_text="Полное название товара"
    )

    slug = models.SlugField(
        unique=True,
        max_length=255,
        verbose_name="URL-адрес",
        help_text="Автоматически генерируется из названия"
    )

    # 💰 Ценообразование
    price = models.IntegerField(
        verbose_name="Базовая цена",
        null=True,
        blank=True,
        default=0,
        help_text="Цена в рублях (целое число)"
    )

    # 📝 Контент
    product_desription = CKEditor5Field(
        verbose_name="Описание товара",
        help_text="Подробное описание с форматированием",
        config_name='default'
    )

    # 🆔 Артикул и управление
    product_sku = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Артикул товара",
        help_text="Уникальный код для импорта и учета"
    )

    newest_product = models.BooleanField(
        default=False,
        verbose_name="Новый товар",
        help_text="Показывать в разделе новинок"
    )

    # 📈 SEO оптимизация  
    page_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="SEO заголовок",
        help_text="Заголовок страницы для поисковиков"
    )

    meta_description = models.TextField(
        blank=True,
        max_length=160,
        verbose_name="SEO описание",
        help_text="Описание страницы для поисковиков"
    )

    def save(self, *args, **kwargs):
        """💾 Автогенерация slug при сохранении"""
        if not self.slug:
            self.slug = slugify(self.product_name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """🌐 URL товара - переопределяется в дочерних моделях"""
        raise NotImplementedError("Переопределите get_absolute_url в дочерней модели")

    def get_main_image(self):
        """🖼️ Получение главного изображения - переопределяется в дочерних моделях"""
        raise NotImplementedError("Переопределите get_main_image в дочерней модели")

    def get_all_images(self):
        """🖼️ Все изображения товара - переопределяется в дочерних моделях"""
        raise NotImplementedError("Переопределите get_all_images в дочерней модели")

    class Meta:
        abstract = True  # ✅ Не создает таблицу!
        ordering = ['-newest_product', 'product_name']

# 🎯 РЕЗУЛЬТАТ:
#
# ✅ BaseModel - общие поля для ВСЕХ моделей:
# - uid (UUID primary key)
# - created_at, updated_at (временные метки)
#
# ✅ BaseCategory - общие поля для категорий:
# - category_name, slug (основные поля)
# - page_title, meta_description (SEO)
# - display_order, is_active (управление)
# - автогенерация slug
#
# ✅ BaseProduct - общие поля для товаров:
# - product_name, slug (основные поля)
# - price (ценообразование)
# - product_desription (CKEditor5)
# - product_sku, newest_product (управление)
# - page_title, meta_description (SEO)
# - автогенерация slug
# - абстрактные методы для изображений и URL
#
# 🔧 ИСПОЛЬЗОВАНИЕ:
# products/models.py: class Product(BaseProduct)
# boats/models.py: class BoatProduct(BaseProduct)
# products/models.py: class Category(BaseCategory)
# boats/models.py: class BoatCategory(BaseCategory)