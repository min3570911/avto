# 📁 products/models.py
# 🛍️ Модели для системы интернет-магазина автоковриков
# ✅ УДАЛЕНО: ColorVariant, parent поле

from django.db import models
from base.models import BaseModel
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django_summernote.fields import SummernoteTextField

# 🎨 Определения типов цветов
COLOR_TYPE_CHOICES = (
    ('carpet', 'Коврик'),
    ('border', 'Окантовка')
)


class Category(BaseModel):
    """📂 Модель категорий товаров"""
    category_name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(unique=True, null=True, blank=True, verbose_name="URL-адрес")
    category_image = models.ImageField(upload_to="catgories", verbose_name="Изображение категории")

    def save(self, *args, **kwargs):
        """🔄 Автоматическое создание slug из названия категории"""
        self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.category_name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


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
    # 🗑️ УДАЛЕНО: parent поле (не используется в проекте)
    product_name = models.CharField(max_length=100, verbose_name="Название товара")
    slug = models.SlugField(unique=True, null=True, blank=True, verbose_name="URL-адрес")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name="products", verbose_name="Категория")
    # ✅ ИЗМЕНЕНО: price теперь необязательное поле (null=True, blank=True)
    price = models.IntegerField(verbose_name="Базовая цена", null=True, blank=True, default=0)
    product_desription = SummernoteTextField(
        verbose_name="Описание товара",
        help_text="Подробное описание товара с возможностью форматирования"
    )
    newest_product = models.BooleanField(default=False, verbose_name="Новый товар")

    def save(self, *args, **kwargs):
        """🔄 Автоматическое создание slug из названия товара"""
        self.slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.product_name

    # 🔧 ОСНОВНОЙ МЕТОД расчета цены по комплектации
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
        # ⚠️ Если базовая цена не указана, возвращаем 0
        return float(self.price) if self.price else 0

    # 💰 НОВЫЕ МЕТОДЫ для упрощения использования в шаблонах
    def get_salon_price(self):
        """
        🎯 Получает цену комплектации "Салон" для отображения в списках товаров

        Основной метод для использования в шаблонах без параметров.
        Возвращает цену самой популярной комплектации "Салон".

        @return: цену комплектации "Салон" из справочника KitVariant
        """
        return self.get_product_price_by_kit('salon')

    def get_default_price(self):
        """
        🏠 Получает цену по умолчанию (комплектация "Салон")

        Альтернативное название для метода get_salon_price() для большей ясности.
        Используется как основная цена товара в каталоге.

        @return: цену комплектации "Салон" как основную цену товара
        """
        return self.get_salon_price()

    def display_price(self):
        """
        📊 Отображает цену для админки с правильным форматированием

        Специальный метод для отображения цены в Django Admin
        с правильной валютой и форматированием.

        @return: отформатированную строку с ценой в рублях
        """
        price = self.get_salon_price()
        return f"{price:.0f} руб."  # 🔄 Убираем дробную часть для целых чисел

    display_price.short_description = "Цена (Салон)"

    # 📊 ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ
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
        unique_together = ('user', 'product')  # Один отзыв от пользователя на товар


class Color(BaseModel):
    """🎨 Модель для хранения доступных цветов ковриков и окантовки"""
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
            # Ищем опцию подпятник
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


# 🗑️ ПОЛНОСТЬЮ УДАЛЕНО:
# - class ColorVariant (устаревшая модель)
# - поле parent в модели Product (не используется)

# ✅ ИЗМЕНЕНИЯ:
# - Поле price в Product теперь необязательное (null=True, blank=True)
# - Добавлен default=0 для поля price
# - Обновлен метод get_product_price_by_kit() для обработки пустой цены