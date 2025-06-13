# 📁 products/image_utils.py
# 🆕 НОВЫЙ файл для обработки ZIP архивов с изображениями
# 🖼️ Автоматическое распределение изображений по папкам categories/ и product/

import os
import zipfile
import logging
from typing import Tuple, List, Dict
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from products.models import Category

logger = logging.getLogger(__name__)

# 🖼️ Поддерживаемые форматы изображений
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

# 📂 Системные файлы, которые нужно пропускать
SYSTEM_FILES_TO_SKIP = [
    '__MACOSX',
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini'
]


def process_images_zip(zip_file: InMemoryUploadedFile) -> int:
    """
    🖼️ Основная функция обработки ZIP архива с изображениями

    Распаковывает ZIP архив и автоматически распределяет изображения:
    - Категории → media/categories/
    - Товары → media/product/

    Args:
        zip_file: Загруженный ZIP файл

    Returns:
        int: Количество успешно обработанных изображений

    Raises:
        Exception: При ошибках обработки архива
    """
    try:
        logger.info(f"🔄 Начинаем обработку ZIP архива: {zip_file.name}")

        # 📊 Счетчики
        processed_count = 0
        categories_count = 0
        products_count = 0
        skipped_count = 0

        # 📂 Создаем необходимые директории
        _ensure_media_directories()

        # 🗂️ Получаем список существующих категорий для умного распределения
        existing_categories = _get_existing_categories()

        # 🗜️ Обрабатываем ZIP архив
        with zipfile.ZipFile(zip_file, 'r') as zip_archive:
            file_list = zip_archive.namelist()

            logger.info(f"📦 Файлов в архиве: {len(file_list)}")

            for filename in file_list:
                try:
                    # 🚫 Пропускаем системные файлы и папки
                    if _should_skip_file(filename):
                        logger.debug(f"⏭️ Пропуск системного файла: {filename}")
                        skipped_count += 1
                        continue

                    # 🖼️ Проверяем формат изображения
                    if not _is_supported_image(filename):
                        logger.warning(f"⚠️ Неподдерживаемый формат: {filename}")
                        skipped_count += 1
                        continue

                    # 📂 Определяем целевую папку
                    target_folder = _determine_target_folder(filename, existing_categories)

                    # 💾 Сохраняем файл
                    success = _save_image_file(zip_archive, filename, target_folder)

                    if success:
                        processed_count += 1
                        if target_folder == 'categories':
                            categories_count += 1
                        else:
                            products_count += 1

                        logger.info(f"✅ Сохранено: {filename} → {target_folder}/")
                    else:
                        skipped_count += 1

                except Exception as e:
                    logger.error(f"❌ Ошибка обработки файла {filename}: {e}")
                    skipped_count += 1
                    continue

        # 📊 Логируем итоговую статистику
        logger.info(
            f"📈 Обработка ZIP завершена: "
            f"обработано {processed_count}, "
            f"категорий {categories_count}, "
            f"товаров {products_count}, "
            f"пропущено {skipped_count}"
        )

        return processed_count

    except zipfile.BadZipFile:
        error_msg = "❌ Файл поврежден или не является ZIP архивом"
        logger.error(error_msg)
        raise Exception(error_msg)

    except Exception as e:
        error_msg = f"❌ Критическая ошибка при обработке ZIP архива: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def _ensure_media_directories():
    """📂 Создает необходимые директории для изображений"""
    try:
        categories_dir = os.path.join(settings.MEDIA_ROOT, 'categories')
        products_dir = os.path.join(settings.MEDIA_ROOT, 'product')

        os.makedirs(categories_dir, exist_ok=True)
        os.makedirs(products_dir, exist_ok=True)

        logger.debug(f"📂 Директории созданы: {categories_dir}, {products_dir}")

    except Exception as e:
        logger.error(f"❌ Ошибка создания директорий: {e}")
        raise


def _get_existing_categories() -> List[str]:
    """📂 Получает список названий существующих категорий"""
    try:
        # 🔍 Получаем названия всех категорий в верхнем регистре для сравнения
        categories = Category.objects.values_list('category_name', flat=True)
        category_names = [name.upper() for name in categories if name]

        logger.debug(f"📂 Найдено категорий: {len(category_names)}")
        return category_names

    except Exception as e:
        logger.error(f"❌ Ошибка получения категорий: {e}")
        return []


def _should_skip_file(filename: str) -> bool:
    """🚫 Проверяет, нужно ли пропустить файл"""

    # 📁 Пропускаем папки
    if filename.endswith('/'):
        return True

    # 🚫 Пропускаем системные файлы
    for system_file in SYSTEM_FILES_TO_SKIP:
        if system_file in filename:
            return True

    # 📄 Пропускаем скрытые файлы
    basename = os.path.basename(filename)
    if basename.startswith('.'):
        return True

    return False


def _is_supported_image(filename: str) -> bool:
    """🖼️ Проверяет, поддерживается ли формат изображения"""
    file_extension = os.path.splitext(filename)[1].lower()
    return file_extension in SUPPORTED_IMAGE_EXTENSIONS


def _determine_target_folder(filename: str, existing_categories: List[str]) -> str:
    """
    📂 Определяет целевую папку для изображения

    Логика:
    1. Извлекаем имя файла без расширения
    2. Проверяем, есть ли категория с таким названием
    3. Если есть → categories/, иначе → product/

    Args:
        filename: Имя файла в архиве
        existing_categories: Список существующих категорий

    Returns:
        str: 'categories' или 'product'
    """
    try:
        # 📄 Извлекаем базовое имя файла без расширения
        basename = os.path.basename(filename)
        name_without_ext = os.path.splitext(basename)[0].upper()

        # 🔍 Ищем точные совпадения с категориями
        if name_without_ext in existing_categories:
            logger.debug(f"📂 {filename} → categories (найдена категория {name_without_ext})")
            return 'categories'

        # 🔍 Ищем частичные совпадения (имя файла содержит название категории)
        for category in existing_categories:
            if category in name_without_ext or name_without_ext in category:
                logger.debug(f"📂 {filename} → categories (частичное совпадение с {category})")
                return 'categories'

        # 🛍️ По умолчанию - товары
        logger.debug(f"📦 {filename} → product (категория не найдена)")
        return 'product'

    except Exception as e:
        logger.warning(f"⚠️ Ошибка определения папки для {filename}: {e}. Используем product/")
        return 'product'


def _save_image_file(zip_archive: zipfile.ZipFile, filename: str, target_folder: str) -> bool:
    """
    💾 Сохраняет файл изображения в целевую папку

    Args:
        zip_archive: Открытый ZIP архив
        filename: Имя файла в архиве
        target_folder: Целевая папка ('categories' или 'product')

    Returns:
        bool: True если файл успешно сохранен
    """
    try:
        # 📂 Определяем путь для сохранения
        target_dir = os.path.join(settings.MEDIA_ROOT, target_folder)
        basename = os.path.basename(filename)
        target_path = os.path.join(target_dir, basename)

        # 📖 Читаем файл из архива
        with zip_archive.open(filename) as source_file:
            file_data = source_file.read()

        # 💾 Сохраняем файл (перезаписываем если существует)
        with open(target_path, 'wb') as target_file:
            target_file.write(file_data)

        # ✅ Проверяем что файл создался и не пустой
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            logger.debug(f"💾 Файл сохранен: {target_path}")
            return True
        else:
            logger.error(f"❌ Файл не создался или пустой: {target_path}")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка сохранения файла {filename}: {e}")
        return False


def get_images_statistics(zip_file: InMemoryUploadedFile) -> Dict:
    """
    📊 Получает статистику изображений в ZIP архиве без извлечения

    Используется для предпросмотра перед обработкой

    Args:
        zip_file: ZIP файл для анализа

    Returns:
        Dict: Статистика с количеством файлов по типам
    """
    try:
        stats = {
            'total_files': 0,
            'image_files': 0,
            'categories_files': 0,
            'products_files': 0,
            'unsupported_files': 0,
            'file_formats': {},
            'largest_file': {'name': '', 'size': 0},
            'errors': []
        }

        # 📂 Получаем список категорий
        existing_categories = _get_existing_categories()

        with zipfile.ZipFile(zip_file, 'r') as zip_archive:
            for filename in zip_archive.namelist():
                # 🚫 Пропускаем системные файлы
                if _should_skip_file(filename):
                    continue

                stats['total_files'] += 1

                # 🖼️ Проверяем формат
                if _is_supported_image(filename):
                    stats['image_files'] += 1

                    # 📂 Определяем тип
                    target_folder = _determine_target_folder(filename, existing_categories)
                    if target_folder == 'categories':
                        stats['categories_files'] += 1
                    else:
                        stats['products_files'] += 1

                    # 📊 Статистика форматов
                    ext = os.path.splitext(filename)[1].lower()
                    stats['file_formats'][ext] = stats['file_formats'].get(ext, 0) + 1

                    # 📏 Размер файла
                    try:
                        file_info = zip_archive.getinfo(filename)
                        if file_info.file_size > stats['largest_file']['size']:
                            stats['largest_file'] = {
                                'name': os.path.basename(filename),
                                'size': file_info.file_size
                            }
                    except:
                        pass

                else:
                    stats['unsupported_files'] += 1

        return stats

    except Exception as e:
        logger.error(f"❌ Ошибка анализа ZIP архива: {e}")
        return {
            'total_files': 0,
            'image_files': 0,
            'categories_files': 0,
            'products_files': 0,
            'unsupported_files': 0,
            'file_formats': {},
            'largest_file': {'name': '', 'size': 0},
            'errors': [str(e)]
        }


def validate_images_zip(zip_file: InMemoryUploadedFile) -> Tuple[bool, List[str]]:
    """
    ✅ Валидирует ZIP архив с изображениями

    Args:
        zip_file: ZIP файл для валидации

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []

    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_archive:
            file_list = zip_archive.namelist()

            # 📊 Базовые проверки
            if not file_list:
                errors.append("Архив пустой")
                return False, errors

            # 🖼️ Проверяем наличие изображений
            image_files = [f for f in file_list
                           if not _should_skip_file(f) and _is_supported_image(f)]

            if not image_files:
                errors.append("В архиве нет поддерживаемых изображений")
                return False, errors

            # 📏 Проверяем размеры файлов
            max_file_size = 5 * 1024 * 1024  # 5MB на файл
            for filename in image_files:
                try:
                    file_info = zip_archive.getinfo(filename)
                    if file_info.file_size > max_file_size:
                        errors.append(
                            f"Файл {os.path.basename(filename)} слишком большой: "
                            f"{file_info.file_size / 1024 / 1024:.1f}MB (макс. 5MB)"
                        )
                except:
                    pass

            # ✅ Если есть ошибки размеров - возвращаем их
            if errors:
                return False, errors

            return True, []

    except zipfile.BadZipFile:
        errors.append("Файл поврежден или не является ZIP архивом")
        return False, errors

    except Exception as e:
        errors.append(f"Ошибка валидации: {str(e)}")
        return False, errors


# 🎯 Дополнительные утилиты для будущего расширения

def cleanup_old_images(days_old: int = 30):
    """
    🧹 Очистка старых неиспользуемых изображений

    Args:
        days_old: Количество дней для определения "старых" файлов
    """
    # TODO: Реализовать очистку неиспользуемых изображений
    pass


def optimize_images(target_size: int = 800):
    """
    ⚡ Оптимизация изображений (сжатие, изменение размера)

    Args:
        target_size: Максимальная ширина в пикселях
    """
    # TODO: Реализовать оптимизацию изображений
    pass


def generate_thumbnails():
    """🖼️ Генерация миниатюр для всех изображений"""
    # TODO: Реализовать генерацию миниатюр
    pass

# 🔧 ВОЗМОЖНОСТИ ЭТОГО ФАЙЛА:
#
# ✅ ОСНОВНЫЕ ФУНКЦИИ:
# - process_images_zip() - главная функция обработки ZIP архива
# - _determine_target_folder() - умное распределение по папкам
# - _save_image_file() - сохранение файлов с перезаписью
#
# ✅ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ:
# - get_images_statistics() - анализ содержимого ZIP без распаковки
# - validate_images_zip() - валидация архива
# - _ensure_media_directories() - создание папок
#
# ✅ УМНАЯ ЛОГИКА:
# - Автоматическое определение типа изображения (категория/товар)
# - Пропуск системных файлов (__MACOSX, .DS_Store)
# - Поддержка вложенных папок в ZIP
# - Детальное логирование всех операций
#
# 🎯 РЕЗУЛЬТАТ:
# - Категории автоматически попадают в media/categories/
# - Товары автоматически попадают в media/product/
# - Существующие файлы перезаписываются
# - Полная статистика обработки