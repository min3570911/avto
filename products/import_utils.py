# 📁 products/import_utils.py
# 🔧 Утилиты для обработки импорта данных из Excel

import os
import re
import logging
from typing import Tuple, Optional, Dict, Any
from django.conf import settings
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from .models import Category, Product, ProductImage

logger = logging.getLogger(__name__)


def parse_product_sku(sku_string: str) -> Tuple[Optional[int], Optional[str]]:
    """
    🔍 Парсинг SKU товара для извлечения категории и названия

    Формат: "2.Acura MDX I" → category_sku=2, product_name="Acura MDX I"

    Args:
        sku_string: Строка SKU из Excel (колонка B)

    Returns:
        Tuple[category_sku, product_name] или (None, None) если формат неверный

    Examples:
        >>> parse_product_sku("2.Acura MDX I")
        (2, "Acura MDX I")

        >>> parse_product_sku("10.BMW 3 серия")
        (10, "BMW 3 серия")

        >>> parse_product_sku("Неверный формат")
        (None, None)
    """

    if not sku_string or not isinstance(sku_string, str):
        logger.warning(f"🚫 Пустой или неверный SKU: {sku_string}")
        return None, None

    # 🔍 Проверяем наличие точки
    if '.' not in sku_string:
        logger.warning(f"🚫 SKU без точки: {sku_string}")
        return None, None

    try:
        # 📝 Разбиваем по первой точке
        parts = sku_string.split('.', 1)

        if len(parts) != 2:
            logger.warning(f"🚫 Неверный формат SKU: {sku_string}")
            return None, None

        # 🔢 Парсим номер категории
        category_sku_str = parts[0].strip()
        if not category_sku_str.isdigit():
            logger.warning(f"🚫 SKU категории не число: {category_sku_str}")
            return None, None

        category_sku = int(category_sku_str)

        # 📝 Извлекаем название товара
        product_name = parts[1].strip()
        if not product_name:
            logger.warning(f"🚫 Пустое название товара в SKU: {sku_string}")
            return None, None

        logger.debug(f"✅ Распарсен SKU: {sku_string} → категория={category_sku}, товар='{product_name}'")
        return category_sku, product_name

    except (ValueError, IndexError) as e:
        logger.error(f"❌ Ошибка парсинга SKU '{sku_string}': {e}")
        return None, None


def validate_excel_row(row_data: Dict[str, Any]) -> Tuple[bool, list]:
    """
    ✅ Валидация данных строки Excel

    Args:
        row_data: Словарь с данными строки {column_name: value}

    Returns:
        Tuple[is_valid, errors_list]

    Проверяет:
    - Наличие обязательных полей
    - Корректность формата цены
    - Длину строк
    """

    errors = []

    # 📋 Обязательные поля
    required_fields = {
        'Код товара': 'product_sku',
        'Наименование товара': 'product_name',
        'Цена': 'price'
    }

    # 🔍 Проверка обязательных полей
    for excel_col, field_name in required_fields.items():
        value = row_data.get(excel_col)
        if not value or (isinstance(value, str) and not value.strip()):
            errors.append(f"Поле '{excel_col}' обязательно для заполнения")

    # 💰 Валидация цены
    price_value = row_data.get('Цена')
    if price_value is not None:
        try:
            # 🧹 Очистка от лишних символов
            if isinstance(price_value, str):
                price_clean = re.sub(r'[^\d,.]', '', price_value)
                price_clean = price_clean.replace(',', '.')
            else:
                price_clean = str(price_value)

            price_float = float(price_clean)
            if price_float < 0:
                errors.append(f"Цена не может быть отрицательной: {price_float}")
            elif price_float > 999999:
                errors.append(f"Цена слишком большая: {price_float}")

        except (ValueError, TypeError):
            errors.append(f"Некорректная цена: {price_value}")

    # 📏 Проверка длины строк
    string_limits = {
        'Код товара': 50,
        'Наименование товара': 100,
        'Title страницы': 200,
        'Meta-описание': 500
    }

    for field_name, max_length in string_limits.items():
        value = row_data.get(field_name)
        if value and isinstance(value, str) and len(value) > max_length:
            errors.append(f"Поле '{field_name}' слишком длинное (макс. {max_length} символов)")

    # 🔍 Валидация SKU товара (должен быть уникальным)
    product_sku = row_data.get('Код товара')
    if product_sku:
        existing_product = Product.objects.filter(product_sku=product_sku).first()
        if existing_product:
            logger.info(f"ℹ️ Товар с SKU '{product_sku}' уже существует - будет обновлен")

    is_valid = len(errors) == 0
    return is_valid, errors


def get_or_create_category_by_sku(category_sku: int, category_name: str) -> Category:
    """
    📂 Получение или создание категории по SKU

    Args:
        category_sku: Номер категории
        category_name: Название категории для создания

    Returns:
        Category: Существующая или новая категория
    """

    try:
        # 🔍 Поиск существующей категории
        category = Category.objects.get(category_sku=category_sku)
        logger.debug(f"✅ Найдена категория: {category.category_name} (SKU: {category_sku})")
        return category

    except Category.DoesNotExist:
        # 🆕 Создание новой категории
        logger.info(f"🆕 Создаем новую категорию: SKU={category_sku}, название='{category_name}'")

        category = Category.objects.create(
            category_sku=category_sku,
            category_name=category_name,
            slug=slugify(category_name),
            is_active=True,
            display_order=0
        )

        logger.info(f"✅ Создана категория: {category.category_name} (ID: {category.id})")
        return category


def process_product_image(product: Product, image_filename: str) -> bool:
    """
    🖼️ Обработка изображения товара

    Args:
        product: Объект товара
        image_filename: Имя файла изображения из Excel

    Returns:
        bool: True если изображение обработано успешно

    Логика:
    1. Проверяет существование файла в media/product/
    2. Если товар новый → создает главное изображение
    3. Если у товара нет главного → создает главное
    4. Если главное есть → не трогает
    5. Если изображение уже есть → пропускает
    """

    if not image_filename or not isinstance(image_filename, str):
        logger.warning(f"🚫 Пустое имя файла изображения для товара {product.product_name}")
        return False

    # 🧹 Очистка имени файла
    image_filename = image_filename.strip()

    # 📁 Путь к файлу изображения
    image_path = os.path.join('product', image_filename)
    full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)

    # 🔍 Проверка существования файла
    if not os.path.exists(full_image_path):
        logger.warning(f"📁 Файл изображения не найден: {full_image_path}")
        return False

    # 🔍 Проверяем, есть ли уже такое изображение у товара
    existing_image = product.product_images.filter(
        image__icontains=image_filename
    ).first()

    if existing_image:
        logger.info(f"ℹ️ Изображение '{image_filename}' уже существует у товара {product.product_name}")
        return True

    # 🔍 Проверяем наличие главного изображения
    has_main_image = product.has_main_image()

    if has_main_image:
        logger.info(f"ℹ️ У товара {product.product_name} уже есть главное изображение - пропускаем")
        return True

    try:
        # 🆕 Создаем новое изображение
        product_image = ProductImage.objects.create(
            product=product,
            image=image_path,
            is_main=True  # Устанавливаем как главное, если его нет
        )

        logger.info(f"✅ Создано главное изображение для товара {product.product_name}: {image_filename}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка создания изображения для товара {product.product_name}: {e}")
        return False


def clean_price_value(price_value: Any) -> int:
    """
    💰 Очистка и преобразование цены в integer

    Args:
        price_value: Значение цены из Excel (может быть строкой или числом)

    Returns:
        int: Очищенная цена

    Raises:
        ValueError: Если цену невозможно преобразовать
    """

    if price_value is None or price_value == '':
        return 0

    # 🧹 Очистка строкового значения
    if isinstance(price_value, str):
        # Убираем все кроме цифр, точек и запятых
        price_clean = re.sub(r'[^\d,.]', '', price_value.strip())
        # Заменяем запятую на точку
        price_clean = price_clean.replace(',', '.')
    else:
        price_clean = str(price_value)

    try:
        price_float = float(price_clean)
        return int(price_float)  # Конвертируем в int как в модели
    except (ValueError, TypeError) as e:
        raise ValueError(f"Невозможно преобразовать цену '{price_value}': {e}")


def generate_product_slug(product_name: str, product_sku: str = None) -> str:
    """
    🔗 Генерация уникального slug для товара

    Args:
        product_name: Название товара
        product_sku: SKU товара (опционально)

    Returns:
        str: Уникальный slug
    """

    # 🎯 Базовый slug из названия
    base_slug = slugify(product_name)

    # 🔍 Проверяем уникальность
    if not Product.objects.filter(slug=base_slug).exists():
        return base_slug

    # 🔢 Если не уникален, добавляем SKU
    if product_sku:
        sku_slug = f"{base_slug}-{slugify(product_sku)}"
        if not Product.objects.filter(slug=sku_slug).exists():
            return sku_slug

    # 🔢 Если все еще не уникален, добавляем номер
    counter = 1
    while True:
        numbered_slug = f"{base_slug}-{counter}"
        if not Product.objects.filter(slug=numbered_slug).exists():
            return numbered_slug
        counter += 1


def log_import_operation(operation_type: str, details: str, level: str = 'info'):
    """
    📝 Унифицированное логирование операций импорта

    Args:
        operation_type: Тип операции (create, update, error, skip)
        details: Детали операции
        level: Уровень логирования (info, warning, error)
    """

    emoji_map = {
        'create': '🆕',
        'update': '🔄',
        'error': '❌',
        'skip': '⏭️',
        'success': '✅'
    }

    emoji = emoji_map.get(operation_type, '📝')
    message = f"{emoji} {operation_type.upper()}: {details}"

    if level == 'error':
        logger.error(message)
    elif level == 'warning':
        logger.warning(message)
    else:
        logger.info(message)


# 🔧 ВСПОМОГАТЕЛЬНЫЕ КОНСТАНТЫ
EXCEL_COLUMN_MAPPING = {
    'A': 'Код товара',
    'B': 'Наименование товара',
    'C': 'Title страницы',
    'D': 'Цена',
    'E': 'Описание товара',
    'F': 'Мета-описание',
    'G': 'Изображение'
}

REQUIRED_COLUMNS = ['Код товара', 'Наименование товара', 'Цена']


# 📊 СТАТИСТИКА ИМПОРТА (для использования в процессоре)
class ImportStats:
    """📊 Класс для отслеживания статистики импорта"""

    def __init__(self):
        self.total_rows = 0
        self.processed_rows = 0
        self.created_count = 0
        self.updated_count = 0
        self.error_count = 0
        self.skipped_count = 0
        self.errors = []
        self.success_log = []

    def add_error(self, row_num: int, error_msg: str):
        """❌ Добавить ошибку"""
        self.error_count += 1
        self.errors.append(f"Строка {row_num}: {error_msg}")
        log_import_operation('error', f"Строка {row_num}: {error_msg}", 'error')

    def add_success(self, row_num: int, operation: str, item_name: str):
        """✅ Добавить успешную операцию"""
        if operation == 'create':
            self.created_count += 1
        elif operation == 'update':
            self.updated_count += 1

        message = f"Строка {row_num}: {operation} '{item_name}'"
        self.success_log.append(message)
        log_import_operation(operation, message)

    def add_skip(self, row_num: int, reason: str):
        """⏭️ Добавить пропуск"""
        self.skipped_count += 1
        message = f"Строка {row_num}: пропущена - {reason}"
        self.errors.append(message)
        log_import_operation('skip', message, 'warning')

    def get_summary(self) -> Dict[str, Any]:
        """📊 Получить сводку статистики"""
        return {
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'created_count': self.created_count,
            'updated_count': self.updated_count,
            'error_count': self.error_count,
            'skipped_count': self.skipped_count,
            'success_rate': round((self.created_count + self.updated_count) / max(self.total_rows, 1) * 100, 2),
            'errors': self.errors[:50],  # Ограничиваем количество ошибок в выводе
            'success_log': self.success_log[:50]
        }