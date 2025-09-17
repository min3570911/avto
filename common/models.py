# 📁 common/models.py
# 🔒 ПОЛНАЯ СИСТЕМА МОДЕРАЦИИ ОТЗЫВОВ
# ✅ ИСПРАВЛЕНО: Добавлено поле reviewer_email для устранения ошибки NOT NULL
# 🔧 ДОБАВЛЕНО: Поля аудита модерации, методы и статистика

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from base.models import BaseModel

# Импорт моделей для правильных ссылок
from products.models import Color, KitVariant


class ProductReview(BaseModel):
    """📝 Универсальные отзывы для любых товаров с полной системой модерации"""

    # 🔗 Generic FK для UUID primary keys
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    product = GenericForeignKey('content_type', 'object_id')

    # 👤 Пользователь и автор отзыва
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')

    # 📊 Содержание отзыва
    stars = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name="Оценка"
    )
    content = models.TextField(verbose_name="Содержание отзыва")
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    # 🔒 СИСТЕМА МОДЕРАЦИИ (базовая версия)
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Одобрен",
        help_text="Отзыв прошел модерацию и виден всем пользователям"
    )

    # 📅 ПОЛЯ АУДИТА БУДУТ ДОБАВЛЕНЫ ЧЕРЕЗ МИГРАЦИЮ
    # moderated_by и moderated_at добавим позже через отдельную миграцию

    # 👍👎 Реакции пользователей
    likes = models.ManyToManyField(
        User,
        related_name="liked_reviews",
        blank=True,
        verbose_name="Лайки"
    )
    dislikes = models.ManyToManyField(
        User,
        related_name="disliked_reviews",
        blank=True,
        verbose_name="Дизлайки"
    )

    # ==================== СЧЕТЧИКИ ====================

    def like_count(self):
        """👍 Количество лайков"""
        return self.likes.count()

    def dislike_count(self):
        """👎 Количество дизлайков"""
        return self.dislikes.count()

    # ==================== МЕТОДЫ МОДЕРАЦИИ (базовые) ====================

    def approve(self, moderator=None):
        """✅ Одобрить отзыв (базовая версия)"""
        self.is_approved = True
        # TODO: После добавления полей аудита через миграцию:
        # self.moderated_by = moderator
        # self.moderated_at = timezone.now()
        self.save()
        return True

    def reject(self, moderator=None):
        """❌ Отклонить отзыв (удалить)"""
        # TODO: После добавления полей аудита можно логировать действие модератора
        self.delete()
        return True

    def reset_moderation(self):
        """🔄 Сбросить статус модерации (базовая версия)"""
        self.is_approved = False
        # TODO: После добавления полей аудита:
        # self.moderated_by = None
        # self.moderated_at = None
        self.save()
        return True

    # ==================== ПРОВЕРКИ СТАТУСА ====================

    def is_pending_approval(self):
        """⏳ Ожидает ли отзыв модерации"""
        return not self.is_approved

    def is_moderated(self):
        """🔍 Был ли отзыв модерирован (базовая проверка)"""
        # TODO: После добавления полей аудита:
        # return self.moderated_by is not None
        return self.is_approved  # Временно считаем модерированным, если одобрен

    # ==================== ИНФОРМАЦИЯ О ТОВАРЕ ====================

    def get_product_name(self):
        """🏷️ Название товара (универсальное)"""
        try:
            if hasattr(self.product, 'product_name'):
                return self.product.product_name
            elif hasattr(self.product, 'name'):
                return self.product.name
            else:
                return str(self.product)
        except (AttributeError, TypeError):
            return "Товар не найден"

    def get_product_url(self):
        """🔗 URL товара (универсальный)"""
        try:
            if hasattr(self.product, 'get_absolute_url'):
                return self.product.get_absolute_url()
            elif hasattr(self.product, 'slug'):
                # Определяем тип товара для правильного URL
                if self.content_type.app_label == 'products':
                    return f'/products/{self.product.slug}/'
                elif self.content_type.app_label == 'boats':
                    return f'/boats/{self.product.slug}/'
                else:
                    return f'/admin/{self.content_type.app_label}/{self.content_type.model}/{self.object_id}/'
            else:
                return "#"
        except (AttributeError, TypeError):
            return "#"

    def get_product_type(self):
        """🔍 Тип товара"""
        if self.content_type:
            app_label = self.content_type.app_label
            if app_label == 'products':
                return 'Автомобиль'
            elif app_label == 'boats':
                return 'Лодка'
        return 'Неизвестно'

    # ==================== ОТОБРАЖЕНИЕ ====================

    def get_stars_display(self):
        """⭐ Визуальное отображение рейтинга звездочками"""
        return "★" * self.stars + "☆" * (5 - self.stars)

    # ==================== СТАТИСТИЧЕСКИЕ МЕТОДЫ ====================

    @classmethod
    def get_pending_count(cls):
        """📊 Количество отзывов на модерации"""
        return cls.objects.filter(is_approved=False).count()

    @classmethod
    def get_approved_count(cls):
        """📊 Количество одобренных отзывов"""
        return cls.objects.filter(is_approved=True).count()

    @classmethod
    def get_today_pending_count(cls):
        """📊 Количество отзывов на модерации за сегодня"""
        today = timezone.now().date()
        return cls.objects.filter(
            is_approved=False,
            date_added__date=today
        ).count()

    @classmethod
    def get_approval_rate(cls):
        """📊 Процент одобрения отзывов"""
        total = cls.objects.count()
        if total == 0:
            return 0
        approved = cls.get_approved_count()
        return round((approved / total) * 100, 1)

    @classmethod
    def get_moderation_stats(cls):
        """📊 Полная статистика модерации"""
        return {
            'total': cls.objects.count(),
            'pending': cls.get_pending_count(),
            'approved': cls.get_approved_count(),
            'today_pending': cls.get_today_pending_count(),
            'approval_rate': cls.get_approval_rate(),
        }

    # ==================== СОХРАНЕНИЕ ====================

    def save(self, *args, **kwargs):
        """💾 Переопределение сохранения для будущих нужд"""
        # В будущем здесь можно добавить дополнительную логику
        super().save(*args, **kwargs)

    # ==================== СТРОКОВОЕ ПРЕДСТАВЛЕНИЕ ====================

    def __str__(self):
        status = " [На модерации]" if not self.is_approved else ""
        product_name = self.get_product_name()
        return f"Отзыв от {self.user.username} на {product_name} ({self.stars}⭐){status}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-date_added']
        db_table = 'products_productreview'  # Используем существующую таблицу
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["is_approved", "date_added"]),
            models.Index(fields=["user", "date_added"]),
            # TODO: Добавить после миграции полей аудита:
            # models.Index(fields=["moderated_by", "moderated_at"]),
        ]


class Wishlist(BaseModel):
    """❤️ Универсальное избранное для всех типов товаров"""

    # 👤 Пользователь
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wishlist",
        verbose_name="Пользователь"
    )

    # 🔗 Generic FK для связи с любым товаром (Product, BoatProduct, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    product = GenericForeignKey('content_type', 'object_id')

    # ⚙️ Поля для конфигурации товара
    kit_variant = models.ForeignKey(
        KitVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Комплектация",
        help_text="Применимо только к автомобильным коврикам"
    )

    carpet_color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wishlist_carpet",
        verbose_name="Цвет коврика",
        limit_choices_to={'color_type': 'carpet'}
    )

    border_color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wishlist_border",
        verbose_name="Цвет окантовки",
        limit_choices_to={'color_type': 'border'}
    )

    has_podpyatnik = models.BooleanField(
        default=False,
        verbose_name="С подпятником",
        help_text="Применимо только к автомобильным коврикам"
    )

    # 📅 Дата добавления (для совместимости с admin.py)
    added_on = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )

    def __str__(self):
        product_name = getattr(self.product, 'product_name', str(self.product))
        return f"❤️ {self.user.username} → {product_name}"

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        ordering = ['-added_on']
        db_table = 'products_wishlist'  # ✅ ИСПРАВЛЕНО: Используем существующую таблицу
        indexes = [
            models.Index(fields=["user", "added_on"]),
            models.Index(fields=["content_type", "object_id"]),
        ]
        constraints = [
            # Уникальность: один товар один раз в избранном у пользователя
            models.UniqueConstraint(
                fields=['user', 'content_type', 'object_id'],
                name='unique_user_product_wishlist'
            )
        ]