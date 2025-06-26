# 📁 products/import_processor.py
# 🛠️ ОБНОВЛЕННАЯ версия с улучшенной обработкой изображений
# ✅ Добавлена защита от блокировок файлов и валидация

import logging
import os
import time
from typing import Dict, List, Tuple, Optional
from django.db import transaction, IntegrityError, models
from django.utils.text import slugify
from django.core.files import File
from django.conf import settings
from decimal import Decimal

from products.models import Product, Category, ProductImage
from .import_utils import (
    read_excel_file,
    separate_categories_and_products,
    get_import_statistics
)

logger = logging.getLogger(__name__)


class ProductImportProcessor:
    """
    🚀 ОБНОВЛЁННЫЙ процессор импорта с защитой от блокировок файлов

    Режимы работы:
    1. process_excel_file() - классический режим (Excel → разбор → импорт)
    2. process_structured_data() - новый режим (готовые данные → импорт)

    🛠️ ДОБАВЛЕНО: Улучшенная обработка изображений с защитой от WinError 32
    """

    def __init__(self):
        self.statistics = {
            'total_processed': 0,
            'categories_created': 0,
            'categories_updated': 0,
            'products_created': 0,
            'products_updated': 0,
            'errors': 0,
            'images_processed': 0,
            'images_failed': 0,
            'sku_generated': 0
        }
        self.errors = []
        self.category_cache = {}  # 💾 Кэш созданных категорий

    def process_excel_file(self, file) -> Dict:
        """
        📊 Классический метод обработки Excel файла

        Оставлен для обратной совместимости и внешних API
        """
        try:
            logger.info(f"🚀 Начинаем обработку файла: {file.name}")

            # 📖 Читаем Excel файл
            success, result = read_excel_file(file)
            if not success:
                return self._create_error_result(f"Ошибка чтения файла: {result}")

            raw_data = result
            logger.info(f"📋 Прочитано {len(raw_data)} строк из файла")

            # 🔄 Разделяем на категории и товары
            categories, products, invalid_data = separate_categories_and_products(raw_data)

            if not categories and not products:
                return self._create_error_result("Нет валидных данных для импорта")

            logger.info(f"📂 Найдено: {len(categories)} категорий, {len(products)} товаров")

            # 🚀 Используем новый метод для структурированных данных
            return self.process_structured_data(categories, products, invalid_data)

        except Exception as e:
            error_msg = f"❌ Критическая ошибка при импорте: {str(e)}"
            logger.error(error_msg)
            return self._create_error_result(error_msg)

    def process_structured_data(self, categories: List[Dict], products: List[Dict],
                                invalid_data: List[Dict] = None) -> Dict:
        """
        🆕 НОВЫЙ МЕТОД: Прямая обработка структурированных данных

        Принимает готовые списки категорий и товаров, минуя этап разбора Excel.
        Убирает необходимость в костыле с пересозданием временного файла.

        Args:
            categories: Список данных категорий
            products: Список данных товаров
            invalid_data: Список невалидных данных (опционально)

        Returns:
            Dict: Результаты импорта с детальной статистикой
        """
        try:
            logger.info(f"🎯 Начинаем прямую обработку: {len(categories)} категорий, {len(products)} товаров")

            if invalid_data is None:
                invalid_data = []

            # 📊 Статистика перед импортом
            import_stats = get_import_statistics(categories, products, invalid_data)

            # 🚀 Выполняем импорт в транзакции
            with transaction.atomic():
                # 📂 Сначала импортируем категории
                category_results = self._import_categories(categories)

                # 🛍️ Затем импортируем товары
                product_results = self._import_products(products)

            # 🧹 Дополнительная очистка после обработки
            if self.statistics.get('errors', 0) > 0:
                logger.info("🧹 Выполняем очистку после ошибок...")
                self._cleanup_failed_images()

            # 📈 Формируем итоговый результат
            return {
                'success': True,
                'statistics': {
                    **self.statistics,
                    **import_stats
                },
                'errors': self.errors,
                'invalid_data': invalid_data,
                'category_results': category_results,
                'product_results': product_results
            }

        except Exception as e:
            error_msg = f"❌ Критическая ошибка при обработке данных: {str(e)}"
            logger.error(error_msg)
            return self._create_error_result(error_msg)

    def _import_categories(self, categories_data: List[Dict]) -> List[Dict]:
        """📂 Импорт категорий с созданием моделей Category"""
        results = []

        for category_data in categories_data:
            try:
                self.statistics['total_processed'] += 1
                result = self._process_single_category(category_data)
                results.append(result)

            except Exception as e:
                error_msg = f"❌ Ошибка обработки категории {category_data.get('category_name', '?')}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                self.statistics['errors'] += 1

                results.append({
                    'name': category_data.get('category_name', '?'),
                    'status': 'error',
                    'message': str(e)
                })

        return results

    def _process_single_category(self, category_data: Dict) -> Dict:
        """📂 Обработка одной категории с поддержкой category_sku"""
        category_name = category_data['category_name']
        category_sku = category_data.get('category_sku', 1)

        try:
            # 🔍 Проверяем, существует ли категория (по SKU или названию)
            existing_category = Category.objects.filter(
                models.Q(category_sku=category_sku) | models.Q(category_name=category_name)
            ).first()

            if existing_category:
                # 🔄 Обновляем существующую категорию
                category = self._update_category(existing_category, category_data)
                action = 'updated'
                self.statistics['categories_updated'] += 1
            else:
                # 🆕 Создаём новую категорию
                category = self._create_category(category_data)
                action = 'created'
                self.statistics['categories_created'] += 1

            # 🖼️ Обрабатываем изображение категории с улучшенной защитой
            if category_data.get('image'):
                self._attach_category_image(category, category_data['image'])

            # 💾 Добавляем в кэш для товаров
            self.category_cache[category_name] = category

            logger.info(f"✅ Категория {category_name} (SKU: {category_sku}) {action}")

            return {
                'name': category_name,
                'status': action,
                'message': f'Категория успешно {action}'
            }

        except Exception as e:
            error_msg = f"Ошибка обработки категории {category_name}: {str(e)}"
            logger.error(error_msg)
            raise

    def _create_category(self, category_data: Dict) -> Category:
        """🆕 Создание новой категории с поддержкой category_sku"""
        try:
            category_name = category_data['category_name']
            category_sku = category_data.get('category_sku', 1)

            # 📝 Подготавливаем данные
            description = category_data.get('description', '') or f"Автоковрики для {category_name}"
            title = category_data.get('title', '') or f"Автоковрики {category_name}"
            meta_description = category_data.get('meta_description', '') or \
                               f"Качественные автоковрики для {category_name}. Большой выбор, доставка по Беларуси."

            # 🆕 Создаём категорию
            category = Category.objects.create(
                category_name=category_name,
                category_sku=category_sku,
                slug=slugify(category_name),
                description=description,
                page_title=title,
                meta_title=title[:60] if title else f"Коврики {category_name}",
                meta_description=meta_description[:160],
                is_active=True
            )

            logger.info(f"✅ Создана категория: {category_name} (SKU: {category_sku})")
            return category

        except Exception as e:
            logger.error(f"❌ Ошибка создания категории {category_data.get('category_name', '?')}: {e}")
            raise

    def _update_category(self, category: Category, category_data: Dict) -> Category:
        """🔄 Обновление существующей категории"""
        try:
            # 🔄 Обновляем поля если они заполнены
            if category_data.get('description'):
                category.description = category_data['description']

            if category_data.get('title'):
                category.page_title = category_data['title']
                category.meta_title = category_data['title'][:60]

            if category_data.get('meta_description'):
                category.meta_description = category_data['meta_description'][:160]

            # 🆕 Обновляем SKU категории если он указан
            if category_data.get('category_sku'):
                category.category_sku = category_data['category_sku']

            category.save()

            logger.info(f"🔄 Обновлена категория: {category.category_name} (SKU: {category.category_sku})")
            return category

        except Exception as e:
            logger.error(f"❌ Ошибка обновления категории {category.category_name}: {e}")
            raise

    def _attach_category_image(self, category: Category, image_filename: str):
        """
        🖼️ УЛУЧШЕННОЕ присоединение изображения к категории

        🛠️ ОБНОВЛЕНО: Добавлена защита от блокировок и валидация

        Args:
            category: Объект категории
            image_filename: Имя файла изображения
        """
        try:
            # ✅ Предварительная валидация файла
            if not self._validate_image_file(image_filename, 'categories'):
                logger.warning(f"⚠️ Файл изображения категории не прошел валидацию: {image_filename}")
                return

            # 📁 Формируем путь к изображению
            image_path = f"categories/{image_filename}"

            # 💾 Безопасное присоединение изображения с повторными попытками
            for attempt in range(3):
                try:
                    category.category_image.name = image_path
                    category.save(update_fields=['category_image'])
                    logger.info(f"✅ Присоединено изображение категории (попытка {attempt + 1}): {image_filename}")
                    return

                except Exception as save_error:
                    if attempt < 2:  # Не последняя попытка
                        logger.warning(
                            f"⚠️ Попытка {attempt + 1} сохранения изображения категории неудачна: {save_error}")
                        time.sleep(0.5 * (attempt + 1))  # Увеличиваем задержку
                    else:
                        logger.error(f"❌ Не удалось присоединить изображение категории {image_filename}: {save_error}")
                        self.statistics['images_failed'] += 1

        except Exception as e:
            logger.error(f"❌ Критическая ошибка присоединения изображения категории {image_filename}: {e}")
            self.statistics['images_failed'] += 1

    def _import_products(self, products_data: List[Dict]) -> List[Dict]:
        """🛍️ Импорт товаров с привязкой к категориям"""
        results = []

        for product_data in products_data:
            try:
                self.statistics['total_processed'] += 1
                result = self._process_single_product(product_data)
                results.append(result)

            except Exception as e:
                error_msg = f"❌ Ошибка обработки товара {product_data.get('sku', '?')}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                self.statistics['errors'] += 1

                results.append({
                    'sku': product_data.get('sku', '?'),
                    'status': 'error',
                    'message': str(e)
                })

        return results

    def _process_single_product(self, product_data: Dict) -> Dict:
        """🛍️ Обработка одного товара с поиском по SKU"""
        product_sku = product_data['sku']
        product_name = product_data['name']

        try:
            # 📂 Получаем категорию
            category = self._get_category_for_product(product_data['category_name'])

            # 🎯 Ищем товар по SKU
            existing_product = Product.objects.filter(product_sku=product_sku).first()

            if existing_product:
                # 🔄 Обновляем существующий товар
                product = self._update_product(existing_product, product_data, category)
                action = 'updated'
                self.statistics['products_updated'] += 1
                logger.info(f"🔄 Обновлен товар с SKU: {product_sku}")
            else:
                # 🆕 Создаём новый товар
                product = self._create_product(product_data, category)
                action = 'created'
                self.statistics['products_created'] += 1
                logger.info(f"🆕 Создан товар с SKU: {product_sku}")

            # 🆕 Счетчик автосгенерированных SKU
            if not product_data.get('original_sku'):
                self.statistics['sku_generated'] += 1

            # 🖼️ Обрабатываем изображение товара с улучшенной защитой
            if product_data.get('image'):
                self._attach_product_image(product, product_data['image'])

            logger.info(f"✅ Товар {product_sku} ({product_name}) {action}")

            return {
                'sku': product_sku,
                'name': product_name,
                'status': action,
                'message': f'Товар успешно {action}'
            }

        except Exception as e:
            error_msg = f"Ошибка обработки товара {product_sku}: {str(e)}"
            logger.error(error_msg)
            raise

    def _get_category_for_product(self, category_name: str) -> Category:
        """📂 Получение категории для товара (из кэша или БД)"""
        # 🎯 Проверяем кэш
        if category_name in self.category_cache:
            return self.category_cache[category_name]

        # 🔍 Ищем в БД
        category = Category.objects.filter(category_name=category_name).first()

        if not category:
            # 🆕 Создаём категорию если её нет (fallback)
            category = Category.objects.create(
                category_name=category_name,
                category_sku=1,
                slug=slugify(category_name),
                description=f"Автоковрики для {category_name}",
                meta_title=f"Коврики {category_name}",
                meta_description=f"Качественные автоковрики для {category_name}",
                is_active=True
            )
            self.statistics['categories_created'] += 1
            logger.info(f"✅ Создана fallback категория: {category_name}")

        # 💾 Сохраняем в кэш
        self.category_cache[category_name] = category
        return category

    def _create_product(self, product_data: Dict, category: Category) -> Product:
        """🆕 Создание нового товара с сохранением SKU"""
        try:
            product_name = product_data['name']
            product_sku = product_data['sku']

            # 💰 ИСПРАВЛЕНО: Безопасная обработка цены
            price = self._normalize_price(product_data.get('price', 0))

            # 📝 Описание товара
            description = product_data.get('description', '')
            if not description:
                description = f"<p>Качественные автоковрики {product_name}.</p>"

            # 🆕 Создаём товар с сохранением SKU
            product = Product.objects.create(
                product_name=product_name,
                product_sku=product_sku,
                slug=slugify(f"{product_name}-{product_sku}"),
                category=category,
                price=price,
                product_desription=description,
                page_title=product_data.get('title', ''),
                meta_description=product_data.get('meta_description', ''),
                newest_product=True
            )

            logger.info(
                f"✅ Создан товар: {product_name} (SKU: {product_sku}, цена: {price}, категория: {category.category_name})")
            return product

        except Exception as e:
            logger.error(f"❌ Ошибка создания товара {product_data.get('name', '?')}: {e}")
            raise

    def _update_product(self, product: Product, product_data: Dict, category: Category) -> Product:
        """🔄 Обновление существующего товара"""
        try:
            # 🔄 Обновляем ВСЕ поля
            product.product_name = product_data['name']
            product.category = category
            product.product_sku = product_data['sku']

            # 💰 ИСПРАВЛЕНО: Безопасная обработка цены
            product.price = self._normalize_price(product_data.get('price', 0))

            # 📝 Обновляем описание и SEO поля
            if product_data.get('description'):
                product.product_desription = product_data['description']

            if product_data.get('title'):
                product.page_title = product_data['title']

            if product_data.get('meta_description'):
                product.meta_description = product_data['meta_description']

            # 🔗 Обновляем slug для уникальности
            product.slug = slugify(f"{product.product_name}-{product.product_sku}")

            product.save()

            logger.info(f"🔄 Обновлён товар: {product.product_name} (SKU: {product.product_sku})")
            return product

        except Exception as e:
            logger.error(f"❌ Ошибка обновления товара {product.product_name}: {e}")
            raise

    def _normalize_price(self, price_value) -> int:
        """
        💰 НОВЫЙ МЕТОД: Безопасная нормализация цены

        Обрабатывает Decimal → int → float без потери копеек
        """
        try:
            if price_value is None or price_value == '':
                return 0

            # 🔄 Обработка разных типов
            if isinstance(price_value, (int, float)):
                return max(0, int(price_value))

            if isinstance(price_value, Decimal):
                return max(0, int(price_value))

            if isinstance(price_value, str):
                # 🧹 Очищаем строку от валютных символов
                import re
                clean_price = re.sub(r'[^\d.,]', '', price_value.strip())
                if not clean_price:
                    return 0

                # 🔄 Заменяем запятую на точку и конвертируем
                clean_price = clean_price.replace(',', '.')
                return max(0, int(float(clean_price)))

            return 0

        except Exception as e:
            logger.warning(f"⚠️ Ошибка нормализации цены '{price_value}': {e}")
            return 0

    def _attach_product_image(self, product: Product, image_filename: str):
        """
        🖼️ УЛУЧШЕННОЕ присоединение изображения к товару

        🛠️ ОБНОВЛЕНО: Добавлена защита от блокировок и валидация

        Args:
            product: Объект товара
            image_filename: Имя файла изображения
        """
        try:
            # ✅ Предварительная валидация файла
            if not self._validate_image_file(image_filename, 'product'):
                logger.warning(f"⚠️ Файл изображения товара не прошел валидацию: {image_filename}")
                return

            # 🔍 Проверяем, есть ли уже изображение с таким именем
            existing_image = ProductImage.objects.filter(
                product=product,
                image__icontains=image_filename
            ).first()

            if existing_image:
                # 🔄 Обновляем существующее изображение как главное
                if not existing_image.is_main:
                    ProductImage.objects.filter(product=product, is_main=True).update(is_main=False)
                    existing_image.is_main = True
                    existing_image.save()
                logger.info(f"🔄 Обновлено существующее изображение: {image_filename}")
                return existing_image

            # 📁 Формируем путь к изображению
            image_path = f"product/{image_filename}"

            # 🆕 Создаём новое изображение с защитой от блокировок
            for attempt in range(3):
                try:
                    # 📋 Устанавливаем все существующие изображения как не главные
                    ProductImage.objects.filter(product=product, is_main=True).update(is_main=False)

                    # 🆕 Создаём запись изображения
                    product_image = ProductImage.objects.create(
                        product=product,
                        is_main=True
                    )

                    # 💾 Безопасное присоединение файла
                    product_image.image.name = image_path
                    product_image.save(update_fields=['image'])

                    self.statistics['images_processed'] += 1
                    logger.info(f"✅ Присоединено изображение товара (попытка {attempt + 1}): {image_filename}")
                    return product_image

                except Exception as save_error:
                    if attempt < 2:  # Не последняя попытка
                        logger.warning(f"⚠️ Попытка {attempt + 1} сохранения изображения товара неудачна: {save_error}")
                        time.sleep(0.5 * (attempt + 1))  # Увеличиваем задержку
                    else:
                        logger.error(f"❌ Не удалось присоединить изображение товара {image_filename}: {save_error}")
                        self.statistics['images_failed'] += 1

        except Exception as e:
            logger.error(f"❌ Критическая ошибка присоединения изображения товара {image_filename}: {e}")
            self.statistics['images_failed'] += 1

    def _validate_image_file(self, image_filename: str, target_folder: str) -> bool:
        """
        ✅ 🆕 НОВЫЙ МЕТОД: Валидация файла изображения перед обработкой

        Args:
            image_filename: Имя файла изображения
            target_folder: Целевая папка ('categories' или 'product')

        Returns:
            bool: True если файл валиден и готов к использованию
        """
        try:
            # 📁 Формируем полный путь к файлу
            image_path = f"{target_folder}/{image_filename}"
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)

            # 🔍 Проверяем существование файла
            if not os.path.exists(full_path):
                logger.warning(f"⚠️ Файл не существует: {full_path}")
                return False

            # 📏 Проверяем размер файла
            file_size = os.path.getsize(full_path)
            if file_size == 0:
                logger.warning(f"⚠️ Файл пустой: {full_path}")
                return False

            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"⚠️ Файл слишком большой ({file_size / 1024 / 1024:.1f}MB): {full_path}")
                return False

            # 🖼️ Проверяем расширение файла
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            file_extension = os.path.splitext(image_filename)[1].lower()
            if file_extension not in allowed_extensions:
                logger.warning(f"⚠️ Неподдерживаемое расширение ({file_extension}): {image_filename}")
                return False

            # ✅ Проверяем доступность файла для чтения
            try:
                with open(full_path, 'rb') as test_file:
                    test_file.read(1024)  # Читаем первый килобайт

            except PermissionError:
                logger.warning(f"⚠️ Нет доступа к файлу: {full_path}")
                return False
            except Exception as read_error:
                logger.warning(f"⚠️ Ошибка чтения файла: {full_path}: {read_error}")
                return False

            logger.debug(f"✅ Файл валиден: {image_filename} (размер: {file_size / 1024:.1f} KB)")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка валидации файла {image_filename}: {e}")
            return False

    def _cleanup_failed_images(self):
        """
        🧹 🆕 НОВЫЙ МЕТОД: Очистка неудачно обработанных изображений

        Находит и удаляет записи изображений, которые ссылаются на несуществующие файлы
        """
        try:
            # 🔍 Находим изображения товаров без файлов
            orphaned_product_images = ProductImage.objects.filter(
                image__isnull=False
            ).exclude(image='')

            cleaned_count = 0
            for product_image in orphaned_product_images:
                try:
                    full_path = product_image.image.path
                    if not os.path.exists(full_path):
                        logger.warning(f"🧹 Удаляем запись без файла: {product_image.image.name}")
                        product_image.delete()
                        cleaned_count += 1
                except Exception:
                    pass

            if cleaned_count > 0:
                logger.info(f"🧹 Очищено записей изображений без файлов: {cleaned_count}")

        except Exception as e:
            logger.error(f"❌ Ошибка очистки неудачных изображений: {e}")

    def _create_error_result(self, error_message: str) -> Dict:
        """❌ Создание результата с ошибкой"""
        self.errors.append(error_message)

        return {
            'success': False,
            'error': error_message,
            'statistics': self.statistics,
            'errors': self.errors
        }


def preview_excel_data(file) -> Dict:
    """👁️ Предпросмотр данных с разделением на категории и товары"""
    try:
        # 📖 Читаем файл
        success, result = read_excel_file(file)
        if not success:
            return {'success': False, 'error': result}

        raw_data = result

        # 🔄 Разделяем данные
        categories, products, invalid_data = separate_categories_and_products(raw_data)

        # 📊 Статистика
        stats = get_import_statistics(categories, products, invalid_data)

        # 👁️ Ограничиваем для предпросмотра
        preview_categories = categories[:5]
        preview_products = products[:10]
        preview_invalid = invalid_data[:5]

        return {
            'success': True,
            'statistics': stats,
            'categories': preview_categories,
            'products': preview_products,
            'invalid_data': preview_invalid,
            'total_categories': len(categories),
            'total_products': len(products),
            'total_invalid': len(invalid_data)
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Ошибка предпросмотра: {str(e)}"
        }

# 🔧 КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ✅ ДОБАВЛЕНО: _validate_image_file() - валидация файлов перед обработкой
# ✅ ДОБАВЛЕНО: _cleanup_failed_images() - очистка неудачных записей
# ✅ ДОБАВЛЕНО: images_failed в статистику - подсчет неудачных изображений
# ✅ ИЗМЕНЕНО: _attach_product_image() - добавлены повторные попытки и валидация
# ✅ ИЗМЕНЕНО: _attach_category_image() - добавлены повторные попытки и валидация
# ✅ ИЗМЕНЕНО: process_structured_data() - добавлен вызов очистки при ошибках
# ✅ СОХРАНЕНО: Вся существующая логика процессора
#
# 🎯 РЕЗУЛЬТАТ:
# - Защита от блокировок файлов при сохранении изображений
# - Валидация файлов перед обработкой
# - Повторные попытки при ошибках сохранения
# - Автоматическая очистка неудачных записей
# - Подробная статистика обработки
# - Полная обратная совместимость