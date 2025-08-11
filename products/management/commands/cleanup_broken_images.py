# 📁 products/management/commands/cleanup_broken_images.py
# 🧹 Django команда для удаления битых неглавных изображений из базы данных
# ✅ ИСПРАВЛЕНО: Добавлена безопасность и подробная статистика

import os
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from products.models import ProductImage, Category
from common.models import Color
from django.utils import timezone


class Command(BaseCommand):
    """
    🧹 Команда для поиска и удаления битых неглавных изображений

    Проверяет существование файлов на диске и удаляет записи из БД,
    которые ссылаются на несуществующие файлы.

    Использование:
    python manage.py cleanup_broken_images
    python manage.py cleanup_broken_images --dry-run  # 👁️ Только показать результат
    python manage.py cleanup_broken_images --check-all  # 🔍 Проверить все типы изображений
    python manage.py cleanup_broken_images --verbose  # 📝 Подробный вывод
    """

    help = '🧹 Удаляет записи битых неглавных изображений из базы данных'

    def __init__(self):
        super().__init__()
        # 📊 Счетчики для статистики
        self.stats = {
            'total_checked': 0,
            'broken_found': 0,
            'deleted': 0,
            'main_images_found': 0,
            'main_images_broken': 0,
            'categories_checked': 0,
            'categories_broken': 0,
            'colors_checked': 0,
            'colors_broken': 0,
        }

        # 📝 Настройка логирования
        self.logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        """➕ Добавляем опции командной строки"""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='👁️ Только показать что будет удалено, не удалять записи',
        )

        parser.add_argument(
            '--check-all',
            action='store_true',
            help='🔍 Проверить все типы изображений (товары, категории, цвета)',
        )

        parser.add_argument(
            '--verbose',
            action='store_true',
            help='📝 Подробный вывод процесса',
        )

        parser.add_argument(
            '--include-main',
            action='store_true',
            help='⚠️ ОПАСНО: Включить проверку главных изображений товаров',
        )

    def handle(self, *args, **options):
        """🚀 Основная логика команды"""

        # 🎯 Настройки из аргументов
        dry_run = options['dry_run']
        check_all = options['check_all']
        verbose = options['verbose']
        include_main = options['include_main']

        # 🛡️ Предупреждение о главных изображениях
        if include_main:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️ ВНИМАНИЕ: Включена проверка главных изображений товаров!'
                )
            )

        # 🧹 Стартовое сообщение
        mode_text = "ТЕСТОВЫЙ РЕЖИМ" if dry_run else "АКТИВНЫЙ РЕЖИМ"
        self.stdout.write(
            self.style.SUCCESS(
                f'🧹 Начинаем очистку битых изображений ({mode_text})...'
            )
        )

        # 📋 Проверяем MEDIA_ROOT
        if not os.path.exists(settings.MEDIA_ROOT):
            raise CommandError(f'❌ MEDIA_ROOT не существует: {settings.MEDIA_ROOT}')

        # 🔍 Основная очистка неглавных изображений товаров
        self._cleanup_product_images(dry_run, verbose, include_main)

        # 🔍 Дополнительная очистка других изображений (если запрошено)
        if check_all:
            self._cleanup_category_images(dry_run, verbose)
            self._cleanup_color_images(dry_run, verbose)

        # 📊 Финальная статистика
        self._print_final_statistics(dry_run)

    def _cleanup_product_images(self, dry_run: bool, verbose: bool, include_main: bool):
        """🖼️ Очистка изображений товаров"""

        self.stdout.write('\n🖼️ Проверяем изображения товаров...')

        # 🔍 Получаем неглавные изображения (или все, если include_main=True)
        if include_main:
            images_queryset = ProductImage.objects.all()
            self.stdout.write('⚠️ Проверяем ВСЕ изображения товаров (включая главные)')
        else:
            images_queryset = ProductImage.objects.filter(is_main=False)
            self.stdout.write('✅ Проверяем только неглавные изображения товаров')

        # 📊 Получаем количество для прогресса
        total_images = images_queryset.count()
        self.stdout.write(f'📊 Найдено изображений для проверки: {total_images}')

        if total_images == 0:
            self.stdout.write('ℹ️ Нет изображений для проверки')
            return

        # 🔍 Проверяем каждое изображение
        broken_images = []

        for i, image in enumerate(images_queryset.iterator(), 1):
            self.stats['total_checked'] += 1

            # 📊 Прогресс каждые 10 изображений
            if verbose and i % 10 == 0:
                self.stdout.write(f'📊 Проверено: {i}/{total_images}')

            # 🔍 Проверяем существование файла
            is_broken = self._check_image_file(image, verbose)

            if is_broken:
                broken_images.append(image)
                self.stats['broken_found'] += 1

                # 📝 Отмечаем главные битые изображения отдельно
                if image.is_main:
                    self.stats['main_images_broken'] += 1

                if verbose:
                    main_indicator = "🌟 ГЛАВНОЕ" if image.is_main else "📷 обычное"
                    self.stdout.write(
                        f'❌ Битое изображение: {image.product.product_name} '
                        f'({main_indicator}) - {image.image.name}'
                    )

        # 💾 Удаляем битые изображения (если не dry-run)
        if broken_images:
            self.stdout.write(f'\n❌ Найдено битых изображений: {len(broken_images)}')

            if not dry_run:
                self._delete_broken_images(broken_images)
            else:
                self.stdout.write('👁️ ТЕСТОВЫЙ РЕЖИМ: изображения НЕ удалены')
        else:
            self.stdout.write('✅ Битых изображений не найдено!')

    def _cleanup_category_images(self, dry_run: bool, verbose: bool):
        """📂 Очистка изображений категорий"""

        self.stdout.write('\n📂 Проверяем изображения категорий...')

        categories = Category.objects.exclude(category_image='')
        broken_categories = []

        for category in categories:
            self.stats['categories_checked'] += 1

            if self._check_category_image_file(category, verbose):
                broken_categories.append(category)
                self.stats['categories_broken'] += 1

                if verbose:
                    self.stdout.write(
                        f'❌ Битое изображение категории: {category.category_name} '
                        f'- {category.category_image.name}'
                    )

        # 💾 Очищаем битые изображения категорий
        if broken_categories:
            self.stdout.write(f'❌ Найдено категорий с битыми изображениями: {len(broken_categories)}')

            if not dry_run:
                for category in broken_categories:
                    category.category_image = None
                    category.save(update_fields=['category_image'])
                    self.stats['deleted'] += 1

                self.stdout.write('✅ Очищены ссылки на битые изображения категорий')
            else:
                self.stdout.write('👁️ ТЕСТОВЫЙ РЕЖИМ: ссылки НЕ очищены')
        else:
            self.stdout.write('✅ Битых изображений категорий не найдено!')

    def _cleanup_color_images(self, dry_run: bool, verbose: bool):
        """🎨 Очистка изображений цветов"""

        self.stdout.write('\n🎨 Проверяем изображения цветов...')

        colors = Color.objects.all()
        broken_colors = []

        for color in colors:
            self.stats['colors_checked'] += 1
            broken_fields = []

            # 🔍 Проверяем carpet_image
            if color.carpet_image and not self._file_exists(color.carpet_image.path):
                broken_fields.append('carpet_image')

            # 🔍 Проверяем border_image
            if color.border_image and not self._file_exists(color.border_image.path):
                broken_fields.append('border_image')

            if broken_fields:
                broken_colors.append((color, broken_fields))
                self.stats['colors_broken'] += 1

                if verbose:
                    fields_text = ', '.join(broken_fields)
                    self.stdout.write(
                        f'❌ Битые изображения цвета: {color.name} '
                        f'- поля: {fields_text}'
                    )

        # 💾 Очищаем битые изображения цветов
        if broken_colors:
            self.stdout.write(f'❌ Найдено цветов с битыми изображениями: {len(broken_colors)}')

            if not dry_run:
                for color, broken_fields in broken_colors:
                    update_fields = []

                    if 'carpet_image' in broken_fields:
                        color.carpet_image = None
                        update_fields.append('carpet_image')

                    if 'border_image' in broken_fields:
                        color.border_image = None
                        update_fields.append('border_image')

                    color.save(update_fields=update_fields)
                    self.stats['deleted'] += 1

                self.stdout.write('✅ Очищены ссылки на битые изображения цветов')
            else:
                self.stdout.write('👁️ ТЕСТОВЫЙ РЕЖИМ: ссылки НЕ очищены')
        else:
            self.stdout.write('✅ Битых изображений цветов не найдено!')

    def _check_image_file(self, image: ProductImage, verbose: bool) -> bool:
        """🔍 Проверяет существование файла изображения товара"""

        # 🛡️ Проверяем, что поле image не пустое
        if not image.image:
            if verbose:
                self.stdout.write(f'⚠️ Пустое поле image: {image.product.product_name}')
            return True

        # 🛡️ Проверяем, что image.name не пустое
        if not image.image.name:
            if verbose:
                self.stdout.write(f'⚠️ Пустое имя файла: {image.product.product_name}')
            return True

        # 🔍 Проверяем существование файла
        return not self._file_exists(image.image.path)

    def _check_category_image_file(self, category: Category, verbose: bool) -> bool:
        """🔍 Проверяет существование файла изображения категории"""

        if not category.category_image or not category.category_image.name:
            return False

        return not self._file_exists(category.category_image.path)

    def _file_exists(self, file_path: str) -> bool:
        """📁 Безопасная проверка существования файла"""

        try:
            return os.path.exists(file_path) and os.path.isfile(file_path)
        except (OSError, TypeError, ValueError) as e:
            # 📝 Логируем ошибки доступа к файловой системе
            self.logger.warning(f'⚠️ Ошибка проверки файла {file_path}: {e}')
            return False

    @transaction.atomic
    def _delete_broken_images(self, broken_images: list):
        """💾 Безопасно удаляет битые изображения из БД"""

        try:
            self.stdout.write(f'💾 Удаляем {len(broken_images)} битых изображений...')

            # 🛡️ Используем транзакцию для безопасности
            deleted_count = 0

            for image in broken_images:
                try:
                    # 📝 Логируем что удаляем
                    self.logger.info(
                        f'Удаляем битое изображение: {image.product.product_name} '
                        f'- {image.image.name}'
                    )

                    image.delete()
                    deleted_count += 1

                except Exception as e:
                    self.logger.error(
                        f'❌ Ошибка удаления изображения {image.id}: {e}'
                    )

            self.stats['deleted'] = deleted_count
            self.stdout.write(f'✅ Удалено записей: {deleted_count}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Критическая ошибка удаления: {e}')
            )
            raise CommandError(f'Не удалось удалить битые изображения: {e}')

    def _print_final_statistics(self, dry_run: bool):
        """📊 Выводит финальную статистику работы"""

        mode_text = "ТЕСТОВЫЙ РЕЖИМ" if dry_run else "ВЫПОЛНЕНО"

        self.stdout.write(f'\n📊 === ИТОГОВАЯ СТАТИСТИКА ({mode_text}) ===')
        self.stdout.write(f'🔍 Всего проверено изображений: {self.stats["total_checked"]}')
        self.stdout.write(f'❌ Найдено битых изображений: {self.stats["broken_found"]}')

        if self.stats['main_images_broken'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ В том числе главных изображений: {self.stats["main_images_broken"]}'
                )
            )

        # 📊 Статистика по категориям и цветам
        if self.stats['categories_checked'] > 0:
            self.stdout.write(f'📂 Проверено категорий: {self.stats["categories_checked"]}')
            self.stdout.write(f'❌ Битых изображений категорий: {self.stats["categories_broken"]}')

        if self.stats['colors_checked'] > 0:
            self.stdout.write(f'🎨 Проверено цветов: {self.stats["colors_checked"]}')
            self.stdout.write(f'❌ Битых изображений цветов: {self.stats["colors_broken"]}')

        if not dry_run:
            self.stdout.write(f'💾 Удалено записей из БД: {self.stats["deleted"]}')

        # 🎯 Финальное сообщение
        if self.stats['broken_found'] == 0:
            self.stdout.write(
                self.style.SUCCESS('🎉 Поздравляем! Битых изображений не найдено!')
            )
        elif dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'👁️ ТЕСТОВЫЙ РЕЖИМ: Найдено {self.stats["broken_found"]} битых изображений. '
                    'Запустите без --dry-run для удаления.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Очистка завершена! Удалено {self.stats["deleted"]} битых записей.'
                )
            )

        # ⚠️ Предупреждение о главных изображениях
        if self.stats['main_images_broken'] > 0:
            self.stdout.write(
                self.style.ERROR(
                    '\n⚠️ ВНИМАНИЕ: Найдены битые ГЛАВНЫЕ изображения товаров!\n'
                    'Рекомендуется загрузить новые изображения для этих товаров.\n'
                    'Используйте команду: python manage.py migrate_product_images'
                )
            )

        # 📝 Дополнительные рекомендации
        self.stdout.write(
            '\n💡 РЕКОМЕНДАЦИИ:\n'
            '1. Регулярно запускайте эту команду для поддержания чистоты БД\n'
            '2. Используйте --dry-run перед реальным удалением\n'
            '3. Делайте бэкап БД перед массовыми операциями\n'
            '4. Проверяйте логи на наличие ошибок доступа к файлам'
        )

        # ⏰ Время выполнения
        self.stdout.write(f'\n⏰ Время завершения: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')

# 🔧 ИСПОЛЬЗОВАНИЕ КОМАНДЫ:
#
# 1. 👁️ ТЕСТОВЫЙ РЕЖИМ (только показать):
#    python manage.py cleanup_broken_images --dry-run
#
# 2. ✅ УДАЛЕНИЕ ТОЛЬКО НЕГЛАВНЫХ ИЗОБРАЖЕНИЙ:
#    python manage.py cleanup_broken_images
#
# 3. 🔍 ПРОВЕРКА ВСЕХ ТИПОВ ИЗОБРАЖЕНИЙ:
#    python manage.py cleanup_broken_images --check-all
#
# 4. 📝 ПОДРОБНЫЙ ВЫВОД:
#    python manage.py cleanup_broken_images --verbose
#
# 5. ⚠️ ВКЛЮЧИТЬ ГЛАВНЫЕ ИЗОБРАЖЕНИЯ (ОСТОРОЖНО!):
#    python manage.py cleanup_broken_images --include-main --dry-run
#
# 6. 🎯 ПОЛНАЯ ОЧИСТКА:
#    python manage.py cleanup_broken_images --check-all --verbose
#
# 🛡️ БЕЗОПАСНОСТЬ:
# - Используется транзакция для атомарности операций
# - Подробное логирование всех действий
# - Тестовый режим для проверки перед удалением
# - Отдельная обработка главных изображений
# - Проверка существования MEDIA_ROOT
# - Обработка ошибок файловой системы