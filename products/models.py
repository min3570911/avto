# 📁 products/models.py - ОБНОВЛЕННАЯ модель Category с YouTube автоконверсией
# 🛍️ Только изменения в модели Category - остальные модели БЕЗ ИЗМЕНЕНИЙ

import re
from django.db import models
from base.models import BaseModel
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field

# 🎨 Определения типов цветов
COLOR_TYPE_CHOICES = (
    ('carpet', 'Коврик'),
    ('border', 'Окантовка')
)


class Category(BaseModel):
    """📂 SEO-оптимизированная модель категорий товаров с YouTube автоконверсией"""

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
    category_image = models.ImageField(
        upload_to="categories",
        verbose_name="Изображение категории",
        help_text="Рекомендуемый размер: 800x400 px"
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

    # 📝 Контентные поля с CKEditor 5
    description = CKEditor5Field(
        verbose_name="Описание категории",
        help_text="Основное описание категории с форматированием",
        config_name='blog',  # 🎯 Расширенная конфигурация
        blank=True,
        null=True
    )
    additional_content = CKEditor5Field(
        verbose_name="Дополнительный контент",
        help_text="Вставьте ссылку на YouTube видео (автоматически преобразуется в плеер)",
        config_name='basic',  # 🎯 Базовая конфигурация для ссылок
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
        """
        🎬 Автоматическая конверсия YouTube ссылок в responsive iframe

        Поддерживаемые форматы:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://youtube.com/embed/VIDEO_ID
        """
        if not content:
            return content

        # 🔍 Регулярные выражения для разных форматов YouTube ссылок
        youtube_patterns = [
            # youtube.com/watch?v=VIDEO_ID
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            # youtu.be/VIDEO_ID
            r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
            # youtube.com/embed/VIDEO_ID
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]

        # 🎯 Шаблон responsive iframe для YouTube
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

        # 🔄 Обработка каждого паттерна
        for pattern in youtube_patterns:
            def replace_match(match):
                video_id = match.group(1)
                return iframe_template.format(video_id=video_id).strip()

            content = re.sub(pattern, replace_match, content)

        return content

    def save(self, *args, **kwargs):
        """🔄 Автоматическое создание slug, заполнение SEO-полей и конверсия YouTube"""
        # 🔗 Автогенерация slug
        if not self.slug:
            self.slug = slugify(self.category_name)

        # 🆔 Автогенерация SKU если не задан
        if not self.category_sku:
            last_sku = Category.objects.aggregate(
                max_sku=models.Max('category_sku')
            )['max_sku']
            self.category_sku = (last_sku or 0) + 1

        # 🔍 Автозаполнение SEO-полей если пусты
        if not self.page_title:
            self.page_title = self.category_name

        if not self.meta_title:
            self.meta_title = f"{self.category_name} - купить в интернет-магазине"[:60]

        if not self.meta_description:
            self.meta_description = f"Большой выбор {self.category_name.lower()}. Качественные товары с доставкой по Беларуси. Выгодные цены и быстрая доставка."[
                                    :160]

        # 🎬 Автоматическая конверсия YouTube ссылок в дополнительном контенте
        if self.additional_content:
            self.additional_content = self.convert_youtube_links(self.additional_content)

        super(Category, self).save(*args, **kwargs)

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
        return f"{self.category_name}{status}"

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['display_order', 'category_name']


# 🔧 ВСЕ ОСТАЛЬНЫЕ МОДЕЛИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ
# (Product, KitVariant, ProductImage, Coupon, ProductReview, Color, Wishlist)

class KitVariant(BaseModel):
    """📦 Модель комплектаций товаров"""
    name = models.CharField(max_length=100, verbose_name="Название комплектации")
    code = models.CharField(max_length=50, unique=True, verbose_name="Символьный код")
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Модификатор цены")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    image = models.ImageField(upload_to='configurations', null=True, blank=True, verbose_name="Изображение схемы")
    is_option = models.BooleanField(default=False, verbose_name="Дополнительная опция")

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Тип комплектации"
        verbose_name_plural = "Типы комплектаций"
        ordering = ['order', 'name']


class Product(BaseModel):
    """🛍️ Основная модель товаров"""
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

    def save(self, *args, **kwargs):
        """🔄 Автоматическое создание slug из названия товара"""
        self.slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.product_name

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

    display_price.short_description = "Цена (Салон)"

    def get_rating(self):
        """⭐ Рассчитывает средний рейтинг товара на основе отзывов"""
        if self.reviews.count() > 0:
            total = sum(int(review['stars']) for review in self.reviews.values())
            return total / self.reviews.count()
        return 0

    def get_reviews_count(self):
        """📝 Возвращает количество отзывов"""
        return self.reviews.count()

    def is_new(self):
        """🆕 Проверяет, является ли товар новым"""
        return self.newest_product

    def get_main_image(self):
        """🖼️ Возвращает главное изображение товара"""
        return self.product_images.first()

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at', 'product_name']


class ProductImage(BaseModel):
    """🖼️ Модель изображений товаров"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='product_images', verbose_name="Товар")
    image = models.ImageField(upload_to='product', verbose_name="Изображение")

    def img_preview(self):
        """👁️ Предпросмотр изображения в админке"""
        if self.image:
            return mark_safe(
                f'<img src="{self.image.url}" width="500" style="max-height: 300px; object-fit: contain;"/>')
        return "—"

    img_preview.short_description = "Предпросмотр изображения"

    def __str__(self):
        return f"Изображение для {self.product.product_name}"

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


class ProductReview(BaseModel):
    """📝 Модель отзывов о товарах"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='reviews', verbose_name="Товар")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='reviews', verbose_name="Пользователь")
    stars = models.IntegerField(
        default=3,
        choices=[(i, i) for i in range(1, 6)],
        verbose_name="Оценка")
    content = models.TextField(
        blank=True, null=True, verbose_name="Содержание отзыва")
    date_added = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата добавления")
    likes = models.ManyToManyField(
        User, related_name="liked_reviews",
        blank=True, verbose_name="Лайки")
    dislikes = models.ManyToManyField(
        User, related_name="disliked_reviews",
        blank=True, verbose_name="Дизлайки")

    def like_count(self):
        """👍 Количество лайков"""
        return self.likes.count()

    def dislike_count(self):
        """👎 Количество дизлайков"""
        return self.dislikes.count()

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product.product_name} ({self.stars}⭐)"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-date_added']
        unique_together = ('user', 'product')


class Color(BaseModel):
    """🎨 Модель для хранения доступных цветов ковриков и окантовки"""
    name = models.CharField(max_length=50, verbose_name="Название цвета")
    hex_code = models.CharField(max_length=7, verbose_name="HEX-код")
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок отображения")

    color_type = models.CharField(
        max_length=10,
        choices=COLOR_TYPE_CHOICES,
        default='carpet',
        verbose_name="Тип применения"
    )

    carpet_image = models.ImageField(
        upload_to='colors/carpet',
        null=True,
        blank=True,
        verbose_name="Изображение для коврика"
    )

    border_image = models.ImageField(
        upload_to='colors/border',
        null=True,
        blank=True,
        verbose_name="Изображение для окантовки"
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="Доступен для заказа"
    )

    def carpet_preview(self):
        """👁️ Отображение превью изображения коврика в админке"""
        if self.carpet_image:
            return mark_safe(f'<img src="{self.carpet_image.url}" height="50" style="border-radius: 4px;"/>')
        return "—"

    def border_preview(self):
        """👁️ Отображение превью изображения окантовки в админке"""
        if self.border_image:
            return mark_safe(f'<img src="{self.border_image.url}" height="50" style="border-radius: 4px;"/>')
        return "—"

    def get_image_url(self):
        """🖼️ Возвращает URL изображения в зависимости от типа цвета"""
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

    carpet_preview.short_description = "Превью коврика"
    border_preview.short_description = "Превью окантовки"
    color_preview_admin.short_description = "Цвет"

    def __str__(self):
        availability = " (недоступен)" if not self.is_available else ""
        return f"{self.name} ({self.get_color_type_display()}){availability}"

    class Meta:
        verbose_name = "Цвет"
        verbose_name_plural = "Цвета"
        ordering = ['color_type', 'display_order', 'name']


class Wishlist(BaseModel):
    """❤️ Модель списка избранных товаров"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="wishlist", verbose_name="Пользователь")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name="wishlisted_by", verbose_name="Товар")
    kit_variant = models.ForeignKey(
        KitVariant, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="wishlist_items", verbose_name="Комплектация")
    carpet_color = models.ForeignKey(
        Color, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="wishlist_carpet_items", verbose_name="Цвет коврика")
    border_color = models.ForeignKey(
        Color, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="wishlist_border_items", verbose_name="Цвет окантовки")
    has_podpyatnik = models.BooleanField(default=False, verbose_name="С подпятником")
    added_on = models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")

    def get_total_price(self):
        """💰 Рассчитывает общую стоимость позиции в избранном"""
        total = 0.0

        if self.kit_variant:
            total += float(self.kit_variant.price_modifier)

        if self.has_podpyatnik:
            podpyatnik = KitVariant.objects.filter(code='podpyatnik', is_option=True).first()
            if podpyatnik:
                total += float(podpyatnik.price_modifier)

        return total

    def __str__(self) -> str:
        kit_info = self.kit_variant.name if self.kit_variant else "Без комплектации"
        return f'{self.user.username} - {self.product.product_name} - {kit_info}'

    class Meta:
        unique_together = ('user', 'product', 'kit_variant')
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        ordering = ['-added_on']

# 🔧 ИЗМЕНЕНИЯ в модели Category:
# ✅ ДОБАВЛЕН: Метод convert_youtube_links() для автоконверсии ссылок
# ✅ ОБНОВЛЕН: Метод save() с вызовом конверсии YouTube
# ✅ ДОБАВЛЕН: Метод has_content() для проверки наличия контента
# ✅ УЛУЧШЕНО: Комментарии и help_text для полей
# ✅ RESPONSIVE: YouTube видео с правильной разметкой
# ✅ АВТОМАТИЧЕСКОЕ: Преобразование всех форматов YouTube ссылок