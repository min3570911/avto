# 📁 blog/models.py - Модели для раздела "Статьи"
# 📝 Блог для интернет-магазина автоковриков
# ✅ СОВРЕМЕННО: Переход на CKEditor 5

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
# ✅ НОВОЕ: Импорт CKEditor5Field из django-ckeditor-5
from django_ckeditor_5.fields import CKEditor5Field


class Category(models.Model):
    """📂 Категория статей"""
    name = models.CharField(
        max_length=200,
        verbose_name='Название категории'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='URL-адрес'
    )
    description = models.TextField(
        verbose_name='Описание категории',
        blank=True,
        help_text='Описание для SEO и отображения на странице категории'
    )
    image = models.ImageField(
        upload_to='blog/categories/',
        verbose_name='Изображение категории',
        blank=True,
        null=True,
        help_text='Рекомендуемый размер: 800x400 px'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок сортировки',
        help_text='Чем меньше число, тем выше в списке'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Категория статей'
        verbose_name_plural = 'Категории статей'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """🔗 Получить URL категории"""
        return reverse('blog:category_articles', kwargs={'slug': self.slug})

    def get_articles_count(self):
        """📊 Количество опубликованных статей в категории"""
        return self.articles.filter(is_published=True).count()


class Article(models.Model):
    """📰 Модель статьи блога"""
    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок статьи'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='URL-адрес',
        help_text='Автоматически генерируется из заголовка с .html в конце'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles',
        verbose_name='Автор'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='Категория'
    )
    featured_image = models.ImageField(
        upload_to='blog/articles/',
        verbose_name='Главное изображение',
        help_text='Рекомендуемый размер: 1200x600 px'
    )

    # ✅ НОВОЕ: Замена RichTextField на CKEditor5Field
    excerpt = CKEditor5Field(
        verbose_name='Краткое описание',
        help_text='Краткое описание для карточки статьи (анонс)',
        config_name='basic'  # 🎯 Используем базовую конфигурацию для анонса
    )
    content = CKEditor5Field(
        verbose_name='Содержание статьи',
        help_text='Полное содержание статьи с форматированием',
        config_name='blog'  # 🎯 Используем расширенную конфигурацию для блога
    )

    # 📊 Дополнительные поля
    views = models.PositiveIntegerField(
        default=0,
        verbose_name='Просмотры'
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано'
    )

    # 🕐 Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата публикации',
        help_text='Можно установить дату публикации в будущем'
    )

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published', '-published_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """💾 Автоматическая генерация slug с .html в конце"""
        if not self.slug:
            # Генерируем slug из заголовка
            base_slug = slugify(self.title)
            # Убираем .html если он уже есть, чтобы не дублировать
            if base_slug.endswith('.html'):
                base_slug = base_slug[:-5]
            # Добавляем .html в конец
            self.slug = f"{base_slug}.html"

            # Проверяем уникальность
            counter = 1
            while Article.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}.html"
                counter += 1

        # Устанавливаем дату публикации, если не задана
        if self.is_published and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """🔗 Получить URL статьи"""
        return reverse('blog:article_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """👁️ Увеличить счетчик просмотров"""
        self.views += 1
        self.save(update_fields=['views'])

    def get_related_articles(self, limit=4):
        """🔗 Получить похожие статьи из той же категории"""
        return Article.objects.filter(
            category=self.category,
            is_published=True
        ).exclude(
            id=self.id
        ).order_by('-published_at')[:limit]

    def get_next_article(self):
        """➡️ Следующая статья"""
        return Article.objects.filter(
            is_published=True,
            published_at__gt=self.published_at
        ).order_by('published_at').first()

    def get_previous_article(self):
        """⬅️ Предыдущая статья"""
        return Article.objects.filter(
            is_published=True,
            published_at__lt=self.published_at
        ).order_by('-published_at').first()

    @property
    def reading_time(self):
        """⏱️ Примерное время чтения (слов в минуту: 200)"""
        from django.utils.html import strip_tags
        word_count = len(strip_tags(self.content).split())
        minutes = word_count // 200
        return max(1, minutes)  # Минимум 1 минута


# 🔧 ИЗМЕНЕНИЯ:
# ✅ ЗАМЕНЕНО: ckeditor.fields.RichTextField → django_ckeditor_5.fields.CKEditor5Field
# ✅ ДОБАВЛЕНО: config_name='basic' для excerpt (краткое описание)
# ✅ ДОБАВЛЕНО: config_name='blog' для content (полный текст)
# ✅ СОХРАНЕНО: Вся остальная функциональность модели Article без изменений
# ✅ УЛУЧШЕНО: Современный интерфейс CKEditor 5 с лучшей безопасностью