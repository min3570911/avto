# 📁 products/image_utils.py
# 🛠️ ОБНОВЛЕННАЯ версия с защитой от блокировок файлов Windows
# 🖼️ Автоматическое распределение изображений по папкам categories/ и product/

import os
import time
import zipfile
import logging
import tempfile
import shutil
from typing import Tuple, List, Dict
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from references.models import Category

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

# ⏱️ Настройки для повторных попыток
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # секунды между попытками


def process_images_zip(zip_file: InMemoryUploadedFile) -> int:
    """
    🖼️ Основная функция обработки ZIP архива с изображениями

    🛠️ ОБНОВЛЕНО: Добавлена обработка блокировок файлов

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
        error_count = 0

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

                    # 💾 Сохраняем файл с обработкой блокировок
                    success = _save_image_file_with_retry(zip_archive, filename, target_folder)

                    if success:
                        processed_count += 1
                        if target_folder == 'categories':
                            categories_count += 1
                        else:
                            products_count += 1

                        logger.info(f"✅ Сохранено: {filename} → {target_folder}/")
                    else:
                        error_count += 1

                except Exception as e:
                    logger.error(f"❌ Ошибка обработки файла {filename}: {e}")
                    error_count += 1
                    continue

        # 📊 Логируем итоговую статистику
        logger.info(
            f"📈 Обработка ZIP завершена: "
            f"обработано {processed_count}, "
            f"категорий {categories_count}, "
            f"товаров {products_count}, "
            f"пропущено {skipped_count}, "
            f"ошибок {error_count}"
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


def _save_image_file_with_retry(zip_archive: zipfile.ZipFile, filename: str, target_folder: str) -> bool:
    """
    💾 🆕 НОВАЯ функция: Сохранение файла с механизмом повторных попыток

    🔒 Обрабатывает блокировки файлов Windows (WinError 32)
    ⏱️ Использует повторные попытки с задержкой
    🛡️ Безопасное сохранение через временный файл

    Args:
        zip_archive: Открытый ZIP архив
        filename: Имя файла в архиве
        target_folder: Целевая папка ('categories' или 'product')

    Returns:
        bool: True если файл успешно сохранен
    """
    basename = os.path.basename(filename)
    target_dir = os.path.join(settings.MEDIA_ROOT, target_folder)
    target_path = os.path.join(target_dir, basename)

    # 🔄 Попытки сохранения с повторами
    for attempt in range(MAX_RETRIES):
        try:
            # 📖 Читаем данные из архива
            with zip_archive.open(filename) as source_file:
                file_data = source_file.read()

            # 🛡️ Проверяем, что данные не пусты
            if not file_data:
                logger.error(f"❌ Файл {filename} пустой")
                return False

            # 💾 Сохраняем через временный файл для атомарности
            success = _atomic_file_save(file_data, target_path)

            if success:
                # ✅ Проверяем финальный результат
                if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                    logger.debug(f"💾 Файл сохранен (попытка {attempt + 1}): {target_path}")
                    return True
                else:
                    logger.warning(f"⚠️ Файл создался, но проверка не прошла: {target_path}")

            # ⏱️ Задержка перед следующей попыткой
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"⏳ Попытка {attempt + 1} неудачна для {filename}, повторяем через {RETRY_DELAY}с...")
                time.sleep(RETRY_DELAY)

        except PermissionError as e:
            logger.warning(f"🔒 Файл заблокирован {filename} (попытка {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # Увеличиваем задержку
            else:
                logger.error(f"❌ Не удалось сохранить файл {filename} после {MAX_RETRIES} попыток: {e}")

        except OSError as e:
            # 🔍 Специальная обработка Windows ошибок
            if "WinError 32" in str(e) or "being used by another process" in str(e):
                logger.warning(f"🔒 Windows блокировка файла {filename} (попытка {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 2))  # Еще больше задержка для Windows
                else:
                    logger.error(f"❌ Windows блокировка не снята для {filename} после {MAX_RETRIES} попыток")
            else:
                logger.error(f"❌ OS ошибка при сохранении {filename}: {e}")
                break

        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка сохранения {filename}: {e}")
            break

    return False


def _atomic_file_save(file_data: bytes, target_path: str) -> bool:
    """
    ⚛️ Атомарное сохранение файла через временный файл

    🛡️ Предотвращает повреждение файлов при сбоях
    🔒 Уменьшает вероятность блокировок

    Args:
        file_data: Данные для сохранения
        target_path: Путь к целевому файлу

    Returns:
        bool: True если сохранение успешно
    """
    temp_path = None
    try:
        target_dir = os.path.dirname(target_path)

        # 🗂️ Создаем временный файл в той же директории
        with tempfile.NamedTemporaryFile(
                dir=target_dir,
                delete=False,
                suffix='.tmp'
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_data)
            temp_file.flush()  # 💾 Принудительно записываем на диск
            os.fsync(temp_file.fileno())  # 🔄 Синхронизируем с файловой системой

        # 🔄 Атомарно перемещаем временный файл на место целевого
        if os.path.exists(target_path):
            # 🗑️ Удаляем старый файл, если он заблокирован
            _force_remove_file(target_path)

        shutil.move(temp_path, target_path)
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка атомарного сохранения: {e}")

        # 🧹 Очищаем временный файл при ошибке
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

        return False


def _force_remove_file(file_path: str, max_attempts: int = 3) -> bool:
    """
    🗑️ Принудительное удаление файла с повторными попытками

    💪 Специально для Windows блокировок

    Args:
        file_path: Путь к файлу для удаления
        max_attempts: Максимальное количество попыток

    Returns:
        bool: True если файл удален
    """
    for attempt in range(max_attempts):
        try:
            if os.path.exists(file_path):
                # 🔓 Попытка снять атрибуты только для чтения
                try:
                    os.chmod(file_path, 0o777)
                except:
                    pass

                os.unlink(file_path)
                return True
            else:
                return True  # Файл уже отсутствует

        except PermissionError as e:
            if attempt < max_attempts - 1:
                logger.debug(f"🔒 Попытка {attempt + 1} удаления заблокированного файла {file_path}")
                time.sleep(0.1 * (attempt + 1))
            else:
                logger.warning(f"⚠️ Не удалось удалить заблокированный файл {file_path}: {e}")

        except Exception as e:
            logger.warning(f"⚠️ Ошибка удаления файла {file_path}: {e}")
            break

    return False


def _save_image_file(zip_archive: zipfile.ZipFile, filename: str, target_folder: str) -> bool:
    """
    💾 🔄 ОБНОВЛЕНО: Теперь использует защищенную функцию с повторными попытками

    Args:
        zip_archive: Открытый ZIP архив
        filename: Имя файла в архиве
        target_folder: Целевая папка ('categories' или 'product')

    Returns:
        bool: True если файл успешно сохранен
    """
    # 🔄 Используем новую функцию с защитой от блокировок
    return _save_image_file_with_retry(zip_archive, filename, target_folder)


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

# 🔧 КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ✅ ДОБАВЛЕНО: _save_image_file_with_retry() - новая функция с повторными попытками
# ✅ ДОБАВЛЕНО: _atomic_file_save() - атомарное сохранение через временные файлы
# ✅ ДОБАВЛЕНО: _force_remove_file() - принудительное удаление заблокированных файлов
# ✅ ДОБАВЛЕНО: MAX_RETRIES, RETRY_DELAY - настройки повторных попыток
# ✅ ИЗМЕНЕНО: _save_image_file() - теперь использует защищенную функцию
# ✅ ИЗМЕНЕНО: process_images_zip() - добавлен счетчик ошибок
#
# 🎯 РЕЗУЛЬТАТ:
# - Устранение ошибки WinError 32
# - Повторные попытки при блокировках файлов
# - Атомарные операции сохранения
# - Подробное логирование всех операций
# - Сохранение всей существующей функциональности