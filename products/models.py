# 📁 products/models.py - ПОЛНАЯ ВЕРСИЯ БЕЗ дублирующихся моделей
# ✅ УДАЛЕНО: ProductReview и Wishlist (перенесены в common)
# 🛥️ СОХРАНЕНО: Все остальные модели с полной функциональностью из оригинала
# ✅ ВКЛЮЧЕНЫ: Category, Product, ProductImage, Coupon, Color, KitVariant

import re
from django.db import models
from base.models import BaseModel
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
from django.db.models import Q

# 🆕 КРИТИЧНЫЙ ИМПОРТ: Кастомное хранилище без суффиксов
from .storage import OverwriteStorage

# 🏠 Описание каталога автоковриков
class AutoCatalogDescription(BaseModel):
    """📝 Описание страницы каталога автоковриков (синглтон)"""

    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок каталога",
        default="Автомобильные коврики",
        help_text="Заголовок страницы каталога автоковриков"
    )

    description = CKEditor5Field(
        verbose_name="Описание каталога",
        help_text="Основное описание каталога автоковриков с форматированием",
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
        return f"📝 {self.title}"

    class Meta:
        verbose_name = "Описание каталога автоковриков"
        verbose_name_plural = "Описание каталога автоковриков"

    def save(self, *args, **kwargs):
        """💾 Синглтон логика - разрешить только один экземпляр"""
        if AutoCatalogDescription.objects.exists() and not self.pk:
            return  # 🚫 Не создавать новые записи, если уже есть

        # 🎬 Автоматическая конверсия YouTube ссылок (временно отключено)
        # if self.additional_content:
        #     self.additional_content = self.convert_youtube_links(self.additional_content)

        super().save(*args, **kwargs)


# 🎨 Определения типов цветов
COLOR_TYPE_CHOICES = (
    ('carpet', 'Коврик'),
    ('border', 'Окантовка')
)

# 🛥️ НОВОЕ: Типы категорий для разделения авто/лодки
CATEGORY_TYPE_CHOICES = (
    ('cars', 'Автомобили'),
    ('boats', 'Лодки'),
)


class Category(BaseModel):
    """📂 SEO-оптимизированная модель категорий товаров с поддержкой лодок"""

    # 🏷️ Основные поля
    category_name = models.CharField(
        max_length=100,
        verbose_name="Название категории",
        help_text="Основное название категории для отображения"
    )
    slug = models.SlugField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="URL-адрес",
        help_text="Автоматически генерируется из названия"
    )

    # 🖼️ ИСПРАВЛЕНО: Подключено OverwriteStorage для точных имён файлов
    category_image = models.ImageField(
        upload_to="categories",
        storage=OverwriteStorage(),  # 🎯 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ!
        verbose_name="Изображение категории",
        help_text="Рекомендуемый размер: 800x400 px. Файл сохранится с точным именем"
    )

    # 🆔 Служебные поля
    category_sku = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="Артикул категории",
        help_text="Уникальный номер для внутреннего учета"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок отображения",
        help_text="Чем меньше число, тем выше в списке (0 = сверху)"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
        help_text="Отображать категорию на сайте"
    )

    # 🛥️ НОВЫЕ ПОЛЯ ДЛЯ ЛОДОК
    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPE_CHOICES,
        default='cars',
        verbose_name="Тип категории",
        help_text="Автомобили или лодки для правильной обработки"
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name="Родительская категория",
        help_text="Для создания иерархии: Лодки → Hunter, Marlin..."
    )

    # 📝 Контентные поля
    description = CKEditor5Field(
        verbose_name="Описание категории",
        help_text="Основное описание категории с форматированием",
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

    # 🔍 SEO поля
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

    def convert_youtube_links(self, content):
        """🎬 Автоматическая конверсия YouTube ссылок в responsive iframe"""
        if not content:
            return content

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

    def save(self, *args, **kwargs):
        """🔄 Автоматическое создание slug, заполнение SEO-полей и конверсия YouTube"""
        if not self.slug:
            self.slug = slugify(self.category_name)

        if not self.category_sku:
            last_sku = Category.objects.aggregate(
                max_sku=models.Max('category_sku')
            )['max_sku']
            self.category_sku = (last_sku or 0) + 1

        if not self.page_title:
            self.page_title = self.category_name

        if not self.meta_title:
            # 🛥️ УЛУЧШЕНО: Разные мета-заголовки для авто и лодок
            if self.category_type == 'boats':
                self.meta_title = f"ЭВА коврики для лодок {self.category_name}"[:60]
            else:
                self.meta_title = f"{self.category_name} - купить в интернет-магазине"[:60]

        if not self.meta_description:
            # 🛥️ УЛУЧШЕНО: Разные мета-описания для авто и лодок
            if self.category_type == 'boats':
                self.meta_description = f"Качественные ЭВА коврики для лодок {self.category_name.lower()}. " \
                                        f"Защита дна, выбор цвета, доставка по Беларуси."[:160]
            else:
                self.meta_description = f"Большой выбор {self.category_name.lower()}. " \
                                        f"Качественные товары с доставкой по Беларуси. Выгодные цены и быстрая доставка."[:160]

        if self.additional_content:
            self.additional_content = self.convert_youtube_links(self.additional_content)

        super(Category, self).save(*args, **kwargs)

    # 🛥️ НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ИЕРАРХИЕЙ ЛОДОК
    def get_root_parent(self):
        """🌳 Получить корневую категорию (для лодок это будет 'Лодки')"""
        if self.parent:
            return self.parent.get_root_parent()
        return self

    def get_all_children(self):
        """👥 Получить всех потомков категории"""
        return Category.objects.filter(parent=self)

    def is_root_category(self):
        """🏠 Проверка является ли категория корневой"""
        return self.parent is None

    def is_boat_category(self):
        """🛥️ Проверка является ли категория лодочной"""
        return self.category_type == 'boats'

    def is_car_category(self):
        """🚗 Проверка является ли категория автомобильной"""
        return self.category_type == 'cars'

    # ✅ СУЩЕСТВУЮЩИЕ МЕТОДЫ (без изменений)
    def get_products_count(self):
        """📊 Количество активных товаров в категории"""
        return self.products.filter(newest_product=True).count()

    def get_active_products_count(self):
        """📦 Количество всех товаров в категории"""
        return self.products.count()

    def get_seo_title(self):
        """🔍 Получить SEO-заголовок для страницы"""
        return self.meta_title or self.page_title or self.category_name

    def get_seo_description(self):
        """📝 Получить SEO-описание для страницы"""
        return self.meta_description or f"Товары категории {self.category_name}"

    def get_display_title(self):
        """🏷️ Получить заголовок для отображения на странице"""
        return self.page_title or self.category_name

    def has_content(self):
        """📝 Проверка наличия контента для отображения"""
        return bool(self.description or self.additional_content)

    def __str__(self) -> str:
        status = " (неактивна)" if not self.is_active else ""
        # 🛥️ УЛУЧШЕНО: Показываем тип категории и иерархию
        type_icon = "🛥️" if self.category_type == 'boats' else "🚗"
        hierarchy = f" → {self.category_name}" if self.parent else self.category_name
        return f"{type_icon} {hierarchy}{status}"

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['display_order', 'category_name']


class KitVariant(BaseModel):
    """📦 Модель комплектаций товаров"""
    name = models.CharField(max_length=100, verbose_name="Название комплектации")
    code = models.CharField(max_length=50, unique=True, verbose_name="Символьный код")
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Модификатор цены")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    image = models.ImageField(upload_to='configurations', null=True, blank=True, verbose_name="Изображение схемы")
    is_option = models.BooleanField(default=False, verbose_name="Дополнительная опция")
    description = models.TextField(
        blank=True,
        verbose_name="Описание комплектации"
    )

    def __str__(self) -> str:
        price_info = f" (+{self.price_modifier} BYN)" if self.price_modifier > 0 else ""
        option_mark = " [ОПЦИЯ]" if self.is_option else ""
        return f"{self.name}{price_info}{option_mark}"

    class Meta:
        verbose_name = "Тип комплектации"
        verbose_name_plural = "Типы комплектаций"
        ordering = ['order', 'name']


class Product(BaseModel):
    """🛍️ Основная модель товаров с поддержкой лодок"""
    product_name = models.CharField(max_length=100, verbose_name="Название товара")
    slug = models.SlugField(unique=True, null=True, blank=True, verbose_name="URL-адрес")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name="products", verbose_name="Категория")
    price = models.IntegerField(verbose_name="Базовая цена", null=True, blank=True, default=0)
    product_desription = CKEditor5Field(
        verbose_name="Описание товара",
        help_text="Подробное описание товара с возможностью форматирования",
        config_name='default'
    )
    newest_product = models.BooleanField(default=False, verbose_name="Новый товар")

    # 🆕 Поля для импорта
    product_sku = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Артикул товара",
        help_text="Уникальный код товара для импорта и учета"
    )

    # 🛥️ НОВЫЕ ПОЛЯ ДЛЯ ЛОДОК
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

    # 🔍 SEO поля
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

    # 🛥️ НОВЫЕ МЕТОДЫ ДЛЯ ЛОДОК
    def is_boat_product(self):
        """🛥️ Проверка является ли товар лодочным"""
        return self.category.category_type == 'boats'

    def is_car_product(self):
        """🚗 Проверка является ли товар автомобильным"""
        return self.category.category_type == 'cars'

    def get_mat_dimensions(self):
        """📏 Получить размеры коврика для лодок"""
        if self.is_boat_product() and self.boat_mat_length and self.boat_mat_width:
            return f"{self.boat_mat_length}×{self.boat_mat_width} см"
        return None

    def get_display_name_with_dimensions(self):
        """🏷️ Название товара с размерами (для лодок)"""
        dimensions = self.get_mat_dimensions()
        if dimensions:
            return f"{self.product_name} ({dimensions})"
        return self.product_name

    def save(self, *args, **kwargs):
        """🔄 Автоматическое создание slug из названия товара"""
        if not self.slug and self.product_name:
            self.slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self) -> str:
        sku_info = f" ({self.product_sku})" if self.product_sku else ""
        # 🛥️ УЛУЧШЕНО: Показываем размеры для лодок
        dimensions = self.get_mat_dimensions()
        dimensions_info = f" [{dimensions}]" if dimensions else ""
        return f"{self.product_name}{dimensions_info}{sku_info}"

    # ✅ СУЩЕСТВУЮЩИЕ МЕТОДЫ ЦЕН И КОМПЛЕКТАЦИЙ
    def get_product_price_by_kit(self, kit_code='salon'):
        """🛒 Получает цену товара с учетом выбранной комплектации"""
        kit = KitVariant.objects.filter(code=kit_code).first()
        if kit:
            return float(kit.price_modifier)
        return float(self.price) if self.price else 0

    def get_salon_price(self):
        """🎯 Получает цену комплектации "Салон" для отображения в списках товаров"""
        return self.get_product_price_by_kit('salon')

    def get_default_price(self):
        """🏠 Получает цену по умолчанию (комплектация "Салон")"""
        return self.get_salon_price()

    def display_price(self):
        """📊 Отображает цену для админки с правильным форматированием"""
        price = self.get_salon_price()
        return f"{price:.0f} руб."

    display_price.short_description = "Цена"

    # 🔄 МЕТОДЫ ДЛЯ РАБОТЫ С РЕЙТИНГАМИ И ОТЗЫВАМИ (используют common.ProductReview)
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

    def is_new(self):
        """🆕 Проверяет, является ли товар новым"""
        return self.newest_product

    # 🖼️ МЕТОДЫ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ
    def get_main_image(self):
        """🖼️ Возвращает главное изображение товара"""
        return self.product_images.filter(is_main=True).first()

    def get_gallery_images(self):
        """🖼️ Возвращает дополнительные изображения для галереи"""
        return self.product_images.filter(is_main=False)

    def get_main_image_url(self):
        """🖼️ Возвращает URL главного изображения или заглушки"""
        main_image = self.get_main_image()
        if main_image and main_image.image:
            return main_image.image.url
        return '/media/images/placeholder-product.jpg'

    def has_main_image(self):
        """✅ Проверяет наличие главного изображения"""
        return self.get_main_image() is not None

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at', 'product_name']


class ProductImage(BaseModel):
    """🖼️ Модель изображений товаров с OverwriteStorage"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='product_images', verbose_name="Товар")

    # 🖼️ ИСПРАВЛЕНО: Подключено OverwriteStorage для точных имён файлов
    image = models.ImageField(
        upload_to='product',
        storage=OverwriteStorage(),  # 🎯 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ!
        verbose_name="Изображение",
        help_text="Файл сохранится с точным именем без хеш-суффиксов"
    )

    is_main = models.BooleanField(
        default=False,
        verbose_name="Главное изображение",
        help_text="Отображается в каталоге и как основное в карточке товара"
    )

    def img_preview(self):
        """👁️ Предпросмотр изображения в админке"""
        if self.image:
            main_badge = "🌟 ГЛАВНОЕ" if self.is_main else ""
            return mark_safe(
                f'<div style="text-align: center;">'
                f'<img src="{self.image.url}" width="150" style="max-height: 150px; object-fit: contain; border-radius: 5px;"/>'
                f'<br><small style="color: #2a41e8; font-weight: bold;">{main_badge}</small>'
                f'</div>'
            )
        return "📷 Изображение не загружено"

    img_preview.short_description = "Предпросмотр"

    def save(self, *args, **kwargs):
        """💾 Логика сохранения с контролем главного изображения"""
        if self.is_main:
            # 🔄 Сбрасываем флаг is_main у всех других изображений этого товара
            ProductImage.objects.filter(
                product=self.product,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)

        super(ProductImage, self).save(*args, **kwargs)

    def __str__(self):
        main_info = " (главное)" if self.is_main else ""
        return f"Изображение для {self.product.product_name}{main_info}"

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"
        ordering = ['created_at']


class Coupon(BaseModel):
    """🎫 Модель купонов и скидок"""
    coupon_code = models.CharField(max_length=10, verbose_name="Код купона")
    is_expired = models.BooleanField(default=False, verbose_name="Истёк")
    discount_amount = models.IntegerField(default=100, verbose_name="Сумма скидки")
    minimum_amount = models.IntegerField(default=500, verbose_name="Минимальная сумма заказа")

    def __str__(self):
        status = "неактивен" if self.is_expired else "активен"
        return f"{self.coupon_code} (-{self.discount_amount} руб.) - {status}"

    def is_valid(self, order_total):
        """✅ Проверяет валидность купона для суммы заказа"""
        return not self.is_expired and order_total >= self.minimum_amount

    class Meta:
        verbose_name = "Купон"
        verbose_name_plural = "Купоны"
        ordering = ['-created_at']


class Color(BaseModel):
    """🎨 Модель цветов для ковриков и окантовки"""
    name = models.CharField(max_length=50, verbose_name="Название цвета")
    hex_code = models.CharField(
        max_length=7, verbose_name="HEX-код",
        help_text="Цветовой код в формате #RRGGBB"
    )
    color_type = models.CharField(
        max_length=10, choices=COLOR_TYPE_CHOICES,
        default='carpet', verbose_name="Тип цвета"
    )
    display_order = models.PositiveSmallIntegerField(
        default=0, verbose_name="Порядок отображения"
    )
    is_available = models.BooleanField(
        default=True, verbose_name="Доступен для заказа"
    )

    # 🖼️ Изображения для визуализации (с OverwriteStorage)
    carpet_image = models.ImageField(
        upload_to='colors/carpet',
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name="Изображение коврика",
        help_text="Для визуализации коврика этого цвета"
    )
    border_image = models.ImageField(
        upload_to='colors/border',
        storage=OverwriteStorage(),
        null=True, blank=True,
        verbose_name="Изображение окантовки",
        help_text="Для визуализации окантовки этого цвета"
    )

    def carpet_preview(self):
        """🖼️ Превью коврика в админке"""
        if self.carpet_image:
            return mark_safe(
                f'<img src="{self.carpet_image.url}" width="50" height="50" style="object-fit: cover; border-radius: 3px;"/>')
        return "🚫 Нет изображения"

    def border_preview(self):
        """🖼️ Превью окантовки в админке"""
        if self.border_image:
            return mark_safe(
                f'<img src="{self.border_image.url}" width="50" height="50" style="object-fit: cover; border-radius: 3px;"/>')
        return "🚫 Нет изображения"

    def get_image_url(self):
        """🎯 Получение URL изображения в зависимости от типа"""
        if self.color_type == 'carpet' and self.carpet_image:
            return self.carpet_image.url
        elif self.color_type == 'border' and self.border_image:
            return self.border_image.url
        return ""

    def color_preview_admin(self):
        """🎨 Показывает цветной квадрат в админке"""
        return mark_safe(
            f'<div style="width:20px; height:20px; background-color:{self.hex_code}; '
            f'border:1px solid #666; border-radius:3px; display:inline-block;"></div>'
        )

    def get_color_preview_html(self):
        """🎨 HTML превью цвета для админки"""
        return mark_safe(
            f'<div style="width: 30px; height: 30px; background-color: {self.hex_code}; '
            f'border: 1px solid #ccc; border-radius: 3px; display: inline-block;"></div>'
        )

    def carpet_preview_admin(self):
        """👁️ Превью коврика для админки"""
        if self.carpet_image:
            return mark_safe(
                f'<img src="{self.carpet_image.url}" '
                f'style="width: 40px; height: 40px; object-fit: cover; border-radius: 3px;" />'
            )
        return "Нет изображения"

    def border_preview_admin(self):
        """👁️ Превью окантовки для админки"""
        if self.border_image:
            return mark_safe(
                f'<img src="{self.border_image.url}" '
                f'style="width: 40px; height: 40px; object-fit: cover; border-radius: 3px;" />'
            )
        return "Нет изображения"

    carpet_preview.short_description = "Превью коврика"
    border_preview.short_description = "Превью окантовки"
    color_preview_admin.short_description = "Цвет"
    carpet_preview_admin.short_description = "Превью коврика"
    border_preview_admin.short_description = "Превью окантовки"

    def __str__(self):
        availability = " (недоступен)" if not self.is_available else ""
        return f"{self.name} ({self.get_color_type_display()}){availability}"

    class Meta:
        verbose_name = "Цвет"
        verbose_name_plural = "Цвета"
        ordering = ['color_type', 'display_order', 'name']