# Миграция для добавления полей color в CartItem и OrderItem
# Generated manually on 2025-05-12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_orderitem_product_price_alter_orderitem_order'),
        ('products', '0016_create_color_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='carpet_color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cart_items_carpet', to='products.color'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='border_color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cart_items_border', to='products.color'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='has_podpyatnik',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='carpet_color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_items_carpet', to='products.color'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='border_color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_items_border', to='products.color'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='has_podpyatnik',
            field=models.BooleanField(default=False),
        ),
    ]