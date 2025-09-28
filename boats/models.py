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


# 🛥️ Описание каталога лодочных ковриков
class BoatCatalogDescription(BaseModel):
    """📝 Описание страницы каталога лодочных ковриков (синглтон)"""

    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок каталога",
        default="Коврики для лодок",
        help_text="Заголовок страницы каталога лодочных ковриков"
    )

    description = CKEditor5Field(
        verbose_name="Описание каталога",
        help_text="Основное описание каталога лодочных ковриков с форматированием",
        config_name='blog',
        blank=True,
        null=True
    )

    # 🎬 Дополнительный контент с YouTube
    additional_content = models.TextField(
        verbose_name="Дополнительный контент",
        help_text="Вставьте готовый HTML-код для YouTube видео или другого контента. "
                  "Пример для YouTube: "
                  '<div class="youtube-video-container" style="position: relative; width: 100%; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; background: #000; margin: 20px 0; border-radius: 8px;">'
                  '<iframe src="https://www.youtube.com/embed/VIDEO_ID" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
                  '</div>',
        blank=True,
        null=True
    )

    meta_description = models.TextField(
        max_length=160,
        blank=True,
        null=True,
        verbose_name="Meta Description",
        help_text="SEO описание для поисковых систем (до 160 символов)"
    )

    def convert_youtube_links(self, content):
        """🎬 Автоматическая конверсия YouTube ссылок в responsive iframe"""
        if not content:
            return content

        import re
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(?:[&\w=]*)?',
            r'https?://youtu\.be/([a-zA-Z0-9_-]{11})(?:\?[&\w=]*)?',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})(?:\?[&\w=]*)?',
        ]

        iframe_template = '''
        <div class="youtube-video-container" style="position: relative; width: 100%%; padding-bottom: 56.25%%; height: 0; overflow: hidden; max-width: 100%%; background: #000; margin: 20px 0; border-radius: 8px;">
            <iframe src="https://www.youtube.com/embed/{}"
                    style="position: absolute; top: 0; left: 0; width: 100%%; height: 100%%;"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen>
            </iframe>
        </div>
        '''

        for pattern in youtube_patterns:
            content = re.sub(pattern, lambda m: iframe_template.format(m.group(1)), content)

        return content

    def has_content(self):
        """📝 Проверка наличия контента для отображения"""
        return bool(self.description or self.additional_content)

    def __str__(self):
        return f"🛥️ {self.title}"

    class Meta:
        verbose_name = "Описание каталога лодочных ковриков"
        verbose_name_plural = "Описание каталога лодочных ковриков"

    def save(self, *args, **kwargs):
        """💾 Синглтон логика - разрешить только один экземпляр"""
        if BoatCatalogDescription.objects.exists() and not self.pk:
            return  # 🚫 Не создавать новые записи, если уже есть

        # 🎬 Автоматическая конверсия YouTube ссылок (временно отключено)
        # if self.additional_content:
        #     self.additional_content = self.convert_youtube_links(self.additional_content)

        super().save(*args, **kwargs)


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

    # 📝 Контентные поля (как у автокатегорий)
    description = CKEditor5Field(
        verbose_name="Описание категории",
        help_text="Основное описание категории лодок с форматированием",
        config_name='blog',
        blank=True,
        null=True
    )

    # 🎬 Дополнительный контент с YouTube (как у автокатегорий)
    additional_content = models.TextField(
        verbose_name="Дополнительный контент",
        help_text="Вставьте готовый HTML-код для YouTube видео или другого контента. "
                  "Пример для YouTube: "
                  '<div class="youtube-video-container" style="position: relative; width: 100%; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; background: #000; margin: 20px 0; border-radius: 8px;">'
                  '<iframe src="https://www.youtube.com/embed/VIDEO_ID" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
                  '</div>',
        blank=True,
        null=True
    )

    # 🔍 SEO поля (как у автокатегорий)
    page_title = models.CharField(
        max_length=70,
        blank=True,
        null=True,
        verbose_name="Заголовок страницы (H1)",
        help_text="Основной заголовок на странице категории (до 70 символов)"
    )

    meta_title = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name="Meta Title",
        help_text="Заголовок для поисковых систем (до 60 символов)"
    )

    meta_description = models.TextField(
        max_length=160,
        blank=True,
        null=True,
        verbose_name="Meta Description",
        help_text="Описание для поисковых систем (до 160 символов)"
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

    def convert_youtube_links(self, content):
        """🎬 Автоматическая конверсия YouTube ссылок в responsive iframe"""
        if not content:
            return content

        import re
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
        ]

        iframe_template = '''
        <div class="youtube-video-container">
            <iframe
                src="https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1&showinfo=0"
                title="YouTube video player"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen>
            </iframe>
        </div>
        '''

        for pattern in youtube_patterns:
            def replace_match(match):
                video_id = match.group(1)
                return iframe_template.format(video_id=video_id).strip()

            content = re.sub(pattern, replace_match, content)

        return content

    def has_content(self):
        """📝 Проверка наличия контента для отображения"""
        return bool(self.description or self.additional_content)

    def get_seo_title(self):
        """🔍 Получить SEO заголовок"""
        return self.meta_title or f"ЭВА коврики для лодок {self.category_name}"

    def get_seo_description(self):
        """🔍 Получить SEO описание"""
        return self.meta_description or f"Качественные ЭВА коврики для лодок {self.category_name.lower()}. Защита дна, выбор цвета, доставка по Беларуси."

    def save(self, *args, **kwargs):
        """🔧 Автогенерация slug, заполнение SEO-полей и конверсия YouTube"""
        if not self.slug:
            self.slug = slugify(self.category_name, allow_unicode=True)

        # Автоматическое заполнение SEO полей
        if not self.page_title:
            self.page_title = self.category_name

        if not self.meta_title:
            self.meta_title = f"ЭВА коврики для лодок {self.category_name}"[:60]

        if not self.meta_description:
            self.meta_description = f"Качественные ЭВА коврики для лодок {self.category_name.lower()}. " \
                                    f"Защита дна лодки, выбор цвета, доставка по Беларуси."[:160]

        # Конверсия YouTube ссылок в additional_content
        if self.additional_content:
            self.additional_content = self.convert_youtube_links(self.additional_content)

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

    def get_rating(self):
        """⭐ Рассчитывает средний рейтинг товара на основе отзывов"""
        # Импортируем здесь чтобы избежать циклического импорта
        from django.contrib.contenttypes.models import ContentType
        try:
            from common.models import ProductReview
            ct = ContentType.objects.get_for_model(self)
            reviews = ProductReview.objects.filter(content_type=ct, object_id=self.uid)
            if reviews.count() > 0:
                total = sum(int(review.stars) for review in reviews)
                return total / reviews.count()
        except ImportError:
            pass
        return 0

    def get_reviews_count(self):
        """📝 Возвращает количество отзывов"""
        from django.contrib.contenttypes.models import ContentType
        try:
            from common.models import ProductReview
            ct = ContentType.objects.get_for_model(self)
            return ProductReview.objects.filter(content_type=ct, object_id=self.uid).count()
        except ImportError:
            pass
        return 0

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