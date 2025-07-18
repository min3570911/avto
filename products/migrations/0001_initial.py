# Generated by Django 5.1.4 on 2025-07-19 06:59

import django.db.models.deletion
import django_ckeditor_5.fields
import products.storage
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
            name='Category',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('category_name', models.CharField(help_text='Основное название категории для отображения', max_length=100, verbose_name='Название категории')),
                ('slug', models.SlugField(blank=True, help_text='Автоматически генерируется из названия', null=True, unique=True, verbose_name='URL-адрес')),
                ('category_image', models.ImageField(help_text='Рекомендуемый размер: 800x400 px. Файл сохранится с точным именем', storage=products.storage.OverwriteStorage(), upload_to='categories', verbose_name='Изображение категории')),
                ('category_sku', models.PositiveIntegerField(blank=True, help_text='Уникальный номер для внутреннего учета', null=True, unique=True, verbose_name='Артикул категории')),
                ('display_order', models.PositiveIntegerField(default=0, help_text='Чем меньше число, тем выше в списке (0 = сверху)', verbose_name='Порядок отображения')),
                ('is_active', models.BooleanField(default=True, help_text='Отображать категорию на сайте', verbose_name='Активна')),
                ('description', django_ckeditor_5.fields.CKEditor5Field(blank=True, help_text='Основное описание категории с форматированием', null=True, verbose_name='Описание категории')),
                ('additional_content', models.TextField(blank=True, help_text='Вставьте ссылку на YouTube видео или готовый HTML-код. YouTube ссылки автоматически преобразуются в плеер', null=True, verbose_name='Дополнительный контент')),
                ('page_title', models.CharField(blank=True, help_text='Основной заголовок на странице категории (до 70 символов)', max_length=70, null=True, verbose_name='Заголовок страницы (H1)')),
                ('meta_title', models.CharField(blank=True, help_text='Заголовок для поисковых систем (до 60 символов)', max_length=60, null=True, verbose_name='Meta Title')),
                ('meta_description', models.TextField(blank=True, help_text='Описание для поисковых систем (до 160 символов)', max_length=160, null=True, verbose_name='Meta Description')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
                'ordering': ['display_order', 'category_name'],
            },
        ),
        migrations.CreateModel(
            name='Color',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=50, verbose_name='Название цвета')),
                ('hex_code', models.CharField(max_length=7, verbose_name='HEX-код')),
                ('display_order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок отображения')),
                ('color_type', models.CharField(choices=[('carpet', 'Коврик'), ('border', 'Окантовка')], default='carpet', max_length=10, verbose_name='Тип применения')),
                ('carpet_image', models.ImageField(blank=True, null=True, upload_to='colors/carpet', verbose_name='Изображение для коврика')),
                ('border_image', models.ImageField(blank=True, null=True, upload_to='colors/border', verbose_name='Изображение для окантовки')),
                ('is_available', models.BooleanField(default=True, verbose_name='Доступен для заказа')),
            ],
            options={
                'verbose_name': 'Цвет',
                'verbose_name_plural': 'Цвета',
                'ordering': ['color_type', 'display_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('coupon_code', models.CharField(max_length=10, verbose_name='Код купона')),
                ('is_expired', models.BooleanField(default=False, verbose_name='Истёк')),
                ('discount_amount', models.IntegerField(default=100, verbose_name='Сумма скидки')),
                ('minimum_amount', models.IntegerField(default=500, verbose_name='Минимальная сумма заказа')),
            ],
            options={
                'verbose_name': 'Купон',
                'verbose_name_plural': 'Купоны',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='KitVariant',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100, verbose_name='Название комплектации')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Символьный код')),
                ('price_modifier', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Модификатор цены')),
                ('order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('image', models.ImageField(blank=True, null=True, upload_to='configurations', verbose_name='Изображение схемы')),
                ('is_option', models.BooleanField(default=False, verbose_name='Дополнительная опция')),
            ],
            options={
                'verbose_name': 'Тип комплектации',
                'verbose_name_plural': 'Типы комплектаций',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('product_name', models.CharField(max_length=100, verbose_name='Название товара')),
                ('slug', models.SlugField(blank=True, null=True, unique=True, verbose_name='URL-адрес')),
                ('price', models.IntegerField(blank=True, default=0, null=True, verbose_name='Базовая цена')),
                ('product_desription', django_ckeditor_5.fields.CKEditor5Field(help_text='Подробное описание товара с возможностью форматирования', verbose_name='Описание товара')),
                ('newest_product', models.BooleanField(default=False, verbose_name='Новый товар')),
                ('product_sku', models.CharField(blank=True, help_text='Уникальный код товара для импорта и учета', max_length=50, null=True, unique=True, verbose_name='Артикул товара')),
                ('page_title', models.CharField(blank=True, help_text='SEO заголовок для страницы товара', max_length=200, null=True, verbose_name='Заголовок страницы (Title)')),
                ('meta_description', models.TextField(blank=True, help_text='SEO описание для поисковых систем', null=True, verbose_name='Meta Description')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='products.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Товары',
                'ordering': ['-created_at', 'product_name'],
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('image', models.ImageField(help_text='Файл сохранится с точным именем без хеш-суффиксов', storage=products.storage.OverwriteStorage(), upload_to='product', verbose_name='Изображение')),
                ('is_main', models.BooleanField(default=False, help_text='Отображается в каталоге и как основное в карточке товара', verbose_name='Главное изображение')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_images', to='products.product', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Изображение товара',
                'verbose_name_plural': 'Изображения товаров',
                'ordering': ['-is_main', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('stars', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=3, verbose_name='Оценка')),
                ('content', models.TextField(blank=True, null=True, verbose_name='Содержание отзыва')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
                ('dislikes', models.ManyToManyField(blank=True, related_name='disliked_reviews', to=settings.AUTH_USER_MODEL, verbose_name='Дизлайки')),
                ('likes', models.ManyToManyField(blank=True, related_name='liked_reviews', to=settings.AUTH_USER_MODEL, verbose_name='Лайки')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='products.product', verbose_name='Товар')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Отзыв',
                'verbose_name_plural': 'Отзывы',
                'ordering': ['-date_added'],
                'unique_together': {('user', 'product')},
            },
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('has_podpyatnik', models.BooleanField(default=False, verbose_name='С подпятником')),
                ('added_on', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('border_color', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wishlist_border_items', to='products.color', verbose_name='Цвет окантовки')),
                ('carpet_color', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wishlist_carpet_items', to='products.color', verbose_name='Цвет коврика')),
                ('kit_variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wishlist_items', to='products.kitvariant', verbose_name='Комплектация')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlisted_by', to='products.product', verbose_name='Товар')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Избранное',
                'verbose_name_plural': 'Избранное',
                'ordering': ['-added_on'],
                'unique_together': {('user', 'product', 'kit_variant')},
            },
        ),
    ]
