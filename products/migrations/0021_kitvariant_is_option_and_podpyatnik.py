from django.db import migrations, models


def create_podpyatnik_option(apps, schema_editor):
    """
    Создаем опцию "подпятник" в справочнике KitVariant
    """
    KitVariant = apps.get_model('products', 'KitVariant')

    # Проверяем, существует ли уже запись с кодом "podpyatnik"
    if not KitVariant.objects.filter(code='podpyatnik').exists():
        KitVariant.objects.create(
            name="Подпятник",
            code="podpyatnik",
            price_modifier=15.00,  # Цена в рублях
            order=100,  # Высокий порядок сортировки, чтобы отображалось после основных комплектаций
            is_option=True,  # Отмечаем как опцию
        )


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0020_merge_20250515_2230'),  # Изменена зависимость на существующую миграцию слияния
    ]

    operations = [
        # Добавляем поле is_option в модель KitVariant
        migrations.AddField(
            model_name='kitvariant',
            name='is_option',
            field=models.BooleanField(default=False, verbose_name='Дополнительная опция'),
        ),

        # Создаем запись подпятника
        migrations.RunPython(create_podpyatnik_option),
    ]