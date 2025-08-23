from django.db import models
from django.utils.html import mark_safe

from base.models import BaseModel
# 🔧 ИСПРАВЛЕНО: Импортируем хранилище из products, т.к. оно пока там
from products.storage import OverwriteStorage

# 🎨 Определения типов цветов
COLOR_TYPE_CHOICES = (
    ('carpet', 'Коврик'),
    ('border', 'Окантовка')
)


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
        # 🆕 Явно указываем имя таблицы, чтобы оно не изменилось
        db_table = 'products_color'


from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ProductReview(BaseModel):
    """📝 Универсальные отзывы для любых товаров"""

    # Generic FK - может ссылаться на любую модель
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    product = GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    stars = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    content = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    likes = models.ManyToManyField(User, related_name="liked_reviews", blank=True)
    dislikes = models.ManyToManyField(User, related_name="disliked_reviews", blank=True)

    def like_count(self):
        """👍 Количество лайков"""
        return self.likes.count()

    def dislike_count(self):
        """👎 Количество дизлайков"""
        return self.dislikes.count()

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product} ({self.stars}⭐)"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-date_added']
        db_table = 'products_productreview'
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class Wishlist(BaseModel):
    """❤️ Универсальное избранное для всех типов товаров"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")

    # Generic FK для связи с любым товаром (Product, BoatProduct, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    product = GenericForeignKey('content_type', 'object_id')

    # Поля для конфигурации, как и в CartItem
    # KitVariant остаётся в 'products', т.к. это специфичная для автомобилей опция
    kit_variant = models.ForeignKey(
        'products.KitVariant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="wishlist_items"
    )
    carpet_color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="wishlist_carpet_items"
    )
    border_color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="wishlist_border_items"
    )
    has_podpyatnik = models.BooleanField(default=False)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"❤️ {self.user.username} → {self.product}"

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        ordering = ['-added_on']
        db_table = 'products_wishlist' # Сохраняем имя старой таблицы
        # Индекс для ускорения поиска по пользователю и товару
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user"]),
        ]
