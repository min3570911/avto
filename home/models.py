# 📁 home/models.py - БЕЗ ShippingAddress
# 🗑️ ПОЛНОСТЬЮ УДАЛЕН ShippingAddress для упрощения проекта

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

# 🗑️ УДАЛЕНО:
# - class ShippingAddress (больше не нужен)
# - Все связанные с адресами доставки модели
# - Импорты, связанные с django_countries

# 💡 ПРИМЕЧАНИЕ:
# Адреса доставки теперь указываются прямо в заказах (Order.shipping_address)
# Это упрощает структуру и убирает циклические импорты

# ✅ ОСТАВЛЕНО:
# - Контактная информация сайта
# - FAQ для клиентов
# - Баннеры для главной страницы
# - Отзывы клиентов