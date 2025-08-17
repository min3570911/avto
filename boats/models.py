# 📁 boats/models.py - ИСПРАВЛЕННАЯ И УНИФИЦИРОВАННАЯ ВЕРСИЯ
# 🛥️ BoatProduct - ТОЧНАЯ КОПИЯ Product, но без комплектаций
# ✅ СОВМЕСТИМОСТЬ: Максимальная совместимость с products.models.Product
# 🔧 ОТЛИЧИЯ: Только размеры коврика вместо комплектаций

import uuid
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from base.models import BaseModel
from products.storage import OverwriteStorage


class BoatCategory(BaseModel):
    """
    🛥️ Категории лодок (отдельные от автомобильных)
    ПРИМЕРЫ: Yamaha, Mercury, Suzuki, Honda...
    """

    # 🏷️ Основные поля (как у Category)
    category_name = models.CharField(
        max_length=200,
        verbose_name="Название категории лодок",
        help_text="Например: Yamaha, Mercury, Suzuki"
    )

    slug = models.SlugField(
        unique=True,
        max_length=255,
        verbose_name="URL-адрес",
        help_text="Автоматически генерируется из названия"
    )

    # 🖼️ Изображение категории
    category_image = models.ImageField(
        upload_to="boat_categories",
        storage=OverwriteStorage(),
        null=True,
        blank=True,
        verbose_name="Изображение категории",
        help_text="Логотип бренда лодки. Рекомендуемый размер: 400x300px"
    )

    # 📝 Описание (CKEditor как у продуктов)
    description = CKEditor5Field(
        blank=True,
        null=True,
        verbose_name="Описание категории",
        help_text="Подробное описание категории лодок",
        config_name='default'
    )

    # 🔍 SEO поля (как у Category)
    page_title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Заголовок страницы (Title)",
        help_text="SEO заголовок для страницы категории"
    )

    meta_description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Meta Description",
        help_text="SEO описание для поисковых систем"
    )

    # ⚙️ Управление (как у Category)
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активная категория",
        help_text="Показывать категорию на сайте"
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок отображения",
        help_text="Чем меньше число, тем выше в списке"
    )

    def save(self, *args, **kwargs):
        """🔧 Автогенерация slug"""
        if not self.slug:
            self.slug = slugify(self.category_name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """🌐 URL категории лодок"""
        return reverse('boats:product_list_by_category', kwargs={'slug': self.slug})

    def get_products_count(self):
        """📊 Количество товаров в категории (ИСПРАВЛЕНО)"""
        # Просто считаем все товары, так как у BoatProduct нет поля is_active
        return self.products.count()

    def __str__(self):
        """🛥️ Отображение в админке"""
        status = "" if self.is_active else " (неактивна)"
        return f"🛥️ {self.category_name}{status}"

    class Meta:
        verbose_name = "🛥️ Категория лодок"
        verbose_name_plural = "🛥️ Категории лодок"
        ordering = ['display_order', 'category_name']


class BoatProduct(BaseModel):
    """
    🛥️ УНИФИЦИРОВАННАЯ модель товаров лодок

    ✅ ТОЧНАЯ КОПИЯ products.models.Product, НО:
    - Связь с BoatCategory (вместо Category)
    - Размеры коврика boat_mat_length/width (вместо комплектаций)
    - БЕЗ связи с KitVariant
    - БЕЗ поля has_podpyatnik
    """

    # 🏷️ ОСНОВНАЯ ИНФОРМАЦИЯ (ИДЕНТИЧНО Product)
    product_name = models.CharField(
        max_length=200,
        verbose_name="Название товара",
        help_text="Например: Коврик EVA для Yamaha F150"
    )

    slug = models.SlugField(
        unique=True,
        max_length=255,
        verbose_name="URL-адрес",
        help_text="Автоматически генерируется из названия"
    )

    # 📂 КАТЕГОРИЯ (связь с BoatCategory)
    category = models.ForeignKey(
        BoatCategory,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория лодки",
        help_text="Выберите бренд лодки"
    )

    # 💰 ЦЕНА (IntegerField как у Product)
    price = models.IntegerField(
        verbose_name="Базовая цена",
        null=True,
        blank=True,
        default=0,
        help_text="Цена в рублях (целое число)"
    )

    # 📝 ОПИСАНИЕ (CKEditor5Field как у Product)
    product_desription = CKEditor5Field(
        verbose_name="Описание товара",
        help_text="Подробное описание товара с возможностью форматирования",
        config_name='default'
    )

    # ⭐ УПРАВЛЕНИЕ (как у Product)
    newest_product = models.BooleanField(
        default=False,
        verbose_name="Новый товар"
    )

    # 🆔 АРТИКУЛ (как у Product)
    product_sku = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Артикул товара",
        help_text="Уникальный код товара для импорта и учета"
    )

    # 🛥️ РАЗМЕРЫ ЛОДОЧНОГО КОВРИКА (УНИКАЛЬНО ДЛЯ ЛОДОК)
    boat_mat_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Длина коврика (см)",
        help_text="Длина коврика для лодки в сантиметрах"
    )

    boat_mat_width = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Ширина коврика (см)",
        help_text="Ширина коврика для лодки в сантиметрах"
    )

    # 🔍 SEO ПОЛЯ (как у Product)
    page_title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Заголовок страницы (Title)",
        help_text="SEO заголовок для страницы товара"
    )

    meta_description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Meta Description",
        help_text="SEO описание для поисковых систем"
    )

    def save(self, *args, **kwargs):
        """🔧 Автогенерация slug и SKU"""
        if not self.slug:
            self.slug = slugify(self.product_name, allow_unicode=True)

        # 🆔 Автогенерация SKU если не указан
        if not self.product_sku:
            # Используем первые 3 буквы категории + timestamp
            category_prefix = self.category.category_name[:3].upper()
            import time
            timestamp = str(int(time.time()))[-6:]  # Последние 6 цифр
            self.product_sku = f"BOAT-{category_prefix}-{timestamp}"

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """🌐 URL товара лодки"""
        return reverse('boats:product_detail', kwargs={'slug': self.slug})

    def get_mat_dimensions(self):
        """📏 Получить размеры коврика в формате строки"""
        if self.boat_mat_length and self.boat_mat_width:
            return f"{self.boat_mat_length}×{self.boat_mat_width} см"
        elif self.boat_mat_length:
            return f"Длина: {self.boat_mat_length} см"
        elif self.boat_mat_width:
            return f"Ширина: {self.boat_mat_width} см"
        return "Размеры уточняйте"

    def get_dimensions_display(self):
        """📏 Объект с размерами для шаблонов"""
        if self.boat_mat_length and self.boat_mat_width:
            return {
                'length': self.boat_mat_length,
                'width': self.boat_mat_width,
                'formatted': f"{self.boat_mat_length}×{self.boat_mat_width} см",
                'area': round(self.boat_mat_length * self.boat_mat_width / 10000, 2)  # м²
            }
        return None

    def get_display_price(self):
        """💰 Отформатированная цена"""
        if self.price:
            return f"{self.price:,}".replace(',', ' ')
        return "Цена по запросу"

    def get_main_image(self):
        """🖼️ Получить главное изображение"""
        main_image = self.images.filter(is_main=True).first()
        if main_image:
            return main_image
        return self.images.first()

    def __str__(self):
        """🛥️ Отображение в админке"""
        dimensions = ""
        if self.boat_mat_length and self.boat_mat_width:
            dimensions = f" ({self.boat_mat_length}×{self.boat_mat_width}см)"
        return f"🛥️ {self.product_name}{dimensions}"

    class Meta:
        verbose_name = "🛥️ Товар (лодка)"
        verbose_name_plural = "🛥️ Товары (лодки)"
        ordering = ['-created_at', 'product_name']
        indexes = [
            models.Index(fields=['category', 'newest_product']),
            models.Index(fields=['slug']),
            models.Index(fields=['product_sku']),
        ]


class BoatProductImage(BaseModel):
    """
    🖼️ Изображения лодочных товаров
    ИДЕНТИЧНО products.models.ProductImage
    """

    product = models.ForeignKey(
        BoatProduct,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Товар лодки"
    )

    image = models.ImageField(
        upload_to="boat_products",
        storage=OverwriteStorage(),
        verbose_name="Изображение",
        help_text="Фото лодочного коврика. Рекомендуемый размер: 800x600px"
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Alt текст",
        help_text="Описание изображения для SEO и доступности"
    )

    is_main = models.BooleanField(
        default=False,
        verbose_name="Главное изображение",
        help_text="Основное изображение товара для каталога"
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок отображения",
        help_text="Порядок в галерее (меньше число = выше)"
    )

    def save(self, *args, **kwargs):
        """🔧 Автоматическая генерация alt_text"""
        if not self.alt_text and self.product:
            self.alt_text = f"Изображение {self.product.product_name}"
        super().save(*args, **kwargs)

    def __str__(self):
        main_indicator = "📌 " if self.is_main else ""
        return f"{main_indicator}Фото: {self.product.product_name}"

    class Meta:
        verbose_name = "🖼️ Изображение лодочного товара"
        verbose_name_plural = "🖼️ Изображения лодочных товаров"
        ordering = ['display_order', 'created_at']