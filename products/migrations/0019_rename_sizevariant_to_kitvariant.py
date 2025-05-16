# Generated manually on 2025-05-15

from django.db import migrations, models
import uuid


def create_default_kit_variants(apps, schema_editor):
    """
    Создаем стандартные комплектации ковриков
    """
    KitVariant = apps.get_model('products', 'KitVariant')

    # Создаем комплектации с уникальными UUID
    KitVariant.objects.create(
        uid=uuid.uuid4(),
        name="Салон",
        code="salon",
        price_modifier=100.00,
        order=1,
        created_at="2025-05-15T00:00:00Z",
        updated_at="2025-05-15T00:00:00Z"
    )

    KitVariant.objects.create(
        uid=uuid.uuid4(),
        name="Багажник",
        code="trunk",
        price_modifier=50.00,
        order=2,
        created_at="2025-05-15T00:00:00Z",
        updated_at="2025-05-15T00:00:00Z"
    )

    KitVariant.objects.create(
        uid=uuid.uuid4(),
        name="Салон и багажник",
        code="salon_trunk",
        price_modifier=100.00,
        order=3,
        created_at="2025-05-15T00:00:00Z",
        updated_at="2025-05-15T00:00:00Z"
    )

    KitVariant.objects.create(
        uid=uuid.uuid4(),
        name="Только водительский",
        code="driver_only",
        price_modifier=50.00,
        order=4,
        created_at="2025-05-15T00:00:00Z",
        updated_at="2025-05-15T00:00:00Z"
    )

    KitVariant.objects.create(
        uid=uuid.uuid4(),
        name="Только два передних",
        code="front_only",
        price_modifier=30.00,
        order=5,
        created_at="2025-05-15T00:00:00Z",
        updated_at="2025-05-15T00:00:00Z"
    )


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0015_productreview_dislikes_productreview_likes'),
    ]

    operations = [
        # 1. Создаем новую модель KitVariant
        migrations.CreateModel(
            name='KitVariant',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100, verbose_name='Название комплектации')),
                ('code', models.CharField(max_length=50, verbose_name='Символьный код')),
                ('price_modifier',
                 models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Модификатор цены')),
                ('order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('image', models.ImageField(blank=True, null=True, upload_to='configurations',
                                            verbose_name='Изображение схемы')),
            ],
            options={
                'verbose_name': 'Тип комплектации',
                'verbose_name_plural': 'Типы комплектаций',
                'abstract': False,
            },
        ),

        # 2. Добавляем поле kit_variant в модель Product
        migrations.AddField(
            model_name='product',
            name='kit_variant',
            field=models.ManyToManyField(blank=True, to='products.kitvariant'),
        ),

        # 3. Запускаем функцию создания стандартных комплектаций
        migrations.RunPython(create_default_kit_variants),

        # 4. Добавляем kit_variant в Wishlist
        migrations.AddField(
            model_name='wishlist',
            name='kit_variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    related_name='wishlist_items', to='products.kitvariant'),
        ),

        # 5. Обновляем unique_together для Wishlist
        migrations.AlterUniqueTogether(
            name='wishlist',
            unique_together={('user', 'product', 'kit_variant')},
        ),
    ]