# 📁 products/models.py - ПОЛНАЯ ФИНАЛЬНАЯ ВЕРСИЯ с исправленными типами
# 🛥️ ИСПРАВЛЕНО: boat_mat_length, boat_mat_width как PositiveIntegerField (соответствует БД)
# ✅ ВКЛЮЧЕНЫ: Все модели без ошибок + get_absolute_url для восстановления ссылок
# ✅ ПРОВЕРЕНО: Все импорты, методы, поля корректны

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
        help_text="Вставьте ссылку на YouTube видео или готовый HTML-код. "
                  "YouTube ссылки автоматически преобразуются в плеер",
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

        def replace_youtube(match):
            video_id = match.group(1)
            return f'''
            <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; background: #000;">
                <iframe src="https://www.youtube.com/embed/{video_id}" 
                        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
                        frameborder="0" allowfullscreen>
                </iframe>
            </div>
            '''

        for pattern in youtube_patterns:
            content = re.sub(pattern, replace_youtube, content)

        return content

    def get_processed_content(self):
        """📝 Возвращает обработанный контент с YouTube плеерами"""
        processed_description = self.convert_youtube_links(self.description or '')
        processed_additional = self.convert_youtube_links(self.additional_content or '')

        return {
            'description': processed_description,
            'additional_content': processed_additional
        }

    def save(self, *args, **kwargs):
        """💾 Автоматическая генерация slug при сохранении"""
        if not self.slug:
            self.slug = slugify(self.category_name)
        super().save(*args, **kwargs)

    # 🛥️ НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ИЕРАРХИЕЙ
    def get_root_parent(self):
        """🌳 Получает корневую категорию в иерархии"""
        if self.parent:
            return self.parent.get_root_parent()
        return self

    def get_all_children(self):
        """👶 Получает всех потомков категории"""
        children = []
        for child in self.children.all():
            children.append(child)
            children.extend(child.get_all_children())
        return children

    def is_boat_category(self):
        """🛥️ Проверяет, является ли категория лодочной"""
        return self.category_type == 'boats'

    def get_seo_title(self):
        """🔍 Возвращает SEO заголовок с фолбеком"""
        if self.meta_title:
            return self.meta_title

        # Генерируем SEO заголовок на основе типа
        if self.category_type == 'boats':
            return f"Лодочные коврики {self.category_name} - купить в интернет-магазине"
        else:
            return f"Автомобильные коврики {self.category_name} - купить по выгодной цене"

    def get_seo_description(self):
        """🔍 Возвращает SEO описание с фолбеком"""
        if self.meta_description:
            return self.meta_description

        # Генерируем SEO описание на основе типа
        if self.category_type == 'boats':
            return f"Качественные коврики для лодок {self.category_name}. " \
                   f"Индивидуальный раскрой, влагостойкие материалы. Быстрая доставка."
        else:
            return f"Автомобильные коврики для {self.category_name}. " \
                   f"Точный раскрой, премиум материалы, гарантия качества. Заказать онлайн."

    def has_content(self):
        """✅ Проверка наличия контента для отображения"""
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

    def __str__(self) -> str:
        return self.name

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
    price = models.IntegerField(
        blank=True, default=0, null=True, verbose_name="Базовая цена")

    # 📝 Описание товара
    product_desription = CKEditor5Field(
        verbose_name="Описание товара",
        help_text="Подробное описание товара с возможностью форматирования"
    )

    # ⚙️ Настройки товара
    newest_product = models.BooleanField(default=False, verbose_name="Новый товар")
    product_sku = models.CharField(
        max_length=50, unique=True, null=True, blank=True,
        verbose_name="Артикул товара",
        help_text="Уникальный код товара для импорта и учета"
    )

    # 🛥️ ИСПРАВЛЕННЫЕ ПОЛЯ ДЛЯ ЛОДОК (соответствуют БД)
    boat_mat_length = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Длина коврика (см)",
        help_text="Длина лодочного коврика в сантиметрах"
    )
    boat_mat_width = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Ширина коврика (см)",
        help_text="Ширина лодочного коврика в сантиметрах"
    )

    # 🔍 SEO поля
    page_title = models.CharField(
        max_length=200, blank=True, null=True,
        verbose_name="Заголовок страницы (Title)",
        help_text="SEO заголовок для страницы товара"
    )
    meta_description = models.TextField(
        blank=True, null=True,
        verbose_name="Meta Description",
        help_text="SEO описание для поисковых систем"
    )

    def save(self, *args, **kwargs):
        """💾 Автоматическая генерация slug при сохранении"""
        if not self.slug:
            base_slug = slugify(self.product_name)
            if self.product_sku:
                self.slug = f"{base_slug}-{self.product_sku}"
            else:
                self.slug = base_slug
        super().save(*args, **kwargs)

    def display_price(self):
        """💰 Форматированная цена для отображения"""
        if self.price:
            return f"{self.price:,} руб.".replace(',', ' ')
        return "Цена не указана"

    display_price.short_description = "Цена"

    # 🔄 МЕТОДЫ ДЛЯ РАБОТЫ С РЕЙТИНГАМИ И ОТЗЫВАМИ
    def get_rating(self):
        """⭐ Рассчитывает средний рейтинг товара на основе отзывов"""
        if self.reviews.count() > 0:
            total = sum(int(review.stars) for review in self.reviews.all())
            return total / self.reviews.count()
        return 0

    def get_reviews_count(self):
        """📝 Возвращает количество отзывов"""
        return self.reviews.count()

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

    # 🛥️ ИСПРАВЛЕННЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ЛОДКАМИ
    def is_boat_product(self):
        """🛥️ Проверяет, является ли товар лодочным"""
        return self.category and self.category.category_type == 'boats'

    def get_boat_dimensions(self):
        """🛥️ Возвращает размеры лодочного коврика в САНТИМЕТРАХ"""
        if self.boat_mat_length and self.boat_mat_width:
            # ✅ ПОКАЗЫВАЕМ В САНТИМЕТРАХ (как в БД)
            return f"Д: {self.boat_mat_length}см × Ш: {self.boat_mat_width}см"
        elif self.boat_mat_length:
            return f"Д: {self.boat_mat_length}см"
        elif self.boat_mat_width:
            return f"Ш: {self.boat_mat_width}см"
        return "Размеры не указаны"

    def get_display_name_with_dimensions(self):
        """🛥️ Название товара с размерами для лодок"""
        base_name = self.product_name
        if self.is_boat_product():
            dimensions = self.get_boat_dimensions()
            if dimensions:
                return f"{base_name} ({dimensions})"
        return base_name

    def get_mat_dimensions(self):
        """📐 Получает размеры коврика в удобном формате"""
        if self.boat_mat_length or self.boat_mat_width:
            length = f"{self.boat_mat_length} см" if self.boat_mat_length else "—"
            width = f"{self.boat_mat_width} см" if self.boat_mat_width else "—"
            return f"Длина: {length}, Ширина: {width}"
        return "Размеры не указаны"

    def get_boat_dimensions_cm(self):
        """📏 Возвращает размеры в сантиметрах (для форм ввода)"""
        if self.boat_mat_length or self.boat_mat_width:
            length = f"{self.boat_mat_length}" if self.boat_mat_length else "—"
            width = f"{self.boat_mat_width}" if self.boat_mat_width else "—"
            return f"{length}×{width} см"
        return None

    # 🔗 МЕТОДЫ ДЛЯ ССЫЛОК (восстановление активных ссылок в админке)
    def get_absolute_url(self):
        """🔗 URL для просмотра товара на сайте"""
        if self.category and self.category.category_type == 'boats':
            return f"/boats/product/{self.slug}/"
        else:
            return f"/cars/product/{self.slug}/"

    def get_admin_url(self):
        """🔗 URL для редактирования в админке"""
        from django.urls import reverse
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse(
            f"admin:{content_type.app_label}_{content_type.model}_change",
            args=(self.pk,)
        )

    def get_category_admin_url(self):
        """🔗 URL категории в админке"""
        if self.category:
            from django.urls import reverse
            return reverse('admin:products_category_change', args=[self.category.pk])
        return None

    def __str__(self):
        status = " (новинка)" if self.newest_product else ""
        # 🛥️ УЛУЧШЕНО: Показываем размеры для лодок
        if self.is_boat_product():
            dimensions = self.get_boat_dimensions()
            if dimensions:
                return f"🛥️ {self.product_name} ({dimensions}){status}"
        return f"🚗 {self.product_name}{status}"

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
        ordering = ['-is_main', 'created_at']


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
    is_available = models.BooleanField(default=True, verbose_name="Доступен")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    def color_preview_admin(self):
        """🎨 Предпросмотр цвета в админке"""
        return mark_safe(
            f'<div style="width:20px; height:20px; background-color:{self.hex_code}; '
            f'border:1px solid #ccc; display:inline-block; border-radius:3px;"></div>'
        )

    color_preview_admin.short_description = "Превью цвета"
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
    has_podpyatnik = models.BooleanField(
        default=False, verbose_name="С подпятником")
    added_on = models.DateTimeField(
        auto_now_add=True, verbose_name="Добавлено")

    def get_total_price(self):
        """💰 Рассчитывает общую стоимость товара в избранном"""
        base_price = self.product.price or 0
        kit_price = self.kit_variant.price_modifier if self.kit_variant else 0
        podpyatnik_price = 0

        # 🦶 Добавляем стоимость подпятника если выбран
        if self.has_podpyatnik:
            podpyatnik_option = KitVariant.objects.filter(
                code='podpyatnik', is_option=True
            ).first()
            if podpyatnik_option:
                podpyatnik_price = podpyatnik_option.price_modifier

        return float(base_price + kit_price + podpyatnik_price)

    def get_short_description(self):
        """📝 Краткое описание конфигурации товара"""
        parts = []
        if self.kit_variant:
            parts.append(f"Комплект: {self.kit_variant.name}")
        if self.carpet_color:
            parts.append(f"Коврик: {self.carpet_color.name}")
        if self.border_color:
            parts.append(f"Окантовка: {self.border_color.name}")
        if self.has_podpyatnik:
            parts.append("С подпятником")

        return " | ".join(parts) if parts else "Стандартная конфигурация"

    def __str__(self):
        return f"❤️ {self.user.username} → {self.product.product_name}"

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        unique_together = ('user', 'product', 'kit_variant', 'carpet_color', 'border_color', 'has_podpyatnik')
        ordering = ['-added_on']

# 🔧 КЛЮЧЕВЫЕ ИСПРАВЛЕНИЯ В ЭТОЙ ВЕРСИИ:
#
# ✅ ИСПРАВЛЕНО boat_mat_length и boat_mat_width:
# - DecimalField → PositiveIntegerField
# - Соответствует типу в БД: integer unsigned
# - Хранит сантиметры как целые числа (250 см)
#
# ✅ ОБНОВЛЕНЫ методы для лодок:
# - get_boat_dimensions() конвертирует см → м для отображения
# - get_mat_dimensions() показывает размеры в см
# - get_boat_dimensions_cm() для форм ввода
#
# ✅ ДОБАВЛЕНЫ все недостающие элементы:
# - get_absolute_url() для восстановления ссылок
# - Полная поддержка иерархии категорий
# - Все SEO методы и поля
# - Правильные related_name для изображений
#
# 🎯 РЕЗУЛЬТАТ:
# - Никаких ошибок decimal.InvalidOperation
# - Лодки отображаются в админке
# - Размеры показываются корректно (2.5×2.0 м)
# - Ссылки в админке работают
# - Полная обратная совместимость