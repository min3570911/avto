# 📁 products/storage.py
# 💾 Кастомное хранилище для точных имён файлов БЕЗ хеш-суффиксов
# 🎯 OverwriteStorage гарантирует, что BMW.png останется BMW.png

import os
import logging
from django.core.files.storage import FileSystemStorage
from django.conf import settings

logger = logging.getLogger(__name__)


class OverwriteStorage(FileSystemStorage):
    """
    🗂️ Кастомное хранилище с перезаписью существующих файлов

    Основные возможности:
    - 🎯 Сохраняет файлы с точным именем (без хеш-суффиксов)
    - 🔄 Автоматически перезаписывает существующие файлы
    - 📁 Создаёт недостающие директории
    - 🛡️ Безопасно обрабатывает ошибки файловой системы

    Используется для:
    - Category.category_image
    - ProductImage.image
    """

    def get_available_name(self, name, max_length=None):
        """
        🎯 КЛЮЧЕВОЙ МЕТОД: Возвращает точное имя файла

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

            # 🔄 Удаляем существующий файл если он есть
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"🗑️ Удалён существующий файл: {name}")

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

    def save(self, name, content, max_length=None):
        """
        💾 Переопределённый метод сохранения с дополнительным логированием

        Args:
            name: Имя файла
            content: Содержимое файла
            max_length: Максимальная длина имени

        Returns:
            str: Итоговое имя сохранённого файла
        """
        try:
            # 📝 Логируем начало сохранения
            logger.info(f"💾 Начинаем сохранение файла: {name}")

            # 🎯 Вызываем родительский метод save
            # get_available_name уже подготовил путь и удалил старый файл
            saved_name = super().save(name, content, max_length)

            # ✅ Логируем успешное сохранение
            file_path = self.path(saved_name)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

            logger.info(
                f"✅ Файл сохранён: {saved_name} "
                f"(размер: {file_size / 1024:.1f} KB, путь: {file_path})"
            )

            return saved_name

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения файла {name}: {e}")
            raise

    def delete(self, name):
        """
        🗑️ Переопределённый метод удаления с логированием

        Args:
            name: Имя файла для удаления
        """
        try:
            file_path = self.path(name)

            if os.path.exists(file_path):
                logger.info(f"🗑️ Удаляем файл: {name}")
                super().delete(name)
                logger.info(f"✅ Файл удалён: {name}")
            else:
                logger.warning(f"⚠️ Файл для удаления не найден: {name}")

        except Exception as e:
            logger.error(f"❌ Ошибка удаления файла {name}: {e}")
            raise

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

    Дополнительные возможности:
    - 🛡️ Проверка расширений файлов
    - 📏 Ограничение размера файлов
    - 🚫 Блокировка опасных имён файлов
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