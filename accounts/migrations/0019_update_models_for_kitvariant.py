# Generated manually on 2025-05-15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0018_remove_cartitem_configuration_type_and_more'),
        ('products', '0019_rename_sizevariant_to_kitvariant'),  # Замените xxxx на номер миграции, созданной выше
    ]

    operations = [
        # 1. Добавляем поле kit_variant в CartItem
        migrations.AddField(
            model_name='cartitem',
            name='kit_variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='products.kitvariant'),
        ),

        # 2. Добавляем поле kit_variant в OrderItem
        migrations.AddField(
            model_name='orderitem',
            name='kit_variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='products.kitvariant'),
        ),
    ]