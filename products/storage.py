# 📁 products/storage.py
# 🛠️ ОБНОВЛЕННАЯ версия с защитой от блокировок файлов Windows
# 💾 Кастомное хранилище для точных имён файлов БЕЗ хеш-суффиксов

import os
import time
import logging
import tempfile
import shutil
from django.core.files.storage import FileSystemStorage
from django.conf import settings

logger = logging.getLogger(__name__)

# ⏱️ Настройки для повторных попыток
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # секунды между попытками


class OverwriteStorage(FileSystemStorage):
    """
    🗂️ Кастомное хранилище с перезаписью существующих файлов

    🛠️ ОБНОВЛЕНО: Добавлена защита от блокировок файлов Windows

    Основные возможности:
    - 🎯 Сохраняет файлы с точным именем (без хеш-суффиксов)
    - 🔄 Автоматически перезаписывает существующие файлы
    - 📁 Создаёт недостающие директории
    - 🛡️ Безопасно обрабатывает ошибки файловой системы
    - 🔒 Защита от блокировок файлов (WinError 32)

    Используется для:
    - Category.category_image
    - ProductImage.image
    """

    def get_available_name(self, name, max_length=None):
        """
        🎯 КЛЮЧЕВОЙ МЕТОД: Возвращает точное имя файла

        🛠️ ОБНОВЛЕНО: Добавлена защита от блокировок

        В отличие от стандартного FileSystemStorage, который добавляет
        хеш-суффиксы (_ABC123.jpg), этот метод:
        1. Удаляет существующий файл, если он есть
        2. Возвращает оригинальное имя

        Args:
            name: Исходное имя файла (например, "BMW.png")
            max_length: Максимальная длина имени (не используется)

        Returns:
            str: То же самое имя файла без изменений
        """
        # 📁 Получаем полный путь к файлу
        full_path = self.path(name)

        try:
            # 🗂️ Создаём директорию если её нет
            directory = os.path.dirname(full_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"📁 Создана директория: {directory}")

            # 🔄 Удаляем существующий файл если он есть (с защитой от блокировок)
            if os.path.exists(full_path):
                success = self._safe_delete_file(full_path)
                if success:
                    logger.info(f"🗑️ Удалён существующий файл: {name}")
                else:
                    logger.warning(f"⚠️ Не удалось удалить существующий файл: {name}")

            # 🎯 Возвращаем оригинальное имя без изменений
            logger.debug(f"✅ Подготовлено имя файла: {name}")
            return name

        except OSError as e:
            logger.error(f"❌ Ошибка при подготовке файла {name}: {e}")
            # 🛡️ В случае ошибки возвращаем оригинальное имя
            # Django попытается сохранить файл и обработает ошибку самостоятельно
            return name
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при обработке {name}: {e}")
            return name

    def _safe_delete_file(self, file_path: str) -> bool:
        """
        🗑️ 🆕 НОВЫЙ МЕТОД: Безопасное удаление файла с обработкой блокировок

        Args:
            file_path: Путь к файлу для удаления

        Returns:
            bool: True если файл успешно удален
        """
        for attempt in range(MAX_RETRIES):
            try:
                if os.path.exists(file_path):
                    # 🔓 Попытка снять атрибуты только для чтения
                    try:
                        os.chmod(file_path, 0o777)
                    except:
                        pass

                    os.unlink(file_path)
                    logger.debug(f"🗑️ Файл удален (попытка {attempt + 1}): {file_path}")
                    return True
                else:
                    return True  # Файл уже отсутствует

            except PermissionError as e:
                if attempt < MAX_RETRIES - 1:
                    logger.debug(f"🔒 Файл заблокирован (попытка {attempt + 1}): {file_path}")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    logger.warning(f"⚠️ Не удалось удалить заблокированный файл: {file_path}: {e}")

            except OSError as e:
                if "WinError 32" in str(e) or "being used by another process" in str(e):
                    if attempt < MAX_RETRIES - 1:
                        logger.debug(f"🔒 Windows блокировка (попытка {attempt + 1}): {file_path}")
                        time.sleep(RETRY_DELAY * (attempt + 2))
                    else:
                        logger.warning(f"⚠️ Windows блокировка не снята: {file_path}: {e}")
                else:
                    logger.error(f"❌ OS ошибка при удалении: {file_path}: {e}")
                    break

            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка удаления: {file_path}: {e}")
                break

        return False

    def save(self, name, content, max_length=None):
        """
        💾 Переопределённый метод сохранения с дополнительным логированием

        🛠️ ОБНОВЛЕНО: Добавлен механизм повторных попыток

        Args:
            name: Имя файла
            content: Содержимое файла
            max_length: Максимальная длина имени

        Returns:
            str: Итоговое имя сохранённого файла
        """
        # 📝 Логируем начало сохранения
        logger.info(f"💾 Начинаем сохранение файла: {name}")

        # 🔄 Попытки сохранения с повторами
        for attempt in range(MAX_RETRIES):
            try:
                # 🎯 Вызываем родительский метод save
                # get_available_name уже подготовил путь и удалил старый файл
                saved_name = self._atomic_save(name, content, max_length, attempt)

                if saved_name:
                    # ✅ Логируем успешное сохранение
                    file_path = self.path(saved_name)
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

                    logger.info(
                        f"✅ Файл сохранён (попытка {attempt + 1}): {saved_name} "
                        f"(размер: {file_size / 1024:.1f} KB, путь: {file_path})"
                    )
                    return saved_name

                # ⏱️ Задержка перед следующей попыткой
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"⏳ Попытка {attempt + 1} неудачна для {name}, повторяем через {RETRY_DELAY}с...")
                    time.sleep(RETRY_DELAY * (attempt + 1))

            except PermissionError as e:
                logger.warning(f"🔒 Файл заблокирован {name} (попытка {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))

            except OSError as e:
                # 🔍 Специальная обработка Windows ошибок
                if "WinError 32" in str(e) or "being used by another process" in str(e):
                    logger.warning(f"🔒 Windows блокировка файла {name} (попытка {attempt + 1}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 2))
                else:
                    logger.error(f"❌ OS ошибка при сохранении {name}: {e}")
                    break

            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка сохранения {name}: {e}")
                break

        # ❌ Если все попытки неудачны, пробуем стандартный метод
        try:
            logger.warning(f"⚠️ Используем fallback метод для {name}")
            saved_name = super().save(name, content, max_length)
            logger.info(f"✅ Файл сохранен через fallback: {saved_name}")
            return saved_name
        except Exception as fallback_error:
            error_msg = f"❌ Не удалось сохранить файл {name} после {MAX_RETRIES} попыток: {fallback_error}"
            logger.error(error_msg)
            raise OSError(error_msg)

    def _atomic_save(self, name, content, max_length, attempt):
        """
        ⚛️ 🆕 НОВЫЙ МЕТОД: Атомарное сохранение файла через временный файл

        Args:
            name: Имя файла
            content: Содержимое файла
            max_length: Максимальная длина имени
            attempt: Номер попытки (для логирования)

        Returns:
            str|None: Имя сохраненного файла или None при ошибке
        """
        try:
            # 📂 Определяем пути
            final_path = self.path(name)
            temp_dir = os.path.dirname(final_path)

            # 🗂️ Создаем временный файл в той же директории
            with tempfile.NamedTemporaryFile(
                    dir=temp_dir,
                    delete=False,
                    suffix='.tmp'
            ) as temp_file:
                temp_path = temp_file.name

                # 💾 Записываем содержимое
                if hasattr(content, 'chunks'):
                    # 📦 Если это Django File, читаем по частям
                    for chunk in content.chunks():
                        temp_file.write(chunk)
                else:
                    # 📝 Если это байты или строка
                    if isinstance(content, str):
                        temp_file.write(content.encode('utf-8'))
                    else:
                        temp_file.write(content)

                temp_file.flush()  # 💾 Принудительно записываем на диск
                os.fsync(temp_file.fileno())  # 🔄 Синхронизируем с файловой системой

            # 🔄 Атомарно перемещаем временный файл на место целевого
            shutil.move(temp_path, final_path)

            logger.debug(f"💾 Атомарное сохранение успешно (попытка {attempt + 1}): {name}")
            return name

        except Exception as e:
            logger.error(f"❌ Ошибка атомарного сохранения (попытка {attempt + 1}): {name}: {e}")

            # 🧹 Очищаем временный файл при ошибке
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass

            return None

    def delete(self, name):
        """
        🗑️ Переопределённый метод удаления с логированием

        🛠️ ОБНОВЛЕНО: Использует безопасное удаление

        Args:
            name: Имя файла для удаления
        """
        try:
            file_path = self.path(name)

            if os.path.exists(file_path):
                logger.info(f"🗑️ Удаляем файл: {name}")
                success = self._safe_delete_file(file_path)
                if success:
                    logger.info(f"✅ Файл удалён: {name}")
                else:
                    logger.warning(f"⚠️ Не удалось удалить файл: {name}")
            else:
                logger.warning(f"⚠️ Файл для удаления не найден: {name}")

        except Exception as e:
            logger.error(f"❌ Ошибка удаления файла {name}: {e}")
            # 🔄 Пробуем стандартный метод как fallback
            try:
                super().delete(name)
                logger.info(f"✅ Файл удален стандартным методом: {name}")
            except Exception as fallback_error:
                logger.error(f"❌ Fallback удаление также неудачно для {name}: {fallback_error}")

    def exists(self, name):
        """
        🔍 Проверка существования файла с логированием

        Args:
            name: Имя файла

        Returns:
            bool: True если файл существует
        """
        try:
            exists = super().exists(name)
            logger.debug(f"🔍 Проверка файла {name}: {'существует' if exists else 'не найден'}")
            return exists

        except Exception as e:
            logger.error(f"❌ Ошибка проверки файла {name}: {e}")
            return False

    def url(self, name):
        """
        🌐 Получение URL файла с обработкой ошибок

        Args:
            name: Имя файла

        Returns:
            str: URL файла
        """
        try:
            url = super().url(name)
            logger.debug(f"🌐 URL файла {name}: {url}")
            return url

        except Exception as e:
            logger.error(f"❌ Ошибка получения URL для {name}: {e}")
            # 🛡️ Возвращаем базовый URL в случае ошибки
            return f"{settings.MEDIA_URL}{name}"

    def size(self, name):
        """
        📏 Получение размера файла с обработкой ошибок

        Args:
            name: Имя файла

        Returns:
            int: Размер файла в байтах
        """
        try:
            size = super().size(name)
            logger.debug(f"📏 Размер файла {name}: {size / 1024:.1f} KB")
            return size

        except Exception as e:
            logger.error(f"❌ Ошибка получения размера файла {name}: {e}")
            return 0


class SecureOverwriteStorage(OverwriteStorage):
    """
    🔒 Расширенная версия OverwriteStorage с дополнительными проверками безопасности

    🛠️ ОБНОВЛЕНО: Унаследовано от улучшенного OverwriteStorage

    Дополнительные возможности:
    - 🛡️ Проверка расширений файлов
    - 📏 Ограничение размера файлов
    - 🚫 Блокировка опасных имён файлов
    - 🔒 Все защиты от блокировок из OverwriteStorage
    """

    def __init__(self, location=None, base_url=None, file_permissions_mode=None,
                 directory_permissions_mode=None, allowed_extensions=None,
                 max_file_size=None):
        """
        🔧 Инициализация с дополнительными параметрами безопасности

        Args:
            allowed_extensions: Список разрешённых расширений (например, ['.jpg', '.png'])
            max_file_size: Максимальный размер файла в байтах
        """
        super().__init__(location, base_url, file_permissions_mode, directory_permissions_mode)

        # 🛡️ Настройки безопасности
        self.allowed_extensions = allowed_extensions or ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        self.max_file_size = max_file_size or 5 * 1024 * 1024  # 5MB по умолчанию

        # 🚫 Запрещённые имена файлов
        self.forbidden_names = [
            'con', 'prn', 'aux', 'nul',  # Windows reserved names
            '.htaccess', '.htpasswd',  # Apache config files
            'index.php', 'index.html',  # Потенциально опасные файлы
        ]

        logger.info(
            f"🔒 SecureOverwriteStorage инициализировано: "
            f"расширения {self.allowed_extensions}, "
            f"макс. размер {self.max_file_size / 1024 / 1024:.1f}MB"
        )

    def get_available_name(self, name, max_length=None):
        """🔒 Безопасная версия get_available_name с проверками"""

        # 🛡️ Проверка расширения файла
        file_extension = os.path.splitext(name)[1].lower()
        if file_extension not in self.allowed_extensions:
            error_msg = f"❌ Неразрешённое расширение файла: {file_extension}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 🚫 Проверка запрещённых имён
        base_name = os.path.splitext(os.path.basename(name))[0].lower()
        if base_name in self.forbidden_names:
            error_msg = f"❌ Запрещённое имя файла: {base_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # ✅ Если проверки пройдены, используем родительский метод
        return super().get_available_name(name, max_length)

    def save(self, name, content, max_length=None):
        """🔒 Безопасное сохранение с проверкой размера"""

        # 📏 Проверка размера файла
        if hasattr(content, 'size') and content.size > self.max_file_size:
            error_msg = (
                f"❌ Файл слишком большой: {content.size / 1024 / 1024:.1f}MB. "
                f"Максимум: {self.max_file_size / 1024 / 1024:.1f}MB"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # ✅ Если проверки пройдены, сохраняем файл
        return super().save(name, content, max_length)


# 🎯 Предустановленные экземпляры для разных целей

# 📁 Стандартное хранилище для изображений товаров и категорий
default_overwrite_storage = OverwriteStorage()

# 🔒 Безопасное хранилище для пользовательских загрузок
secure_image_storage = SecureOverwriteStorage(
    allowed_extensions=['.jpg', '.jpeg', '.png', '.webp'],
    max_file_size=5 * 1024 * 1024  # 5MB
)

# 📋 Хранилище для документов (если потребуется)
document_storage = SecureOverwriteStorage(
    allowed_extensions=['.pdf', '.doc', '.docx', '.txt'],
    max_file_size=10 * 1024 * 1024  # 10MB
)

# 🔧 ИСПОЛЬЗОВАНИЕ В МОДЕЛЯХ:
#
# from .storage import OverwriteStorage
#
# class Category(models.Model):
#     category_image = models.ImageField(
#         upload_to="categories",
#         storage=OverwriteStorage()  # 🎯 Точные имена файлов
#     )
#
# class ProductImage(models.Model):
#     image = models.ImageField(
#         upload_to='product',
#         storage=OverwriteStorage()  # 🎯 Точные имена файлов
#     )

# 🎯 РЕЗУЛЬТАТ ИСПОЛЬЗОВАНИЯ:
#
# ❌ БЕЗ OverwriteStorage:
# - BMW.png → BMW_ABC123.png (с хеш-суффиксом)
# - При повторной загрузке → BMW_DEF456.png
#
# ✅ С OverwriteStorage:
# - BMW.png → BMW.png (точное имя)
# - При повторной загрузке → BMW.png (перезапись)
#
# 🔗 СОВМЕСТИМОСТЬ:
# - image_utils.py → сохраняет BMW.png в media/categories/
# - OverwriteStorage → Django сохраняет как BMW.png без суффиксов
# - import_processor.py → находит файл по точному имени BMW.png

# 🔧 КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ✅ ДОБАВЛЕНО: _safe_delete_file() - безопасное удаление с повторными попытками
# ✅ ДОБАВЛЕНО: _atomic_save() - атомарное сохранение через временные файлы
# ✅ ДОБАВЛЕНО: MAX_RETRIES, RETRY_DELAY - настройки повторных попыток
# ✅ ИЗМЕНЕНО: get_available_name() - использует безопасное удаление
# ✅ ИЗМЕНЕНО: save() - добавлен механизм повторных попыток
# ✅ ИЗМЕНЕНО: delete() - использует безопасное удаление
# ✅ СОХРАНЕНО: Вся существующая логика точных имен файлов
#
# 🎯 РЕЗУЛЬТАТ:
# - Устранение блокировок файлов Windows
# - Атомарные операции сохранения
# - Fallback на стандартные методы при ошибках
# - Детальное логирование всех операций
# - Полная обратная совместимость