# 📁 products/migrations/0022_update_product_description_to_summernote.py
# 🔄 Миграция для изменения поля product_desription на SummernoteTextField

from django.db import migrations
import django_summernote.fields


class Migration(migrations.Migration):
    """
    🔄 Обновляем поле описания товара для использования Summernote

    ⚠️ ВАЖНО: Эта миграция не меняет тип поля в БД (остается TextField),
    только меняет его поведение в Django админке
    """

    dependencies = [
        ('products', '0026_alter_product_product_desription'),  # Последняя миграция
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_desription',
            field=django_summernote.fields.SummernoteTextField(
                help_text='Подробное описание товара с возможностью форматирования',
                verbose_name='Описание товара'
            ),
        ),
    ]