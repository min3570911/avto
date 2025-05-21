from django.db import models
from base.models import BaseModel
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.contrib.auth.models import User

# Определения типов цветов
COLOR_TYPE_CHOICES = (
    ('carpet', 'Коврик'),
    ('border', 'Окантовка')
)


class Category(BaseModel):
    category_name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(unique=True, null=True, blank=True, verbose_name="URL-адрес")
    category_image = models.ImageField(upload_to="catgories", verbose_name="Изображение категории")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.category_name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class ColorVariant(BaseModel):
    color_name = models.CharField(max_length=100, verbose_name="Название цвета")
    price = models.IntegerField(default=0, verbose_name="Цена")

    def __str__(self) -> str:
        return self.color_name

    class Meta:
        verbose_name = "Вариант цвета (устаревшее)"
        verbose_name_plural = "Варианты цветов (устаревшее)"


class KitVariant(BaseModel):
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


class Product(BaseModel):
    parent = models.ForeignKey(
        'self', related_name='variants', on_delete=models.CASCADE,
        blank=True, null=True, verbose_name="Родительский товар")
    product_name = models.CharField(max_length=100, verbose_name="Название товара")
    slug = models.SlugField(unique=True, null=True, blank=True, verbose_name="URL-адрес")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name="products", verbose_name="Категория")
    price = models.IntegerField(verbose_name="Базовая цена")
    product_desription = models.TextField(verbose_name="Описание товара")
    # Поле color_variant удалено
    newest_product = models.BooleanField(default=False, verbose_name="Новый товар")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.product_name

    def get_product_price_by_kit(self, kit_code='salon'):
        """
        🛒 Получает цену товара с учетом выбранной комплектации

        @param kit_code: код комплектации, по умолчанию 'salon'
        @return: полную стоимость комплектации, а не модификатор к базовой цене
        """
        # Получаем комплектацию из справочника
        kit = KitVariant.objects.filter(code=kit_code).first()
        if kit:
            return float(kit.price_modifier)  # Возвращаем полную стоимость комплектации
        return float(self.price)  # Запасной вариант - базовая цена

    def get_rating(self):
        total = sum(int(review['stars']) for review in self.reviews.values())
        if self.reviews.count() > 0:
            return total / self.reviews.count()
        else:
            return 0

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class ProductImage(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='product_images', verbose_name="Товар")
    image = models.ImageField(upload_to='product', verbose_name="Изображение")

    def img_preview(self):
        return mark_safe(f'<img src="{self.image.url}" width="500"/>')

    img_preview.short_description = "Предпросмотр изображения"

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"


class Coupon(BaseModel):
    coupon_code = models.CharField(max_length=10, verbose_name="Код купона")
    is_expired = models.BooleanField(default=False, verbose_name="Истёк")
    discount_amount = models.IntegerField(default=100, verbose_name="Сумма скидки")
    minimum_amount = models.IntegerField(default=500, verbose_name="Минимальная сумма заказа")

    class Meta:
        verbose_name = "Купон"
        verbose_name_plural = "Купоны"


class ProductReview(BaseModel):
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
        return self.likes.count()

    def dislike_count(self):
        return self.dislikes.count()

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"


class Color(BaseModel):
    """Модель для хранения доступных цветов ковриков и окантовки"""
    name = models.CharField(max_length=50, verbose_name="Название цвета")
    hex_code = models.CharField(max_length=7, verbose_name="HEX-код")
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок отображения")

    # Тип цвета
    color_type = models.CharField(
        max_length=10,
        choices=COLOR_TYPE_CHOICES,
        default='carpet',
        verbose_name="Тип применения"
    )

    # Поля для загрузки изображений
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
        """Отображение превью изображения коврика в админке"""
        if self.carpet_image:
            return mark_safe(f'<img src="{self.carpet_image.url}" height="50"/>')
        return "—"

    def border_preview(self):
        """Отображение превью изображения окантовки в админке"""
        if self.border_image:
            return mark_safe(f'<img src="{self.border_image.url}" height="50"/>')
        return "—"

    def get_image_url(self):
        """Возвращает URL изображения в зависимости от типа цвета"""
        if self.color_type == 'carpet' and self.carpet_image:
            return self.carpet_image.url
        elif self.color_type == 'border' and self.border_image:
            return self.border_image.url
        return ""

    carpet_preview.short_description = "Превью коврика"
    border_preview.short_description = "Превью окантовки"

    def __str__(self):
        return f"{self.name} ({self.get_color_type_display()})"

    class Meta:
        verbose_name = "Цвет"
        verbose_name_plural = "Цвета"


class Wishlist(BaseModel):
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

    class Meta:
        unique_together = ('user', 'product', 'kit_variant')
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"

    def __str__(self) -> str:
        return f'{self.user.username} - {self.product.product_name} - {self.kit_variant.name if self.kit_variant else "Без комплектации"}'