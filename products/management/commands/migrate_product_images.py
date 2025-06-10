# 📁 products/management/commands/migrate_product_images.py
# 🔄 Django команда для миграции существующих изображений товаров

import os
from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Product, ProductImage


class Command(BaseCommand):
    """
    🖼️ Команда для миграции существующих изображений товаров

    Устанавливает первое изображение каждого товара как главное (is_main=True)
    и создает заглушку placeholder-product.jpg если её нет

    Использование:
    python manage.py migrate_product_images
    """

    help = 'Мигрирует существующие изображения товаров, устанавливая главное изображение'

    def add_arguments(self, parser):
        """➕ Добавляем опции командной строки"""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет изменено, но не применять изменения',
        )

        parser.add_argument(
            '--create-placeholder',
            action='store_true',
            help='Создать файл-заглушку placeholder-product.jpg',
        )

    def handle(self, *args, **options):
        """🚀 Основная логика команды"""

        self.stdout.write(
            self.style.SUCCESS('🖼️ Начинаем миграцию изображений товаров...')
        )

        # 📊 Счетчики для статистики
        products_with_images = 0
        products_without_images = 0
        main_images_set = 0

        # 🔍 Получаем все товары с изображениями
        products_with_imgs = Product.objects.filter(
            product_images__isnull=False
        ).distinct()

        self.stdout.write(
            f"📦 Найдено товаров с изображениями: {products_with_imgs.count()}"
        )

        # 🔄 Обрабатываем каждый товар
        for product in products_with_imgs:
            images = product.product_images.all().order_by('created_at')

            if images.exists():
                products_with_images += 1

                # 🔍 Проверяем, есть ли уже главное изображение
                main_image = images.filter(is_main=True).first()

                if not main_image:
                    # 🎯 Устанавливаем первое изображение как главное
                    first_image = images.first()

                    if not options['dry_run']:
                        first_image.is_main = True
                        first_image.save()

                    main_images_set += 1

                    self.stdout.write(
                        f"✅ Товар '{product.product_name}': установлено главное изображение"
                    )
                else:
                    self.stdout.write(
                        f"ℹ️ Товар '{product.product_name}': главное изображение уже установлено"
                    )

        # 📊 Находим товары без изображений
        products_without_imgs = Product.objects.filter(
            product_images__isnull=True
        ).distinct()

        products_without_images = products_without_imgs.count()

        if products_without_images > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Товаров без изображений: {products_without_images}"
                )
            )

            # 📝 Показываем несколько примеров
            examples = products_without_imgs[:5]
            for product in examples:
                self.stdout.write(f"   - {product.product_name}")

            if products_without_images > 5:
                self.stdout.write(f"   ... и еще {products_without_images - 5}")

        # 🎨 Создание заглушки
        if options['create_placeholder']:
            self.create_placeholder_image()

        # 📊 Итоговая статистика
        self.stdout.write(
            self.style.SUCCESS('\n📊 СТАТИСТИКА МИГРАЦИИ:')
        )
        self.stdout.write(f"   📦 Товаров с изображениями: {products_with_images}")
        self.stdout.write(f"   🖼️ Главных изображений установлено: {main_images_set}")
        self.stdout.write(f"   ⚠️ Товаров без изображений: {products_without_images}")

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('🔍 Режим предпросмотра - изменения НЕ применены')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Миграция завершена успешно!')
            )

    def create_placeholder_image(self):
        """🎨 Создает файл-заглушку для товаров без изображений"""

        placeholder_path = os.path.join(
            settings.MEDIA_ROOT,
            'images',
            'placeholder-product.jpg'
        )

        # 📁 Создаем директорию если не существует
        os.makedirs(os.path.dirname(placeholder_path), exist_ok=True)

        if os.path.exists(placeholder_path):
            self.stdout.write("ℹ️ Заглушка placeholder-product.jpg уже существует")
            return

        # 🎨 Создаем простую заглушку (может потребоваться PIL)
        try:
            from PIL import Image, ImageDraw, ImageFont

            # 📐 Создаем изображение 400x300 пикселей
            img = Image.new('RGB', (400, 300), color='#f8f9fa')
            draw = ImageDraw.Draw(img)

            # 📝 Добавляем текст
            try:
                # Пытаемся использовать системный шрифт
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                # Используем стандартный шрифт
                font = ImageFont.load_default()

            text = "Изображение\nне загружено"

            # 🎯 Центрируем текст
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (400 - text_width) // 2
            y = (300 - text_height) // 2

            draw.text((x, y), text, fill='#6c757d', font=font, align='center')

            # 💾 Сохраняем файл
            img.save(placeholder_path, 'JPEG', quality=85)

            self.stdout.write(
                self.style.SUCCESS(f"✅ Создана заглушка: {placeholder_path}")
            )

        except ImportError:
            # 📝 Если PIL недоступен, создаем простой файл-маркер
            with open(placeholder_path, 'w') as f:
                f.write("# Placeholder file - replace with actual image")

            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ PIL недоступен. Создан файл-маркер: {placeholder_path}\n"
                    f"   Замените его на настоящее изображение-заглушку"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Ошибка создания заглушки: {e}")
            )

    def validate_images(self):
        """🔍 Дополнительная валидация корректности изображений"""

        # 🔍 Проверяем товары с несколькими главными изображениями
        products_with_multiple_main = []

        for product in Product.objects.all():
            main_images_count = product.product_images.filter(is_main=True).count()
            if main_images_count > 1:
                products_with_multiple_main.append(product)

        if products_with_multiple_main:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Обнаружены товары с несколькими главными изображениями: {len(products_with_multiple_main)}"
                )
            )

            for product in products_with_multiple_main[:3]:
                self.stdout.write(f"   - {product.product_name}")
        else:
            self.stdout.write("✅ Все товары имеют корректные главные изображения")

# 🔧 ИСПОЛЬЗОВАНИЕ КОМАНДЫ:
#
# 1. Предпросмотр изменений:
#    python manage.py migrate_product_images --dry-run
#
# 2. Применить миграцию:
#    python manage.py migrate_product_images
#
# 3. Создать заглушку + миграция:
#    python manage.py migrate_product_images --create-placeholder
#
# 4. Только создать заглушку:
#    python manage.py migrate_product_images --create-placeholder --dry-run