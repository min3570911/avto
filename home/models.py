# 📁 home/models.py - ФИНАЛЬНАЯ ВЕРСИЯ с CompanyDescription
# 🆕 ДОБАВЛЕНО: CompanyDescription для описания компании
# ✅ СОХРАНЕНО: Все существующие модели без изменений

from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from django_ckeditor_5.fields import CKEditor5Field


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


# 🎬 Hero-секция главной страницы
class HeroSection(BaseModel):
    """🎬 Hero-секция главной страницы"""
    title = models.CharField(max_length=200, verbose_name="Заголовок", default="EVA коврики в Минске")
    subtitle = models.CharField(
        max_length=300,
        verbose_name="Подзаголовок",
        default="Премиум коврики из экологически чистого материала"
    )

    # 🎥 Медиа контент
    video = models.FileField(
        upload_to='hero_videos/',
        blank=True,
        null=True,
        verbose_name="Фоновое видео",
        help_text="MP4 файл для фонового видео (рекомендуется до 10MB)"
    )
    fallback_image = models.ImageField(
        upload_to='hero_images/',
        blank=True,
        null=True,
        verbose_name="Изображение-заглушка",
        help_text="Отображается если видео не загружается"
    )

    # 🎯 Кнопка действия
    button_text = models.CharField(
        max_length=50,
        verbose_name="Текст кнопки",
        default="Смотреть каталог"
    )
    button_link = models.URLField(
        verbose_name="Ссылка кнопки",
        default="/products/"
    )

    # ⚙️ Настройки
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def __str__(self):
        return f"Hero-секция: {self.title}"

    class Meta:
        verbose_name = "Hero-секция"
        verbose_name_plural = "Hero-секции"
        ordering = ['-created_at']


class HeroAdvantage(BaseModel):
    """🎯 Преимущества для hero-секции"""
    hero_section = models.ForeignKey(
        HeroSection,
        on_delete=models.CASCADE,
        related_name='advantages',
        verbose_name="Hero-секция"
    )

    # 🎨 Иконка преимущества
    icon_file = models.ImageField(
        upload_to='hero_icons/',
        blank=True,
        null=True,
        verbose_name="Файл иконки",
        help_text="SVG или PNG файл (рекомендуется 64x64px)"
    )
    icon = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Эмодзи иконка",
        help_text="Альтернатива файлу - эмодзи или текст"
    )

    # 📝 Содержимое
    title = models.CharField(max_length=100, verbose_name="Заголовок преимущества")
    description = models.CharField(max_length=200, verbose_name="Описание")

    # ⚙️ Настройки
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    def __str__(self):
        return f"{self.title} (Hero: {self.hero_section.title})"

    class Meta:
        verbose_name = "Преимущество Hero-секции"
        verbose_name_plural = "Преимущества Hero-секции"
        ordering = ['order', 'created_at']


# 🆕 НОВАЯ МОДЕЛЬ: CompanyDescription для описания компании (синглтон)
class CompanyDescription(BaseModel):
    """📝 Описание компании для главной страницы (только один экземпляр)"""

    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок",
        default="О нашей компании",
        help_text="Заголовок блока описания компании"
    )

    content = CKEditor5Field(
        verbose_name="Описание компании",
        help_text="Текст с описанием компании, продукции, преимуществ",
        config_name='default'  # 🎨 Используем существующий CKEditor 5
    )

    def __str__(self):
        return f"📝 {self.title}"

    class Meta:
        verbose_name = "Описание компании"
        verbose_name_plural = "Описание компании"

    def save(self, *args, **kwargs):
        """💾 Синглтон логика - разрешить только один экземпляр"""
        if CompanyDescription.objects.exists() and not self.pk:
            return  # 🚫 Не создавать новые записи, если уже есть
        super().save(*args, **kwargs)

# 🚚 НОВАЯ МОДЕЛЬ: DeliveryOption для способов доставки и оплаты
class DeliveryOption(BaseModel):
    """🚚 Способы доставки и оплаты"""

    # 📝 Основная информация
    title = models.CharField(
        max_length=100,
        verbose_name="Название способа",
        help_text="Например: Курьерская доставка, Почта, Транспортная компания"
    )

    description = models.TextField(
        verbose_name="Описание",
        help_text="Подробное описание условий доставки"
    )

    # 💰 Стоимость
    price_info = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Информация о стоимости",
        help_text="Например: Бесплатно, От 10 руб., По тарифам перевозчика"
    )

    # ⏱️ Сроки
    delivery_time = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Сроки доставки",
        help_text="Например: 1-2 дня, 2-3 дня, В день заказа"
    )

    # 🌍 Зона доставки
    coverage_area = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Зона доставки",
        help_text="Например: Минск в пределах МКАД, По всей Беларуси"
    )

    # 💳 Способы оплаты
    payment_methods = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name="Способы оплаты",
        help_text="Например: Наличными курьеру, Предоплата, Наложенный платеж"
    )

    # 📋 Дополнительные условия
    additional_info = models.TextField(
        blank=True,
        null=True,
        verbose_name="Дополнительная информация",
        help_text="Особые условия, ограничения, примечания"
    )

    # 🎨 Иконка
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Иконка",
        help_text="Класс иконки или эмодзи (например: fas fa-truck, 🚚)"
    )

    # ⚙️ Настройки
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Отображать на сайте"
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок отображения"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Способ доставки"
        verbose_name_plural = "Способы доставки"
        ordering = ['order', 'title']


# 📧 НОВАЯ МОДЕЛЬ: ContactMessage для сообщений обратной связи
class ContactMessage(BaseModel):
    """📧 Сообщения обратной связи от клиентов"""

    # 👤 Информация о клиенте
    name = models.CharField(
        max_length=100,
        verbose_name="Имя",
        help_text="Имя отправителя"
    )
    email = models.EmailField(
        verbose_name="Email",
        help_text="Email для ответа"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Телефон",
        help_text="Телефон клиента (необязательно)"
    )

    # 📝 Содержание сообщения
    subject = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Тема",
        help_text="Тема сообщения"
    )
    message = models.TextField(
        verbose_name="Сообщение",
        help_text="Текст сообщения от клиента"
    )

    # 🔧 Статус обработки
    is_processed = models.BooleanField(
        default=False,
        verbose_name="Обработано",
        help_text="Отмечается когда на сообщение ответили"
    )

    # 💬 Ответ администратора
    admin_reply = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ответ администратора",
        help_text="Ответ или комментарий администратора"
    )

    # 📅 Дата ответа
    replied_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Дата ответа",
        help_text="Когда был дан ответ"
    )

    def __str__(self):
        subject_part = f" - {self.subject}" if self.subject else ""
        status = "✅" if self.is_processed else "⏳"
        return f"{status} {self.name} ({self.email}){subject_part}"

    class Meta:
        verbose_name = "Сообщение обратной связи"
        verbose_name_plural = "Сообщения обратной связи"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Автоматически ставим дату ответа если добавили admin_reply"""
        if self.admin_reply and not self.replied_at:
            from django.utils import timezone
            self.replied_at = timezone.now()
            self.is_processed = True
        super().save(*args, **kwargs)


# 🔧 ИТОГОВЫЕ ИЗМЕНЕНИЯ В ФАЙЛЕ:
# ✅ ДОБАВЛЕНО: CompanyDescription - простая модель для описания компании
# ✅ ДОБАВЛЕНО: ContactMessage - модель для сообщений обратной связи
# ✅ ФУНКЦИИ:
#    - Заголовок и содержимое с CKEditor 5
#    - Синглтон логика (только один экземпляр)
#    - Система обратной связи с отслеживанием статуса
#    - Автоматическое управление датами ответов
# ✅ БЕЗОПАСНОСТЬ: Валидация в методе save()
# ✅ СОХРАНЕНО: Все существующие модели без изменений