# Generated by Django 5.1.4 on 2025-06-09 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0029_alter_category_additional_content'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productimage',
            options={'ordering': ['-is_main', 'created_at'], 'verbose_name': 'Изображение товара', 'verbose_name_plural': 'Изображения товаров'},
        ),
        migrations.AddField(
            model_name='product',
            name='meta_description',
            field=models.TextField(blank=True, help_text='SEO описание для поисковых систем', null=True, verbose_name='Meta Description'),
        ),
        migrations.AddField(
            model_name='product',
            name='page_title',
            field=models.CharField(blank=True, help_text='SEO заголовок для страницы товара', max_length=200, null=True, verbose_name='Заголовок страницы (Title)'),
        ),
        migrations.AddField(
            model_name='product',
            name='product_sku',
            field=models.CharField(blank=True, help_text='Уникальный код товара для импорта и учета', max_length=50, null=True, unique=True, verbose_name='Артикул товара'),
        ),
        migrations.AddField(
            model_name='productimage',
            name='is_main',
            field=models.BooleanField(default=False, help_text='Отображается в каталоге и как основное в карточке товара', verbose_name='Главное изображение'),
        ),
    ]
