# 📁 blog/migrations/0001_initial.py
# 📊 Первоначальная миграция для создания таблиц блога

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleCategory',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100, verbose_name='Название категории')),
                ('slug', models.SlugField(blank=True, null=True, unique=True, verbose_name='URL-адрес')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание категории')),
                ('image', models.ImageField(blank=True, null=True, upload_to='blog/categories/', verbose_name='Изображение категории')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')),
            ],
            options={
                'verbose_name': 'Категория статей',
                'verbose_name_plural': 'Категории статей',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок статьи')),
                ('slug', models.SlugField(blank=True, null=True, unique=True, verbose_name='URL-адрес')),
                ('main_image', models.ImageField(upload_to='blog/articles/', verbose_name='Главное изображение')),
                ('short_description', models.TextField(verbose_name='Краткое описание')),
                ('content', models.TextField(verbose_name='Содержание статьи')),
                ('is_active', models.BooleanField(default=True, verbose_name='Опубликована')),
                ('is_featured', models.BooleanField(default=False, verbose_name='Рекомендуемая')),
                ('meta_title', models.CharField(blank=True, help_text='Если не указан, используется обычный заголовок', max_length=60, null=True, verbose_name='SEO заголовок')),
                ('meta_description', models.CharField(blank=True, help_text='Краткое описание для поисковых систем', max_length=160, null=True, verbose_name='SEO описание')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='blog.articlecategory', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Статья',
                'verbose_name_plural': 'Статьи',
                'ordering': ['-created_at'],
            },
        ),
    ]