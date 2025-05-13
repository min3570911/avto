# Миграция для создания модели Color
# Generated manually on 2025-05-12

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_productreview_dislikes_productreview_likes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Color',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=50, verbose_name='Название цвета')),
                ('hex_code', models.CharField(max_length=7, verbose_name='HEX-код')),
                ('display_order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок отображения')),
            ],
            options={
                'verbose_name': 'Цвет',
                'verbose_name_plural': 'Цвета',
                'abstract': False,
            },
        ),
    ]