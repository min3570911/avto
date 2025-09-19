# 📁 common/models.py
# 🔒 ПОЛНАЯ СИСТЕМА МОДЕРАЦИИ ОТЗЫВОВ С АНТИ-СПАМ ЗАЩИТОЙ
# ✅ ОБНОВЛЕНО: Добавлены поля для анонимных отзывов и анти-спам защиты
# 🛡️ ДОБАВЛЕНО: Поля аудита, анти-спам метрики и методы защиты

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.conf import settings
from base.models import BaseModel

# Импорт моделей для правильных ссылок
from products.models import Color, KitVariant


class ProductReview(BaseModel):
    """📝 Универсальные отзывы для любых товаров с полной системой модерации и анти-спам защитой"""

    # 🔗 Generic FK для UUID primary keys
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    product = GenericForeignKey('content_type', 'object_id')

    # 👤 Пользователь и автор отзыва (ИЗМЕНЕНО: теперь опциональное для анонимных)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True,
        verbose_name="Пользователь",
        help_text="Пустое для анонимных отзывов"
    )

    # 🆕 НОВЫЕ ПОЛЯ для анонимных отзывов
    reviewer_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Имя автора",
        help_text="Имя для анонимных отзывов"
    )

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

    # 🆕 НОВЫЕ ПОЛЯ для анти-спам защиты
    ip_address = models.GenericIPAddressField(
        verbose_name="IP адрес",
        help_text="IP адрес отправителя отзыва"
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Браузер и ОС пользователя"
    )

    form_submit_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Время заполнения формы",
        help_text="Время в секундах от загрузки до отправки формы"
    )

    is_suspicious = models.BooleanField(
        default=False,
        verbose_name="Подозрительный",
        help_text="Отмечен системой как подозрительный"
    )

    spam_score = models.FloatField(
        default=0.0,
        verbose_name="Оценка спама",
        help_text="Автоматическая оценка спама от 0 до 100"
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

    # ==================== НОВЫЕ МЕТОДЫ ДЛЯ АНОНИМНЫХ ОТЗЫВОВ ====================

    def get_author_name(self):
        """👤 Получение имени автора (зарегистрированного или анонимного)"""
        if self.user:
            # Предпочитаем полное имя, если есть
            if self.user.first_name:
                return f"{self.user.first_name} {self.user.last_name}".strip()
            return self.user.username
        elif self.reviewer_name:
            return self.reviewer_name
        else:
            return "Аноним"

    def is_anonymous_review(self):
        """🔍 Проверка является ли отзыв анонимным"""
        return self.user is None

    def get_author_type(self):
        """🏷️ Тип автора отзыва"""
        if self.user:
            return "Зарегистрированный пользователь"
        else:
            return "Анонимный пользователь"

    # ==================== АНТИ-СПАМ МЕТОДЫ ====================

    def calculate_spam_score(self):
        """🎯 Пересчет спам-оценки отзыва"""
        # Импортируем здесь чтобы избежать циклического импорта
        try:
            from common.utils import calculate_spam_score

            review_data = {
                'content': self.content,
                'ip_address': self.ip_address,
                'form_submit_time': self.form_submit_time or 0,
                'user_agent': self.user_agent,
            }

            new_score = calculate_spam_score(review_data)
            self.spam_score = new_score

            # Обновляем флаг подозрительности
            spam_threshold = getattr(settings, 'SPAM_DETECTION', {}).get('SPAM_SCORE_THRESHOLD', 70.0)
            self.is_suspicious = new_score >= spam_threshold

            return new_score
        except ImportError:
            # Если utils недоступны, возвращаем базовую оценку
            return 0.0

    def mark_as_suspicious(self, reason=""):
        """🚨 Пометить отзыв как подозрительный"""
        self.is_suspicious = True
        if self.spam_score < 70:
            self.spam_score = 70  # Минимальная оценка для подозрительных
        self.save()

    def mark_as_safe(self):
        """✅ Пометить отзыв как безопасный"""
        self.is_suspicious = False
        if self.spam_score > 30:
            self.spam_score = 30  # Максимальная оценка для безопасных
        self.save()

    def get_spam_level(self):
        """📊 Уровень спама в виде текста"""
        score = self.spam_score
        if score >= 80:
            return "Высокий"
        elif score >= 50:
            return "Средний"
        elif score >= 20:
            return "Низкий"
        else:
            return "Минимальный"

    def get_spam_color(self):
        """🎨 Цвет для отображения уровня спама"""
        score = self.spam_score
        if score >= 80:
            return "danger"  # Красный
        elif score >= 50:
            return "warning"  # Желтый
        elif score >= 20:
            return "info"  # Синий
        else:
            return "success"  # Зеленый

    # ==================== СЧЕТЧИКИ ====================

    def like_count(self):
        """👍 Количество лайков"""
        return self.likes.count()

    def dislike_count(self):
        """👎 Количество дизлайков"""
        return self.dislikes.count()

    # ==================== МЕТОДЫ МОДЕРАЦИИ ====================

    def approve(self, moderator=None):
        """✅ Одобрить отзыв"""
        self.is_approved = True
        # При одобрении снижаем подозрительность
        if self.is_suspicious and self.spam_score < 70:
            self.is_suspicious = False
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
        """🔄 Сбросить статус модерации"""
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
        """🔍 Был ли отзыв модерирован"""
        # TODO: После добавления полей аудита:
        # return self.moderated_by is not None
        return self.is_approved  # Временно считаем модерированным, если одобрен

    def needs_attention(self):
        """⚠️ Требует ли отзыв особого внимания"""
        return self.is_suspicious or self.spam_score >= 50

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
    def get_suspicious_count(cls):
        """🚨 Количество подозрительных отзывов"""
        return cls.objects.filter(is_suspicious=True).count()

    @classmethod
    def get_anonymous_count(cls):
        """👤 Количество анонимных отзывов"""
        return cls.objects.filter(user__isnull=True).count()

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
    def get_spam_stats(cls):
        """📊 Статистика спама"""
        total = cls.objects.count()
        if total == 0:
            return {'total': 0, 'suspicious': 0, 'high_spam': 0, 'spam_rate': 0}

        suspicious = cls.get_suspicious_count()
        high_spam = cls.objects.filter(spam_score__gte=80).count()

        return {
            'total': total,
            'suspicious': suspicious,
            'high_spam': high_spam,
            'spam_rate': round((suspicious / total) * 100, 1)
        }

    @classmethod
    def get_moderation_stats(cls):
        """📊 Полная статистика модерации"""
        spam_stats = cls.get_spam_stats()
        return {
            'total': cls.objects.count(),
            'pending': cls.get_pending_count(),
            'approved': cls.get_approved_count(),
            'suspicious': cls.get_suspicious_count(),
            'anonymous': cls.get_anonymous_count(),
            'today_pending': cls.get_today_pending_count(),
            'approval_rate': cls.get_approval_rate(),
            'spam_rate': spam_stats['spam_rate'],
        }

    # ==================== СОХРАНЕНИЕ ====================

    def save(self, *args, **kwargs):
        """💾 Переопределение сохранения с автоматическим расчетом спам-оценки"""
        # Автоматически рассчитываем спам-оценку при первом сохранении
        if not self.pk and self.ip_address:
            self.calculate_spam_score()

        super().save(*args, **kwargs)

    # ==================== СТРОКОВОЕ ПРЕДСТАВЛЕНИЕ ====================

    def __str__(self):
        status = " [На модерации]" if not self.is_approved else ""
        spam_flag = " [СПАМ]" if self.is_suspicious else ""
        author = self.get_author_name()
        product_name = self.get_product_name()
        return f"Отзыв от {author} на {product_name} ({self.stars}⭐){status}{spam_flag}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-date_added']
        db_table = 'products_productreview'  # Используем существующую таблицу
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["is_approved", "date_added"]),
            models.Index(fields=["user", "date_added"]),
            models.Index(fields=["is_suspicious", "spam_score"]),  # Новый индекс для анти-спам
            models.Index(fields=["ip_address", "date_added"]),  # Новый индекс для IP
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
        db_table = 'products_wishlist'  # Используем существующую таблицу
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