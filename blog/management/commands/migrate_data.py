from django.core.management.base import BaseCommand
import os
import sys
import sqlite3
from datetime import datetime


class Command(BaseCommand):
    help = 'Переносит данные из старой SQLite базы в новую'

    def add_arguments(self, parser):
        parser.add_argument('--old-db', default='old_db.sqlite3', help='Путь к старой базе данных')
        parser.add_argument('--new-db', default='db.sqlite3', help='Путь к новой базе данных')

    def handle(self, *args, **options):
        old_db_path = options['old_db']
        new_db_path = options['new_db']

        # Проверяем наличие баз данных
        if not os.path.exists(old_db_path):
            self.stdout.write(self.style.ERROR(f"Ошибка: файл {old_db_path} не найден!"))
            return

        if not os.path.exists(new_db_path):
            self.stdout.write(self.style.ERROR(f"Ошибка: файл {new_db_path} не найден!"))
            return

        # Подключаемся к базам данных
        old_conn = sqlite3.connect(old_db_path)
        new_conn = sqlite3.connect(new_db_path)

        try:
            # Переносим данные
            self.migrate_blog_categories(old_conn, new_conn)
            self.migrate_installation_options(old_conn, new_conn)
            self.migrate_colors(old_conn, new_conn)
            self.migrate_products(old_conn, new_conn)

            self.stdout.write(self.style.SUCCESS("\n✅ Перенос данных успешно завершен!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ ОШИБКА при переносе данных: {e}"))
            import traceback
            traceback.print_exc()
        finally:
            # Закрываем соединения с базами данных
            old_conn.close()
            new_conn.close()

    def migrate_blog_categories(self, old_conn, new_conn):
        """Перенос категорий блога из старой БД в новую"""
        from blog.models import Category

        self.stdout.write("\n=== Перенос категорий блога ===")

        # Проверка существования таблицы в старой БД
        cursor = old_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blog_category'")
        if not cursor.fetchone():
            self.stdout.write("Таблица blog_category отсутствует в старой БД. Пропуск.")
            return

        # Получаем данные из старой БД
        cursor.execute("PRAGMA table_info(blog_category)")
        columns = [col[1] for col in cursor.fetchall()]

        # Формируем запрос на основе существующих колонок
        query = "SELECT id"
        for col in ['name', 'slug', 'description', 'image', 'sort_order', 'created_at', 'updated_at']:
            if col in columns:
                query += f", {col}"
            else:
                query += ", NULL"
        query += " FROM blog_category"

        try:
            cursor.execute(query)
            categories = cursor.fetchall()

            # Вставляем данные в новую БД
            for cat in categories:
                cat_id = cat[0]
                cat_data = list(cat[1:])

                # Подготовка данных с учетом возможных отсутствующих колонок
                name = cat_data[0] or "Без названия"
                slug = cat_data[1] or f"category-{cat_id}"
                description = cat_data[2] or ""
                image = cat_data[3]
                sort_order = cat_data[4] or 0
                created_at = cat_data[5] or datetime.now()
                updated_at = cat_data[6] or datetime.now()

                # Проверка, существует ли уже такая категория
                if Category.objects.filter(slug=slug).exists():
                    self.stdout.write(f"[ПРОПУСК] Категория '{name}' уже существует")
                    continue

                category = Category(
                    id=cat_id,  # Сохраняем тот же ID
                    name=name,
                    slug=slug,
                    description=description,
                    image=image if image else None,
                    sort_order=sort_order,
                    created_at=created_at,
                    updated_at=updated_at
                )
                category.save(force_insert=True)  # Сохраняем с тем же ID
                self.stdout.write(self.style.SUCCESS(f"[УСПЕХ] Категория '{name}' перенесена"))

            self.stdout.write(f"Всего перенесено категорий: {len(categories)}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при переносе категорий: {e}"))

    def migrate_installation_options(self, old_conn, new_conn):
        """Перенос типов комплектаций из старой БД в новую"""
        self.stdout.write("\n=== Перенос типов комплектаций ===")

        # Импортируем модель, с проверкой на ее существование
        try:
            from products.models import InstallationOption
        except ImportError:
            self.stdout.write("[ПРОПУСК] Модель InstallationOption не найдена")
            return

        # Проверка существования таблицы в старой БД
        cursor = old_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_installationoption'")
        if not cursor.fetchone():
            self.stdout.write("Таблица products_installationoption отсутствует в старой БД. Пропуск.")
            return

        # Получаем данные из старой БД
        try:
            cursor.execute("SELECT id, name, extra_price FROM products_installationoption")
            options = cursor.fetchall()

            # Вставляем данные в новую БД
            for opt in options:
                opt_id, name, extra_price = opt

                # Проверка, существует ли уже такая опция
                if InstallationOption.objects.filter(name=name).exists():
                    self.stdout.write(f"[ПРОПУСК] Опция комплектации '{name}' уже существует")
                    continue

                option = InstallationOption(
                    id=opt_id,  # Сохраняем тот же ID
                    name=name,
                    extra_price=extra_price or 0
                )
                option.save(force_insert=True)  # Сохраняем с тем же ID
                self.stdout.write(self.style.SUCCESS(f"[УСПЕХ] Опция комплектации '{name}' перенесена"))

            self.stdout.write(f"Всего перенесено опций комплектации: {len(options)}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при переносе типов комплектаций: {e}"))

    def migrate_colors(self, old_conn, new_conn):
        """Перенос цветов из старой БД в новую"""
        self.stdout.write("\n=== Перенос цветов ===")

        # Импортируем модели цветов, с проверкой на их существование
        try:
            from products.models import MatColor, BorderColor
            mat_color_available = True
            border_color_available = True
        except ImportError:
            self.stdout.write("[ПРОПУСК] Модели цветов не найдены")
            return

        # Перенос цветов ковриков
        if mat_color_available:
            self.stdout.write("\n=== Перенос цветов ковриков ===")

            # Проверка существования таблицы в старой БД
            cursor = old_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_matcolor'")
            if not cursor.fetchone():
                self.stdout.write("Таблица products_matcolor отсутствует в старой БД. Пропуск.")
            else:
                try:
                    # Получаем данные о цветах ковриков из старой БД
                    cursor.execute("SELECT id, name, code FROM products_matcolor")
                    mat_colors = cursor.fetchall()

                    # Вставляем данные о цветах ковриков в новую БД
                    for color in mat_colors:
                        color_id, name, code = color

                        # Проверка, существует ли уже такой цвет коврика
                        if MatColor.objects.filter(code=code).exists():
                            self.stdout.write(f"[ПРОПУСК] Цвет коврика '{name}' уже существует")
                            continue

                        mat_color = MatColor(
                            id=color_id,  # Сохраняем тот же ID
                            name=name,
                            code=code
                        )
                        mat_color.save(force_insert=True)  # Сохраняем с тем же ID
                        self.stdout.write(self.style.SUCCESS(f"[УСПЕХ] Цвет коврика '{name}' перенесен"))

                    self.stdout.write(f"Всего перенесено цветов ковриков: {len(mat_colors)}")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка при переносе цветов ковриков: {e}"))

        # Перенос цветов окантовки
        if border_color_available:
            self.stdout.write("\n=== Перенос цветов окантовки ===")

            # Проверка существования таблицы в старой БД
            cursor = old_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_bordercolor'")
            if not cursor.fetchone():
                self.stdout.write("Таблица products_bordercolor отсутствует в старой БД. Пропуск.")
                return

            try:
                # Получаем данные о цветах окантовки из старой БД
                cursor.execute("SELECT id, name, code FROM products_bordercolor")
                border_colors = cursor.fetchall()

                # Вставляем данные о цветах окантовки в новую БД
                for color in border_colors:
                    color_id, name, code = color

                    # Проверка, существует ли уже такой цвет окантовки
                    if BorderColor.objects.filter(code=code).exists():
                        self.stdout.write(f"[ПРОПУСК] Цвет окантовки '{name}' уже существует")
                        continue

                    border_color = BorderColor(
                        id=color_id,  # Сохраняем тот же ID
                        name=name,
                        code=code
                    )
                    border_color.save(force_insert=True)  # Сохраняем с тем же ID
                    self.stdout.write(self.style.SUCCESS(f"[УСПЕХ] Цвет окантовки '{name}' перенесен"))

                self.stdout.write(f"Всего перенесено цветов окантовки: {len(border_colors)}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка при переносе цветов окантовки: {e}"))

    def migrate_products(self, old_conn, new_conn):
        """Перенос товаров из старой БД в новую"""
        self.stdout.write("\n=== Перенос товаров (автоковриков) ===")

        # Импортируем модели продуктов, с проверкой на их существование
        try:
            from products.models import FloorMatProduct, InstallationOption
        except ImportError:
            self.stdout.write("[ПРОПУСК] Модели продуктов не найдены")
            return

        # Проверка существования таблицы в старой БД
        cursor = old_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_floormatproduct'")
        if not cursor.fetchone():
            self.stdout.write("Таблица products_floormatproduct отсутствует в старой БД. Пропуск.")
            return

        try:
            # Получаем схему таблицы
            cursor.execute("PRAGMA table_info(products_floormatproduct)")
            columns = [col[1] for col in cursor.fetchall()]
            required_columns = ['id', 'code', 'name', 'price']

            # Проверка наличия обязательных колонок
            if not all(col in columns for col in required_columns):
                self.stdout.write("В таблице products_floormatproduct отсутствуют обязательные колонки. Пропуск.")
                return

            # Формируем запрос на основе существующих колонок
            query = "SELECT id, code, name, price"
            optional_columns = [
                'description', 'mat_color_id', 'border_color_id',
                'crossbar', 'heelpad', 'created', 'updated', 'discount_price'
            ]

            for col in optional_columns:
                if col in columns:
                    query += f", {col}"
                else:
                    query += ", NULL"
            query += " FROM products_floormatproduct"

            cursor.execute(query)
            products = cursor.fetchall()

            # Получаем связи товаров с опциями комплектации, если такая таблица существует
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='products_floormatproduct_installation_options'")
            product_options = {}

            if cursor.fetchone():
                try:
                    cursor.execute("""
                        SELECT floormatproduct_id, installationoption_id
                        FROM products_floormatproduct_installation_options
                    """)
                    options_data = cursor.fetchall()

                    for prod_id, opt_id in options_data:
                        if prod_id not in product_options:
                            product_options[prod_id] = []
                        product_options[prod_id].append(opt_id)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка при получении опций комплектации: {e}"))

            # Вставляем данные в новую БД
            for prod in products:
                values = list(prod)
                prod_id = values[0]
                code = values[1]
                name = values[2]
                price = values[3]

                # Получаем дополнительные поля с учетом возможного отсутствия
                idx = 4
                description = values[idx] if idx < len(values) else ""
                idx += 1
                mat_color_id = values[idx] if idx < len(values) else None
                idx += 1
                border_color_id = values[idx] if idx < len(values) else None
                idx += 1
                crossbar = values[idx] if idx < len(values) else False
                idx += 1
                heelpad = values[idx] if idx < len(values) else False
                idx += 1
                created = values[idx] if idx < len(values) else datetime.now()
                idx += 1
                updated = values[idx] if idx < len(values) else datetime.now()
                idx += 1
                discount_price = values[idx] if idx < len(values) else None

                # Проверка существования товара
                if FloorMatProduct.objects.filter(code=code).exists():
                    self.stdout.write(f"[ПРОПУСК] Товар '{code}' уже существует")
                    continue

                try:
                    # Создаем продукт
                    product = FloorMatProduct(
                        id=prod_id,
                        code=code,
                        name=name,
                        price=price,
                        description=description or "",
                        mat_color_id=mat_color_id,
                        border_color_id=border_color_id,
                        crossbar=crossbar or False,
                        heelpad=heelpad or False,
                        created=created,
                        updated=updated
                    )

                    # Добавляем discount_price, если это поле существует в модели
                    if hasattr(product, 'discount_price') and discount_price is not None:
                        product.discount_price = discount_price

                    product.save(force_insert=True)

                    # Добавляем опции комплектации
                    if prod_id in product_options:
                        for opt_id in product_options[prod_id]:
                            try:
                                option = InstallationOption.objects.get(id=opt_id)
                                product.installation_options.add(option)
                            except InstallationOption.DoesNotExist:
                                self.stdout.write(
                                    self.style.ERROR(f"[ОШИБКА] Опция комплектации с ID {opt_id} не найдена"))

                    self.stdout.write(self.style.SUCCESS(f"[УСПЕХ] Товар '{code}' перенесен"))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"[ОШИБКА] Не удалось перенести товар '{code}': {e}"))

            self.stdout.write(f"Всего перенесено товаров: {len(products)}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при переносе товаров: {e}"))