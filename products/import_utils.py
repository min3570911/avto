# 📁 products/import_utils.py
# 🛠️ ПРАВИЛЬНАЯ версия утилит импорта с двойной логикой (категории + товары)
# ✅ Учитывает структуру: строки с точкой = категории, без точки = товары

import logging
import openpyxl
from typing import Dict, List, Tuple, Optional, Union
from decimal import Decimal, InvalidOperation
from django.core.files.uploadedfile import InMemoryUploadedFile
import re

logger = logging.getLogger(__name__)

# 🗂️ Маппинг колонок Excel (одинаковый для категорий и товаров)
EXCEL_COLUMN_MAPPING = {
    'identifier': 0,  # A: Категория (1.BMW) или SKU товара (10001)
    'name': 1,  # B: Название категории или товара
    'title': 2,  # C: Title страницы
    'price': 3,  # D: Цена (только для товаров, у категорий пустая)
    'description': 4,  # E: Описание
    'meta_description': 5,  # F: Мета-описание
    'image': 6  # G: Изображение
}

# 📋 Обязательные поля
REQUIRED_FIELDS = ['identifier', 'name']

# 🎯 Максимальные длины полей
FIELD_LIMITS = {
    'identifier': 50,
    'name': 200,
    'title': 70,
    'price': None,  # Числовое поле
    'description': None,  # Без ограничений для CKEditor
    'meta_description': 160,
    'image': 255
}


def read_excel_file(file: InMemoryUploadedFile) -> Tuple[bool, Union[List[Dict], str]]:
    """
    📊 Чтение Excel файла с разделением на категории и товары

    Args:
        file: Загруженный Excel файл

    Returns:
        Tuple[bool, Union[List[Dict], str]]: (success, data_or_error)
    """
    try:
        logger.info(f"🔄 Начинаем чтение файла: {file.name}")

        # 📖 Загружаем Excel файл
        workbook = openpyxl.load_workbook(file, data_only=True)
        worksheet = workbook.active

        # 📏 Получаем размеры таблицы
        max_row = worksheet.max_row
        max_col = worksheet.max_column

        logger.info(f"📊 Размер таблицы: {max_row} строк, {max_col} колонок")

        if max_row < 2:
            return False, "❌ Файл должен содержать минимум 2 строки (заголовок + данные)"

        # 📋 Читаем данные начиная со второй строки (пропускаем заголовок)
        data = []

        for row_num in range(2, max_row + 1):
            try:
                # 🔍 Получаем значения ячеек
                row_data = {}

                # 📝 Безопасное извлечение данных из каждой ячейки
                for field_name, col_index in EXCEL_COLUMN_MAPPING.items():
                    cell_value = None

                    if col_index < max_col:
                        cell = worksheet.cell(row=row_num, column=col_index + 1)  # +1 так как Excel 1-based
                        cell_value = cell.value

                    # 🧹 Очистка и нормализация данных
                    if cell_value is not None:
                        if isinstance(cell_value, str):
                            cell_value = cell_value.strip()
                            if not cell_value:
                                cell_value = None

                    row_data[field_name] = cell_value

                # 🚫 Пропускаем строки без идентификатора
                if not row_data.get('identifier'):
                    logger.warning(f"⚠️ Строка {row_num}: пропущена (нет идентификатора)")
                    continue

                # 🎯 Определяем тип строки: категория или товар
                identifier = str(row_data['identifier']).strip()
                is_category = '.' in identifier

                row_data['row_number'] = row_num
                row_data['is_category'] = is_category

                if is_category:
                    # 📂 Это категория - извлекаем чистое название
                    row_data['category_name'] = extract_category_name(identifier)
                    row_data['type'] = 'category'
                else:
                    # 🛍️ Это товар - сохраняем SKU
                    row_data['sku'] = identifier
                    row_data['type'] = 'product'

                data.append(row_data)

            except Exception as e:
                logger.error(f"❌ Ошибка обработки строки {row_num}: {str(e)}")
                continue

        logger.info(f"✅ Успешно прочитано {len(data)} строк данных")
        return True, data

    except Exception as e:
        error_msg = f"❌ Ошибка чтения файла: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def extract_category_name(category_identifier: str) -> str:
    """
    📂 Извлечение чистого названия категории из идентификатора

    Примеры:
    - "1.BMW" -> "BMW"
    - "2.Acura" -> "Acura"
    - "sky.BMW" -> "BMW"

    Args:
        category_identifier: Идентификатор категории с точкой

    Returns:
        str: Чистое название категории
    """
    try:
        # 🔍 Берём часть после последней точки
        parts = category_identifier.split('.')
        if len(parts) >= 2:
            category_name = parts[-1].strip().upper()
            return category_name if category_name else 'ТОВАРЫ'

        return category_identifier.strip().upper()

    except Exception as e:
        logger.error(f"Ошибка извлечения категории из '{category_identifier}': {e}")
        return 'ТОВАРЫ'


def validate_row(row_data: Dict) -> Tuple[bool, List[str]]:
    """
    ✅ Валидация строки (категории или товара)

    Args:
        row_data: Словарь с данными строки

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []

    try:
        # 🔍 Проверка обязательных полей
        for field in REQUIRED_FIELDS:
            if not row_data.get(field):
                errors.append(f"❌ Обязательное поле '{field}' не заполнено")

        # 📏 Проверка длины текстовых полей
        for field, max_length in FIELD_LIMITS.items():
            if max_length and row_data.get(field):
                value = str(row_data[field])
                if len(value) > max_length:
                    errors.append(f"⚠️ Поле '{field}' слишком длинное ({len(value)}/{max_length})")

        # 💰 Проверка цены - только для товаров
        if row_data.get('type') == 'product':
            price_value = row_data.get('price')
            if price_value is not None:
                try:
                    normalized_price = normalize_price(price_value)
                    if normalized_price < 0:
                        errors.append(f"❌ Цена не может быть отрицательной: {normalized_price}")
                    elif normalized_price > 999999:
                        errors.append(f"⚠️ Цена слишком большая: {normalized_price}")
                except Exception:
                    errors.append(f"❌ Некорректная цена: {price_value}")

        # 🎨 Проверка имени изображения
        if row_data.get('image'):
            image_name = str(row_data['image'])
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if not any(image_name.lower().endswith(ext) for ext in valid_extensions):
                errors.append(f"⚠️ Неподдерживаемый формат изображения: {image_name}")

        # 🏷️ Проверка идентификатора
        identifier = str(row_data['identifier']).strip()
        if len(identifier) > 50:
            errors.append(f"❌ Идентификатор слишком длинный: {identifier}")

        # ✅ Дополнительная валидация названия
        name = row_data.get('name', '').strip()
        if name and len(name) < 3:
            errors.append(f"⚠️ Название слишком короткое: {name}")

    except Exception as e:
        errors.append(f"❌ Ошибка валидации: {str(e)}")
        logger.error(f"Ошибка при валидации строки: {e}")

    is_valid = len(errors) == 0
    return is_valid, errors


def normalize_price(price_value: Union[str, int, float, None]) -> float:
    """
    💰 Нормализация цены (только для товаров)

    Args:
        price_value: Значение цены в любом формате

    Returns:
        float: Нормализованная цена (0.0 если пустая)
    """
    try:
        if price_value is None or price_value == '':
            return 0.0

        if isinstance(price_value, (int, float)):
            return float(price_value)

        if isinstance(price_value, str):
            # 🧹 Удаляем валютные символы и лишние символы
            price_clean = re.sub(r'[^\d.,]', '', price_value.strip())

            if not price_clean:
                return 0.0

            # 🔄 Заменяем запятую на точку
            price_clean = price_clean.replace(',', '.')

            # 🎯 Обрабатываем случай множественных точек
            if price_clean.count('.') > 1:
                parts = price_clean.split('.')
                price_clean = ''.join(parts[:-1]) + '.' + parts[-1]

            return float(price_clean)

    except Exception as e:
        logger.warning(f"⚠️ Не удалось обработать цену '{price_value}': {e}")

    return 0.0


def separate_categories_and_products(raw_data: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    🔄 Разделение данных на категории и товары с привязкой

    Args:
        raw_data: Сырые данные из Excel

    Returns:
        Tuple[List[Dict], List[Dict], List[Dict]]: (categories, products, invalid_data)
    """
    categories = []
    products = []
    invalid_data = []
    current_category = None

    for row in raw_data:
        try:
            # ✅ Валидируем строку
            is_valid, errors = validate_row(row)

            if not is_valid:
                row['errors'] = errors
                invalid_data.append(row)
                continue

            if row['is_category']:
                # 📂 Обрабатываем категорию
                category_data = {
                    'category_name': row['category_name'],
                    'name': row.get('name', ''),
                    'title': row.get('title', ''),
                    'description': row.get('description', ''),
                    'meta_description': row.get('meta_description', ''),
                    'image': row.get('image', ''),
                    'row_number': row.get('row_number', 0)
                }

                categories.append(category_data)
                current_category = row['category_name']  # 💾 Запоминаем текущую категорию

            else:
                # 🛍️ Обрабатываем товар
                if not current_category:
                    # ⚠️ Товар без категории - создаём дефолтную
                    current_category = 'ТОВАРЫ'

                product_data = {
                    'sku': row['sku'],
                    'name': row.get('name', ''),
                    'title': row.get('title', ''),
                    'price': normalize_price(row.get('price')),
                    'description': row.get('description', ''),
                    'meta_description': row.get('meta_description', ''),
                    'image': row.get('image', ''),
                    'category_name': current_category,  # 🔗 Привязываем к текущей категории
                    'row_number': row.get('row_number', 0)
                }

                products.append(product_data)

        except Exception as e:
            logger.error(f"❌ Ошибка обработки строки {row.get('row_number', '?')}: {e}")
            row['errors'] = [f"Ошибка обработки: {str(e)}"]
            invalid_data.append(row)

    logger.info(f"✅ Разделено: {len(categories)} категорий, {len(products)} товаров, {len(invalid_data)} ошибок")

    return categories, products, invalid_data


def get_import_statistics(categories: List[Dict], products: List[Dict], invalid_data: List[Dict]) -> Dict:
    """
    📊 Подсчёт статистики импорта с разделением на категории и товары
    """
    try:
        category_names = set(cat['category_name'] for cat in categories)
        products_with_images = sum(1 for prod in products if prod.get('image'))
        products_with_prices = sum(1 for prod in products if prod.get('price', 0) > 0)

        return {
            'total_rows': len(categories) + len(products) + len(invalid_data),
            'categories_count': len(categories),
            'products_count': len(products),
            'invalid_rows': len(invalid_data),
            'category_names': list(category_names),
            'products_with_images': products_with_images,
            'products_with_prices': products_with_prices,
            'categories_with_images': sum(1 for cat in categories if cat.get('image')),
        }
    except Exception as e:
        logger.error(f"Ошибка подсчёта статистики: {e}")
        return {}

# 🚀 ОСНОВНЫЕ ИЗМЕНЕНИЯ:
# ✅ Добавлено определение типа строки (категория/товар) по наличию точки
# ✅ Разделение данных на categories и products с привязкой
# ✅ Отдельная валидация для категорий (цена не обязательна)
# ✅ Правильное извлечение названия категории из "1.BMW" -> "BMW"
# ✅ Запоминание текущей категории для привязки товаров
# ✅ Обновлённая статистика с разделением типов данных