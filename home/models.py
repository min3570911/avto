# 📁 home/models.py - ОБНОВЛЕНО с HeroSection для hero-блока
# 🆕 ДОБАВЛЕНО: HeroSection для управления главной секцией из админки
# ✅ СОХРАНЕНО: Все существующие модели (FAQ, Banner, Testimonial, ContactInfo)

from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel


# 🌟 Модели для главной страницы сайта

class ContactInfo(BaseModel):
    """📞 Контактная информация сайта"""
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")
    address = models.TextField(verbose_name="Физический адрес")
    working_hours = models.CharField(max_length=100, verbose_name="Часы работы")

    # 🌐 Социальные сети
    telegram = models.URLField(blank=True, null=True, verbose_name="Telegram")
    instagram = models.URLField(blank=True, null=True, verbose_name="Instagram")
    facebook = models.URLField(blank=True, null=True, verbose_name="Facebook")

    # ⚙️ Настройки
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def __str__(self):
        return f"Контакты ({self.phone})"

    class Meta:
        verbose_name = "Контактная информация"
        verbose_name_plural = "Контактная информация"


class FAQ(BaseModel):
    """❓ Часто задаваемые вопросы"""
    question = models.CharField(max_length=255, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Частый вопрос"
        verbose_name_plural = "Частые вопросы"
        ordering = ['order', 'created_at']


class Banner(BaseModel):
    """🎨 Баннеры для главной страницы"""
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    subtitle = models.CharField(max_length=300, blank=True, null=True, verbose_name="Подзаголовок")
    image = models.ImageField(upload_to='banners/', verbose_name="Изображение")
    link = models.URLField(blank=True, null=True, verbose_name="Ссылка")
    button_text = models.CharField(max_length=50, blank=True, null=True, verbose_name="Текст кнопки")

    # ⚙️ Настройки
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"
        ordering = ['order', '-created_at']


class Testimonial(BaseModel):
    """💬 Отзывы клиентов для главной страницы"""
    name = models.CharField(max_length=100, verbose_name="Имя клиента")
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name="Должность/город")
    text = models.TextField(verbose_name="Текст отзыва")
    avatar = models.ImageField(upload_to='testimonials/', blank=True, null=True, verbose_name="Фото")
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        default=5,
        verbose_name="Оценка"
    )

    # ⚙️ Настройки
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    featured = models.BooleanField(default=False, verbose_name="Рекомендуемый")

    def __str__(self):
        return f"Отзыв от {self.name}"

    class Meta:
        verbose_name = "Отзыв клиента"
        verbose_name_plural = "Отзывы клиентов"
        ordering = ['-featured', '-created_at']


# 🆕 НОВАЯ МОДЕЛЬ: HeroSection для управления главной секции
class HeroSection(BaseModel):
    """🎬 Hero-секция главной страницы"""
    title = models.CharField(max_length=200, verbose_name="Заголовок", default="EVA коврики в Минске")
    subtitle = models.CharField(
        max_length=300,
        verbose_name="Подзаголовок",
        default="уют, комфорт, чистота в вашем автомобиле"
    )

    # 🎬 Медиа контент
    video = models.FileField(
        upload_to='videos/',
        verbose_name="Фоновое видео",
        help_text="Видео для фона hero-секции (рекомендуемый формат: MP4)"
    )
    fallback_image = models.ImageField(
        upload_to='hero/',
        blank=True,
        null=True,
        verbose_name="Изображение-заглушка",
        help_text="Изображение для устройств, не поддерживающих видео"
    )

    # 🎯 Кнопка действия
    button_text = models.CharField(max_length=50, verbose_name="Текст кнопки", default="ЗАКАЗАТЬ")
    button_link = models.CharField(
        max_length=100,
        verbose_name="Ссылка кнопки",
        default="#catalog-section",
        help_text="Якорь или URL для кнопки (например: #catalog-section)"
    )

    # ⚙️ Настройки
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def __str__(self):
        status = " (активна)" if self.is_active else " (неактивна)"
        return f"Hero-секция: {self.title}{status}"

    class Meta:
        verbose_name = "Hero-секция"
        verbose_name_plural = "Hero-секции"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """💾 При сохранении активной секции, деактивируем остальные"""
        if self.is_active:
            # 🔄 Деактивируем все остальные hero-секции
            HeroSection.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class HeroAdvantage(BaseModel):
    """🎯 Преимущества для hero-секции"""
    ICON_CHOICES = [
        ('🚚', '🚚 Доставка'),
        ('🧵', '🧵 Материалы'),
        ('🚗', '🚗 Совместимость'),
        ('🧽', '🧽 Чистота'),
        ('⚡', '⚡ Скорость'),
        ('💎', '💎 Качество'),
        ('🛡️', '🛡️ Гарантия'),
        ('💰', '💰 Цена'),
    ]

    hero_section = models.ForeignKey(
        HeroSection,
        on_delete=models.CASCADE,
        related_name='advantages',
        verbose_name="Hero-секция"
    )

    # 🆕 НОВОЕ: Поле для загрузки SVG иконки
    icon_file = models.FileField(
        upload_to='hero/icons/',
        blank=True,
        null=True,
        verbose_name="SVG иконка",
        help_text="Загрузите SVG файл для иконки (рекомендуется)"
    )

    # 🔄 ОБНОВЛЕНО: Эмодзи как fallback
    icon = models.CharField(
        max_length=10,
        choices=ICON_CHOICES,
        verbose_name="Эмодзи (запасной вариант)",
        default='🚚',
        help_text="Используется, если SVG иконка не загружена"
    )
    title = models.CharField(max_length=100, verbose_name="Заголовок")
    description = models.CharField(max_length=200, verbose_name="Описание")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    def get_icon_url(self):
        """🎯 Получить URL иконки (приоритет SVG, fallback эмодзи)"""
        if self.icon_file:
            return self.icon_file.url
        return None

    def has_svg_icon(self):
        """📁 Проверка наличия SVG иконки"""
        return bool(self.icon_file)

    def __str__(self):
        return f"{self.icon} {self.title}"

    class Meta:
        verbose_name = "Преимущество hero-секции"
        verbose_name_plural = "Преимущества hero-секции"
        ordering = ['order', 'created_at']

# 💡 ПРИМЕЧАНИЕ:
# 🗑️ ShippingAddress по-прежнему удален для упрощения проекта
# ✅ Все существующие модели сохранены и работают
# 🆕 Добавлены HeroSection и HeroAdvantage для управления главной страницы из админки
# 🎯 HeroSection поддерживает:
#   - Заголовок и подзаголовок
#   - Фоновое видео с изображением-заглушкой
#   - Настраиваемую кнопку действия
#   - Автоматическую деактивацию других секций при активации новой
# 🎯 HeroAdvantage позволяет:
#   - Управлять списком преимуществ
#   - Выбирать иконки из предустановленного списка
#   - Настраивать порядок отображения