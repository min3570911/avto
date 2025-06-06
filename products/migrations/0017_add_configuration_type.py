# Generated by Django 5.1.4 on 2025-05-14 18:06

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_create_color_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigurationType',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100, verbose_name='Название комплектации')),
                ('code', models.CharField(max_length=30, unique=True, verbose_name='Символьный код')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок сортировки')),
                ('image', models.ImageField(blank=True, null=True, upload_to='configurations', verbose_name='Изображение схемы')),
                ('price_modifier', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Модификатор цены')),
            ],
            options={
                'verbose_name': 'Тип комплектации',
                'verbose_name_plural': 'Типы комплектации',
                'ordering': ['order'],
            },
        ),
    ]
