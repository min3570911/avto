# 📁 boats/models.py - УНИФИЦИРОВАННЫЕ МОДЕЛИ ЛОДОК
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
        """📊 Количество товаров в категории"""
        return self.products.filter(is_active=True).count()

    def __str__(self):
        """🛥️ Отображение в админке"""
        status = "" if self.is_active else " (неактивна)"
        return f"🛥️ {self.category_name}{status}"

    class Meta:
        verbose_name = "🛥️ Категория лодок"
        verbose_name_plural = "🛥️ Категории лодок"
        ordering = ['display_order', 'category_name']


from base.models import BaseProduct
from django.contrib.contenttypes.fields import GenericRelation


class BoatProduct(BaseProduct):
    """🛥️ Товар для лодки (наследует общие поля от BaseProduct)"""
    category = models.ForeignKey(
        BoatCategory,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория лодки"
    )

    # Уникальные поля для лодок
    boat_mat_length = models.PositiveIntegerField(null=True, blank=True, verbose_name="Длина коврика (см)")
    boat_mat_width = models.PositiveIntegerField(null=True, blank=True, verbose_name="Ширина коврика (см)")

    # Связь с универсальными отзывами
    reviews = GenericRelation(
        'common.ProductReview',
        object_id_field='object_id',
        content_type_field='content_type'
    )

    # Связь с универсальным избранным
    wishlisted_by = GenericRelation(
        'common.Wishlist',
        object_id_field='object_id',
        content_type_field='content_type'
    )

    def get_mat_dimensions(self):
        """📏 Получить размеры коврика в формате строки"""
        if self.boat_mat_length and self.boat_mat_width:
            return f"{self.boat_mat_length}×{self.boat_mat_width} см"
        return None

    def __str__(self):
        """🛥️ Отображение в админке"""
        dimensions = self.get_mat_dimensions()
        if dimensions:
            return f"🛥️ {self.product_name} ({dimensions})"
        return f"🛥️ {self.product_name}"

    class Meta:
        verbose_name = "🛥️ Товар (лодка)"
        verbose_name_plural = "🛥️ Товары (лодки)"
        ordering = ['-created_at', 'product_name']
        db_table = 'boats_boatproduct'


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

# 🔧 ИТОГОВЫЕ КОММЕНТАРИИ:
#
# ✅ УНИФИКАЦИЯ ЗАВЕРШЕНА:
# • BoatProduct - точная копия Product (без комплектаций)
# • Все поля совпадают по типам и названиям
# • Размеры коврика boat_mat_length/width вместо KitVariant
# • CKEditor5Field для описания (как у Product)
# • IntegerField для цены (как у Product)
# • Идентичные SEO поля
# • Идентичные методы отображения
#
# 🗄️ СОЗДАВАЕМЫЕ ТАБЛИЦЫ:
# • boats_boatcategory - категории лодок
# • boats_boatproduct - унифицированные товары лодок
# • boats_boatproductimage - изображения товаров
#
# 📋 СЛЕДУЮЩИЕ ШАГИ:
# 1. Создать миграцию: python manage.py makemigrations boats
# 2. Применить миграцию: python manage.py migrate boats
# 3. Обновить boats/admin.py под новую структуру
# 4. Перенести данные (1 товар) вручную