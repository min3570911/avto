# 📁 references/models.py - ПОЛНАЯ ВЕРСИЯ с db_table для переименования приложения
# 🔧 ДОБАВЛЕНО: db_table для сохранения старых имен таблиц
# ✅ СОХРАНЕНО: Вся функциональность моделей без изменений

from django.db import models
from django.contrib.auth.models import User
from django.utils.html import mark_safe
from base.models import BaseModel
from django_ckeditor_5.fields import CKEditor5Field

# 🎨 Константы для выбора типа цвета
COLOR_TYPE_CHOICES = [
    ('carpet', 'Цвет коврика'),
    ('border', 'Цвет окантовки'),
]


class Category(BaseModel):
    """📂 Модель категорий товаров с иерархией"""
    category_name = models.CharField(max_length=200, verbose_name="Название категории")
    slug = models.SlugField(unique=True, null=True, blank=True, verbose_name="URL-адрес")

    # 🌳 Иерархия категорий
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children', verbose_name="Родительская категория"
    )

    # 🎯 Тип категории (cars/boats)
    CATEGORY_TYPE_CHOICES = [
        ('cars', 'Автомобили'),
        ('boats', 'Лодки'),
    ]
    category_type = models.CharField(
        max_length=10, choices=CATEGORY_TYPE_CHOICES,
        default='cars', verbose_name="Тип категории"
    )

    # 📝 Контент и SEO
    description = models.TextField(blank=True, null=True, verbose_name="Описание категории")
    additional_content = CKEditor5Field(
        blank=True, null=True, verbose_name="Дополнительный контент",
        help_text="Дополнительная информация о категории"
    )
    category_image = models.ImageField(
        upload_to='categories', null=True, blank=True,
        verbose_name="Изображение категории"
    )

    # 🔍 SEO поля
    meta_title = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Meta Title",
        help_text="Заголовок для поисковых систем"
    )
    meta_description = models.TextField(
        blank=True, null=True,
        verbose_name="Meta Description",
        help_text="Описание для поисковых систем"
    )

    # ⚙️ Настройки отображения
    display_order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def get_products_count(self):
        """📊 Количество товаров в категории"""
        return self.products.count()

    def get_all_children(self):
        """🌳 Получение всех дочерних категорий рекурсивно"""
        children = []
        for child in self.children.all():
            children.append(child)
            children.extend(child.get_all_children())
        return children

    def is_boat_category(self):
        """🛥️ Проверка - является ли категория лодочной"""
        return self.category_type == 'boats'

    def is_car_category(self):
        """🚗 Проверка - является ли категория автомобильной"""
        return self.category_type == 'cars'

    def get_seo_title(self):
        """🔍 SEO заголовок категории"""
        if self.meta_title:
            return self.meta_title

        if self.category_type == 'boats':
            return f"Коврики для лодок {self.category_name} - купить в интернет-магазине"
        else:
            return f"Автомобильные коврики {self.category_name} - купить недорого"

    def get_seo_description(self):
        """🔍 SEO описание категории"""
        if self.meta_description:
            return self.meta_description

        if self.category_type == 'boats':
            return f"Коврики для лодок {self.category_name}. " \
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
        db_table = 'products_category'  # ✅ ДОБАВЛЕНО: сохраняем старое имя таблицы


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
        db_table = 'products_kitvariant'  # ✅ ДОБАВЛЕНО: сохраняем старое имя таблицы


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

    # 🛥️ ПОЛЯ ДЛЯ ЛОДОК (соответствуют БД)
    boat_mat_length = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Длина коврика для лодки (см)",
        help_text="Заполняется только для лодочных товаров"
    )
    boat_mat_width = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Ширина коврика для лодки (см)",
        help_text="Заполняется только для лодочных товаров"
    )

    # 🔍 SEO поля
    page_title = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Заголовок страницы"
    )
    meta_description = models.TextField(
        blank=True, null=True,
        verbose_name="Meta Description"
    )

    # Методы для определения типа товара
    def is_boat_product(self):
        """🛥️ Проверка - является ли товар лодочным"""
        return self.category and self.category.category_type == 'boats'

    def is_car_product(self):
        """🚗 Проверка - является ли товар автомобильным"""
        return self.category and self.category.category_type == 'cars'

    def get_boat_dimensions(self):
        """🛥️ Получение размеров лодки в читаемом формате"""
        if self.boat_mat_length and self.boat_mat_width:
            return f"{self.boat_mat_length}×{self.boat_mat_width} см"
        elif self.boat_mat_length:
            return f"Длина: {self.boat_mat_length} см"
        elif self.boat_mat_width:
            return f"Ширина: {self.boat_mat_width} см"
        return None

    def get_main_image(self):
        """🖼️ Получение главного изображения товара"""
        main_image = self.product_images.filter(is_main=True).first()
        if main_image:
            return main_image
        return self.product_images.first()

    def get_price_display(self):
        """💰 Отображение цены в удобном формате"""
        if self.price:
            return f"{self.price:,}".replace(',', ' ') + " BYN"
        return "Цена не указана"

    def get_rating(self):
        """⭐ Средний рейтинг товара"""
        reviews = self.reviews.all()
        if reviews:
            return sum([review.stars for review in reviews]) / len(reviews)
        return 0

    def get_product_price_by_kit(self, kit_code):
        """💰 Расчет цены товара с учетом комплектации"""
        base_price = self.price or 0

        if kit_code:
            kit_variant = KitVariant.objects.filter(code=kit_code).first()
            if kit_variant:
                return base_price + float(kit_variant.price_modifier)

        return base_price

    def __str__(self):
        return self.product_name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']
        db_table = 'products_product'  # ✅ ДОБАВЛЕНО: сохраняем старое имя таблицы


class ProductImage(BaseModel):
    """🖼️ Модель изображений товаров"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name="product_images", verbose_name="Товар"
    )
    image = models.ImageField(
        upload_to='product',
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
        db_table = 'products_productimage'  # ✅ ДОБАВЛЕНО: сохраняем старое имя таблицы


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
        db_table = 'products_color'  # ✅ ДОБАВЛЕНО: сохраняем старое имя таблицы


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
        db_table = 'products_coupon'  # ✅ ДОБАВЛЕНО: сохраняем старое имя таблицы


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
        db_table = 'products_productreview'  # ✅ ДОБАВЛЕНО: сохраняем старое имя таблицы


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
        parts = [self.product.product_name]

        if self.kit_variant:
            parts.append(f"Комплектация: {self.kit_variant.name}")

        if self.carpet_color:
            parts.append(f"Коврик: {self.carpet_color.name}")

        if self.border_color:
            parts.append(f"Окантовка: {self.border_color.name}")

        if self.has_podpyatnik:
            parts.append("С подпятником")

        return " | ".join(parts)

    def __str__(self):
        return f"Избранное {self.user.username}: {self.product.product_name}"

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        ordering = ['-added_on']
        unique_together = ('user', 'product', 'kit_variant')
        db_table = 'products_wishlist'  # ✅ ДОБАВЛЕНО: сохраняем старое имя таблицы

# 🔧 КОММЕНТАРИЙ ДЛЯ РАЗРАБОТЧИКА:
#
# ✅ ДОБАВЛЕНО: db_table ко всем моделям для сохранения старых имен таблиц
# ✅ СОХРАНЕНО: Вся функциональность моделей без изменений
# ✅ СОХРАНЕНО: Все методы, свойства и связи между моделями
# ✅ СОХРАНЕНО: Все Meta-опции (verbose_name, ordering, unique_together)
#
# 🎯 ЦЕЛЬ: После переименования приложения products → references
# Django ищет таблицы с префиксом references_, но в БД они
# все еще называются products_*
#
# 💡 РЕШЕНИЕ: Указываем явно старые имена таблиц через db_table
#
# ⚠️ ВРЕМЕННО: В будущем (этап 7) эти модели будут удалены
# и заменены на отдельные CarProduct/BoatProduct, поэтому
# переименование таблиц в БД не имеет смысла
#
# 🚀 РЕЗУЛЬТАТ: Сайт будет работать с переименованным приложением
# используя существующие данные в БД