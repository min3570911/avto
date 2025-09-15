# 📁 common/models.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
# ✅ ФИКС: Правильные импорты и Generic FK для UUID primary keys
# 🔧 ИСПРАВЛЕНО: Все ошибки импортов и определений полей

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey  # ✅ ИСПРАВЛЕНО: правильный импорт
from base.models import BaseModel

# ✅ ИСПРАВЛЕНО: добавим импорт моделей для правильных ссылок
from products.models import Color, KitVariant


class ProductReview(BaseModel):
    """📝 Универсальные отзывы для любых товаров"""

    # ✅ ИСПРАВЛЕНО: Generic FK для UUID primary keys
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()  # ✅ ПРАВИЛЬНО: для UUID primary keys
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

    # ✅ ИСПРАВЛЕНО: Generic FK для связи с любым товаром (Product, BoatProduct, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()  # ✅ ПРАВИЛЬНО: для UUID primary keys
    product = GenericForeignKey('content_type', 'object_id')

    # ✅ ИСПРАВЛЕНО: Поля для конфигурации с правильными импортами
    # KitVariant остаётся в 'products', т.к. это специфичная для автомобилей опция
    kit_variant = models.ForeignKey(
        KitVariant,  # ✅ ИСПРАВЛЕНО: используем импортированную модель
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="wishlist_items"
    )
    carpet_color = models.ForeignKey(
        Color,  # ✅ ИСПРАВЛЕНО: используем импортированную модель
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="wishlist_carpet_items"
    )
    border_color = models.ForeignKey(
        Color,  # ✅ ИСПРАВЛЕНО: используем импортированную модель
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
        db_table = 'products_wishlist'  # Сохраняем имя старой таблицы
        # Индекс для ускорения поиска по пользователю и товару
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user"]),
        ]


# 🔧 ДОПОЛНИТЕЛЬНО: можно добавить админку для проверки
class ProductReviewAdmin:
    """👨‍💼 Админка для универсальных отзывов"""

    def __str__(self):
        """🔍 Информативное представление для админки"""
        return f"ProductReview(user={self.user}, product={self.product})"