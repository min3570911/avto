# 📁 boats/models.py - ФИНАЛЬНЫЕ ОТДЕЛЬНЫЕ МОДЕЛИ ДЛЯ ЛОДОК
# 🛥️ Создание независимых таблиц boats (НЕ proxy-модели)
# ✅ ПЛОСКАЯ СТРУКТУРА: Все категории корневые (Yamaha, Mercury, Suzuki...)
# ✅ СПЕЦИАЛЬНЫЕ ПОЛЯ: boat_mat_length, boat_mat_width, описание через CKEditor

import uuid
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from base.models import BaseModel

# 🆕 Кастомное хранилище из products
from products.storage import OverwriteStorage


class BoatCategory(BaseModel):
    """
    🛥️ Отдельная модель категорий лодок (независимая от products)

    ПЛОСКАЯ СТРУКТУРА:
    ├─ Yamaha (parent=null)
    ├─ Mercury (parent=null)
    ├─ Suzuki (parent=null)
    └─ Honda (parent=null)
    """

    # 🏷️ Основные поля
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

    # 🖼️ Изображение категории (логотип бренда)
    category_image = models.ImageField(
        upload_to="boat_categories",
        storage=OverwriteStorage(),
        null=True,
        blank=True,
        verbose_name="Изображение категории",
        help_text="Логотип бренда лодки. Рекомендуемый размер: 400x300px"
    )

    # 📝 Описания (заполняется через админку)
    description = CKEditor5Field(
        blank=True,
        null=True,
        verbose_name="Описание категории",
        help_text="Подробное описание категории лодок (через визуальный редактор)",
        config_name='default'
    )

    # 📊 SEO поля
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Meta title",
        help_text="SEO заголовок для поисковых систем"
    )

    meta_description = models.TextField(
        max_length=300,
        blank=True,
        verbose_name="Meta description",
        help_text="SEO описание для поисковых систем (до 300 символов)"
    )

    # ⚙️ Управление категорией
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активная категория",
        help_text="Показывать категорию на сайте"
    )

    display_order = models.IntegerField(
        default=0,
        verbose_name="Порядок отображения",
        help_text="Чем меньше число, тем выше в списке"
    )

    def save(self, *args, **kwargs):
        """🔧 Автогенерация slug при сохранении"""
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
        """🛥️ Отображение в админке с иконкой лодки"""
        status = "" if self.is_active else " (неактивна)"
        return f"🛥️ {self.category_name}{status}"

    class Meta:
        verbose_name = "🛥️ Категория лодок"
        verbose_name_plural = "🛥️ Категории лодок"
        ordering = ['display_order', 'category_name']


class BoatProduct(BaseModel):
    """
    🛥️ Отдельная модель товаров лодок (независимая от products)

    КЛЮЧЕВЫЕ ОСОБЕННОСТИ:
    - boat_mat_length, boat_mat_width (размеры коврика)
    - description через CKEditor5 (заполняется в админке)
    - БЕЗ комплектаций (упрощенная логика vs автомобили)
    - Использует цвета из products.models.Color (общие)
    """

    # 🏷️ Основная информация
    product_name = models.CharField(
        max_length=200,
        verbose_name="Название товара",
        help_text="Например: Коврик EVA Yamaha F150"
    )

    slug = models.SlugField(
        unique=True,
        max_length=255,
        verbose_name="URL-адрес",
        help_text="Автоматически генерируется из названия"
    )

    # 📂 Связь с категорией лодок
    category = models.ForeignKey(
        BoatCategory,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория лодки",
        help_text="Выберите бренд лодки"
    )

    # 💰 Цена товара
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Цена (руб.)",
        help_text="Базовая цена лодочного коврика"
    )

    # 📐 УНИКАЛЬНЫЕ ПОЛЯ ДЛЯ ЛОДОК: Размеры коврика
    boat_mat_length = models.PositiveIntegerField(
        verbose_name="Длина коврика (см)",
        help_text="Длина лодочного коврика в сантиметрах",
        null=True,
        blank=True
    )

    boat_mat_width = models.PositiveIntegerField(
        verbose_name="Ширина коврика (см)",
        help_text="Ширина лодочного коврика в сантиметрах",
        null=True,
        blank=True
    )

    # 📝 Описание товара (заполняется через админку)
    description = CKEditor5Field(
        blank=True,
        null=True,
        verbose_name="Описание товара",
        help_text="Подробное описание лодочного коврика (через визуальный редактор)",
        config_name='default'
    )

    # 🏷️ Краткое описание для карточек
    short_description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Краткое описание",
        help_text="Краткое описание для отображения в каталоге (до 500 символов)"
    )

    # 📊 SEO поля
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Meta title",
        help_text="SEO заголовок для поисковых систем"
    )

    meta_description = models.TextField(
        max_length=300,
        blank=True,
        verbose_name="Meta description",
        help_text="SEO описание для поисковых систем"
    )

    # ⚙️ Управление товаром
    is_active = models.BooleanField(
        default=True,
        verbose_name="Товар активен",
        help_text="Показывать товар в каталоге"
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Рекомендуемый товар",
        help_text="Показывать в разделе рекомендуемых"
    )

    newest_product = models.BooleanField(
        default=False,
        verbose_name="Новинка",
        help_text="Отметить как новинку"
    )

    # 📦 Складские данные
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество на складе",
        help_text="Остаток товара на складе"
    )

    # 🏷️ Дополнительные поля
    sku = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="Артикул (SKU)",
        help_text="Уникальный код товара"
    )

    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Вес (кг)",
        help_text="Вес товара для расчета доставки"
    )

    def save(self, *args, **kwargs):
        """🔧 Автогенерация slug и SKU при сохранении"""
        if not self.slug:
            self.slug = slugify(self.product_name, allow_unicode=True)

        if not self.sku:
            # Генерация SKU: BOAT-{category_name}-{random}
            category_code = self.category.category_name[:4].upper()
            self.sku = f"BOAT-{category_code}-{uuid.uuid4().hex[:6].upper()}"

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """🌐 URL товара лодки"""
        return reverse('boats:product_detail', kwargs={'slug': self.slug})

    def get_main_image(self):
        """🖼️ Получить главное изображение товара"""
        main_image = self.images.filter(is_main=True).first()
        if main_image:
            return main_image
        # Если нет главного, берем первое доступное
        return self.images.first()

    def get_mat_dimensions(self):
        """📐 Получить размеры коврика в формате "120×80 см" """
        if self.boat_mat_length and self.boat_mat_width:
            return f"{self.boat_mat_length}×{self.boat_mat_width} см"
        elif self.boat_mat_length:
            return f"Длина: {self.boat_mat_length} см"
        elif self.boat_mat_width:
            return f"Ширина: {self.boat_mat_width} см"
        return "Размеры уточняйте"

    def get_display_price(self):
        """💰 Отформатированная цена для отображения"""
        return f"{self.price:,.0f}".replace(',', ' ')

    def get_similar_products(self, limit=4):
        """🔄 Похожие товары из той же категории"""
        return BoatProduct.objects.filter(
            category=self.category,
            is_active=True
        ).exclude(id=self.id)[:limit]

    def is_in_stock(self):
        """📦 Проверка наличия на складе"""
        return self.stock_quantity > 0

    def get_dimensions_display(self):
        """📏 Красивое отображение размеров для шаблонов"""
        if self.boat_mat_length and self.boat_mat_width:
            return {
                'length': self.boat_mat_length,
                'width': self.boat_mat_width,
                'formatted': f"{self.boat_mat_length}×{self.boat_mat_width} см",
                'area': round(self.boat_mat_length * self.boat_mat_width / 10000, 2)  # м²
            }
        return None

    def __str__(self):
        """🛥️ Отображение в админке с размерами"""
        dimensions = ""
        if self.boat_mat_length and self.boat_mat_width:
            dimensions = f" ({self.boat_mat_length}×{self.boat_mat_width}см)"

        status = "" if self.is_active else " (неактивен)"
        return f"🛥️ {self.product_name}{dimensions}{status}"

    class Meta:
        verbose_name = "🛥️ Товар (лодка)"
        verbose_name_plural = "🛥️ Товары (лодки)"
        ordering = ['-created_at', 'product_name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
        ]


class BoatProductImage(BaseModel):
    """
    🖼️ Изображения лодочных товаров (отдельная от products)
    Независимая модель для управления галереей изображений лодок
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

# 🔧 ФИНАЛЬНЫЕ КОММЕНТАРИИ:
#
# ✅ СОЗДАНЫ ТРИ ОТДЕЛЬНЫЕ МОДЕЛИ:
# 1. BoatCategory - категории лодок (Yamaha, Mercury...)
# 2. BoatProduct - товары лодок (с размерами коврика)
# 3. BoatProductImage - изображения товаров лодок
#
# 🎯 КЛЮЧЕВЫЕ ОСОБЕННОСТИ:
# • Плоская структура категорий (все корневые)
# • boat_mat_length, boat_mat_width - размеры ковриков
# • description через CKEditor5 (заполняется в админке)
# • Независимость от products (отдельные таблицы)
# • Использование цветов из products.models.Color (общие)
# • SEO-оптимизированные поля
# • Методы для отображения размеров
#
# 🗄️ СОЗДАВАЕМЫЕ ТАБЛИЦЫ:
# • boats_boatcategory - категории лодок
# • boats_boatproduct - товары лодок
# • boats_boatproductimage - изображения товаров
#
# 📋 СЛЕДУЮЩИЕ ШАГИ:
# 1. Создать миграцию: python manage.py makemigrations boats
# 2. Применить миграцию: python manage.py migrate boats
# 3. Обновить boats/admin.py под отдельные модели
# 4. Настроить Excel импорт по образу products