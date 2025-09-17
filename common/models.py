# common/models.py
# Обновленная версия с модерацией отзывов
# Добавлено поле is_approved для контроля публикации отзывов

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from base.models import BaseModel

# Импорт моделей для правильных ссылок
from products.models import Color, KitVariant


class ProductReview(BaseModel):
    """Универсальные отзывы для любых товаров с модерацией"""

    # Generic FK для UUID primary keys
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    product = GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    stars = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    content = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    # НОВОЕ ПОЛЕ: Модерация отзывов
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Одобрен",
        help_text="Отзыв прошел модерацию и виден всем пользователям"
    )

    likes = models.ManyToManyField(User, related_name="liked_reviews", blank=True)
    dislikes = models.ManyToManyField(User, related_name="disliked_reviews", blank=True)

    def like_count(self):
        """Количество лайков"""
        return self.likes.count()

    def dislike_count(self):
        """Количество дизлайков"""
        return self.dislikes.count()

    def get_stars_display(self):
        """Визуальное отображение рейтинга звездочками"""
        return "★" * self.stars + "☆" * (5 - self.stars)

    def is_pending_approval(self):
        """Ожидает ли отзыв модерации"""
        return not self.is_approved

    def __str__(self):
        status = " [На модерации]" if not self.is_approved else ""
        return f"Отзыв от {self.user.username} на {self.product} ({self.stars}⭐){status}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-date_added']
        db_table = 'products_productreview'
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["is_approved", "date_added"]),  # Индекс для быстрой выборки одобренных отзывов
        ]


class Wishlist(BaseModel):
    """Универсальное избранное для всех типов товаров"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")

    # Generic FK для связи с любым товаром (Product, BoatProduct, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    product = GenericForeignKey('content_type', 'object_id')

    # Поля для конфигурации
    # KitVariant остаётся в 'products', т.к. это специфичная для автомобилей опция
    kit_variant = models.ForeignKey(
        KitVariant,
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
        db_table = 'products_wishlist'
        # Индекс для ускорения поиска по пользователю и товару
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user"]),
        ]