# 📁 boats/migrations/0004_add_missing_short_description.py
# 🔧 Принудительное добавление отсутствующего поля short_description
# ✅ ИСПРАВЛЯЕТ: no such column: boats_boatproduct.short_description

from django.db import migrations, models


class Migration(migrations.Migration):
    """🔧 Добавление отсутствующего поля short_description в таблицу boats_boatproduct"""

    dependencies = [
        ('boats', '0003_auto_20250809_0841'),
    ]

    operations = [
        # 🆕 Принудительно добавляем поле short_description
        migrations.AddField(
            model_name='boatproduct',
            name='short_description',
            field=models.TextField(
                blank=True,
                help_text='Краткое описание для отображения в каталоге (до 500 символов)',
                max_length=500,
                verbose_name='Краткое описание',
                default=''  # 🔧 Значение по умолчанию для существующих записей
            ),
        ),
    ]