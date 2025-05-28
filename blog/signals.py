# 📁 blog/signals.py
# 🔔 Сигналы для автоматизации процессов в блоге

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from .models import Article


@receiver(pre_save, sender=Article)
def auto_slug_and_publish_date(sender, instance, **kwargs):
    """
    🔧 Автоматическая генерация slug и установка даты публикации

    Args:
        sender: Класс модели (Article)
        instance: Экземпляр статьи
        **kwargs: Дополнительные аргументы
    """

    # 🔗 Генерация slug если он пустой
    if not instance.slug:
        base_slug = slugify(instance.title)
        # Убираем .html если он уже есть
        if base_slug.endswith('.html'):
            base_slug = base_slug[:-5]

        # Добавляем .html
        instance.slug = f"{base_slug}.html"

        # 🔍 Проверка уникальности
        counter = 1
        original_slug = instance.slug
        while Article.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{base_slug}-{counter}.html"
            counter += 1

    # 📅 Установка даты публикации
    if instance.is_published and not instance.published_at:
        instance.published_at = timezone.now()