# 📁 products/import_processor.py
# 🛠️ ПРАВИЛЬНАЯ версия процессора с двойной обработкой (категории → товары)
# ✅ Сначала создаём категории, потом товары с привязкой

import logging
from typing import Dict, List, Tuple, Optional
from django.db import transaction, IntegrityError
from django.utils.text import slugify
from django.core.files import File
from django.conf import settings
import os
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
    🚀 Процессор импорта с двойной логикой: категории + товары
    """

    def __init__(self):
        self.statistics = {
            'total_processed': 0,
            'categories_created': 0,
            'categories_updated': 0,
            'products_created': 0,
            'products_updated': 0,
            'errors': 0,
            'images_processed': 0
        }
        self.errors = []
        self.category_cache = {}  # 💾 Кэш созданных категорий

    def process_excel_file(self, file) -> Dict:
        """
        📊 Основной метод обработки Excel файла с двойной логикой

        Args:
            file: Загруженный Excel файл

        Returns:
            Dict: Результаты импорта с детальной статистикой
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

            # 📊 Статистика перед импортом
            import_stats = get_import_statistics(categories, products, invalid_data)

            # 🚀 Выполняем импорт в транзакции
            with transaction.atomic():
                # 📂 Сначала импортируем категории
                category_results = self._import_categories(categories)

                # 🛍️ Затем импортируем товары
                product_results = self._import_products(products)

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
            error_msg = f"❌ Критическая ошибка при импорте: {str(e)}"
            logger.error(error_msg)
            return self._create_error_result(error_msg)

    def _import_categories(self, categories_data: List[Dict]) -> List[Dict]:
        """
        📂 Импорт категорий с созданием моделей Category

        Args:
            categories_data: Список данных категорий

        Returns:
            List[Dict]: Результаты импорта категорий
        """
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
        """
        📂 Обработка одной категории

        Args:
            category_data: Данные категории

        Returns:
            Dict: Результат обработки
        """
        category_name = category_data['category_name']

        try:
            # 🔍 Проверяем, существует ли категория
            existing_category = Category.objects.filter(category_name=category_name).first()

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

            # 🖼️ Обрабатываем изображение категории
            if category_data.get('image'):
                self._process_category_image(category, category_data['image'])

            # 💾 Добавляем в кэш для товаров
            self.category_cache[category_name] = category

            logger.info(f"✅ Категория {category_name} {action}")

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
        """
        🆕 Создание новой категории

        Args:
            category_data: Данные категории

        Returns:
            Category: Созданная категория
        """
        try:
            category_name = category_data['category_name']

            # 📝 Подготавливаем данные
            description = category_data.get('description', '') or f"Автоковрики для {category_name}"
            title = category_data.get('title', '') or f"Автоковрики {category_name}"
            meta_description = category_data.get('meta_description', '') or \
                               f"Качественные автоковрики для {category_name}. Большой выбор, доставка по Беларуси."

            # 🆕 Создаём категорию
            category = Category.objects.create(
                category_name=category_name,
                slug=slugify(category_name),
                description=description,
                page_title=title,
                meta_title=title[:60] if title else f"Коврики {category_name}",
                meta_description=meta_description[:160],
                is_active=True
            )

            logger.info(f"✅ Создана категория: {category_name}")
            return category

        except Exception as e:
            logger.error(f"❌ Ошибка создания категории {category_data.get('category_name', '?')}: {e}")
            raise

    def _update_category(self, category: Category, category_data: Dict) -> Category:
        """
        🔄 Обновление существующей категории

        Args:
            category: Существующая категория
            category_data: Новые данные

        Returns:
            Category: Обновлённая категория
        """
        try:
            # 🔄 Обновляем поля если они заполнены
            if category_data.get('description'):
                category.description = category_data['description']

            if category_data.get('title'):
                category.page_title = category_data['title']
                category.meta_title = category_data['title'][:60]

            if category_data.get('meta_description'):
                category.meta_description = category_data['meta_description'][:160]

            category.save()

            logger.info(f"🔄 Обновлена категория: {category.category_name}")
            return category

        except Exception as e:
            logger.error(f"❌ Ошибка обновления категории {category.category_name}: {e}")
            raise

    def _import_products(self, products_data: List[Dict]) -> List[Dict]:
        """
        🛍️ Импорт товаров с привязкой к категориям

        Args:
            products_data: Список данных товаров

        Returns:
            List[Dict]: Результаты импорта товаров
        """
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
        """
        🛍️ Обработка одного товара

        Args:
            product_data: Данные товара

        Returns:
            Dict: Результат обработки товара
        """
        product_sku = product_data['sku']
        product_name = product_data['name']

        try:
            # 📂 Получаем категорию
            category = self._get_category_for_product(product_data['category_name'])

            # 🔍 Проверяем, существует ли товар (ищем по slug)
            product_slug = slugify(product_name)
            existing_product = Product.objects.filter(slug=product_slug).first()

            if existing_product:
                # 🔄 Обновляем существующий товар
                product = self._update_product(existing_product, product_data, category)
                action = 'updated'
                self.statistics['products_updated'] += 1
            else:
                # 🆕 Создаём новый товар
                product = self._create_product(product_data, category)
                action = 'created'
                self.statistics['products_created'] += 1

            # 🖼️ Обрабатываем изображение товара
            if product_data.get('image'):
                self._process_product_image(product, product_data['image'])

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
        """
        📂 Получение категории для товара (из кэша или БД)

        Args:
            category_name: Название категории

        Returns:
            Category: Объект категории
        """
        # 🎯 Проверяем кэш
        if category_name in self.category_cache:
            return self.category_cache[category_name]

        # 🔍 Ищем в БД
        category = Category.objects.filter(category_name=category_name).first()

        if not category:
            # 🆕 Создаём категорию если её нет (fallback)
            category = Category.objects.create(
                category_name=category_name,
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
        """
        🆕 Создание нового товара

        Args:
            product_data: Данные товара
            category: Категория товара

        Returns:
            Product: Созданный товар
        """
        try:
            product_name = product_data['name']
            price = max(0, int(product_data.get('price', 0)))

            # 📝 Описание товара
            description = product_data.get('description', '')
            if not description:
                description = f"<p>Качественные автоковрики {product_name}.</p>"

            # 🆕 Создаём товар
            product = Product.objects.create(
                product_name=product_name,
                slug=slugify(product_name),
                category=category,
                price=price,
                product_desription=description,
                newest_product=True
            )

            logger.info(f"✅ Создан товар: {product_name} (цена: {price}, категория: {category.category_name})")
            return product

        except Exception as e:
            logger.error(f"❌ Ошибка создания товара {product_data.get('name', '?')}: {e}")
            raise

    def _update_product(self, product: Product, product_data: Dict, category: Category) -> Product:
        """
        🔄 Обновление существующего товара
        """
        try:
            # 🔄 Обновляем поля
            product.product_name = product_data['name']
            product.category = category

            # 💰 Обновляем цену только если она больше 0
            new_price = max(0, int(product_data.get('price', 0)))
            if new_price > 0:
                product.price = new_price

            # 📝 Обновляем описание если оно есть
            if product_data.get('description'):
                product.product_desription = product_data['description']

            product.save()

            logger.info(f"🔄 Обновлён товар: {product.product_name}")
            return product

        except Exception as e:
            logger.error(f"❌ Ошибка обновления товара {product.product_name}: {e}")
            raise

    def _process_product_image(self, product: Product, image_filename: str):
        """🖼️ Обработка изображения товара"""
        try:
            image_path = os.path.join(settings.MEDIA_ROOT, 'product', image_filename)

            if not os.path.exists(image_path):
                logger.warning(f"⚠️ Изображение не найдено: {image_path}")
                return

            # 🔍 Проверяем существующее изображение
            existing_image = ProductImage.objects.filter(
                product=product,
                image__icontains=image_filename
            ).first()

            if existing_image:
                if not existing_image.is_main:
                    ProductImage.objects.filter(product=product, is_main=True).update(is_main=False)
                    existing_image.is_main = True
                    existing_image.save()
                return existing_image

            # 🆕 Создаём новое изображение
            with open(image_path, 'rb') as f:
                ProductImage.objects.filter(product=product, is_main=True).update(is_main=False)

                product_image = ProductImage.objects.create(product=product, is_main=True)
                product_image.image.save(image_filename, File(f), save=True)

            self.statistics['images_processed'] += 1
            logger.info(f"✅ Добавлено изображение: {image_filename}")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки изображения {image_filename}: {e}")

    def _process_category_image(self, category: Category, image_filename: str):
        """🖼️ Обработка изображения категории"""
        try:
            image_path = os.path.join(settings.MEDIA_ROOT, 'categories', image_filename)

            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    category.category_image.save(image_filename, File(f), save=True)
                logger.info(f"✅ Добавлено изображение категории: {image_filename}")
            else:
                logger.warning(f"⚠️ Изображение категории не найдено: {image_path}")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки изображения категории {image_filename}: {e}")

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
    """
    👁️ Предпросмотр данных с разделением на категории и товары
    """
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

# 🚀 ОСНОВНЫЕ ИЗМЕНЕНИЯ:
# ✅ Двойная обработка: сначала категории, потом товары
# ✅ Правильная привязка товаров к категориям через category_name
# ✅ Кэширование категорий для производительности
# ✅ Отдельная обработка изображений категорий и товаров
# ✅ Обновлённая статистика с разделением типов
# ✅ Fallback создание категорий для товаров без категории