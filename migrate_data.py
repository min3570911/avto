"""
Скрипт для переноса справочных данных из старой БД в новую
"""

import os
import sys
import sqlite3
import django
from datetime import datetime

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avtokovriki.settings')
django.setup()

# Импорт моделей
from blog.models import Category
from django.contrib.auth.models import User

# Предположительные пути к моделям товаров и других справочников
# Измените на ваши актуальные пути к моделям
try:
    from products.models import FloorMatProduct, InstallationOption, MatColor, BorderColor
except ImportError:
    print("ВНИМАНИЕ: Не удалось импортировать модели продуктов. Проверьте пути импорта.")
    FloorMatProduct = InstallationOption = MatColor = BorderColor = None


def migrate_blog_categories(old_conn, new_conn):
    """Перенос категорий блога из старой БД в новую"""
    print("\n=== Перенос категорий блога ===")

    # Проверка существования таблицы в старой БД
    cursor = old_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blog_category'")
    if not cursor.fetchone():
        print("Таблица blog_category отсутствует в старой БД. Пропуск.")
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
                print(f"[ПРОПУСК] Категория '{name}' уже существует")
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
            print(f"[УСПЕХ] Категория '{name}' перенесена")

        print(f"Всего перенесено категорий: {len(categories)}")

    except Exception as e:
        print(f"Ошибка при переносе категорий: {e}")


def migrate_installation_options(old_conn, new_conn):
    """Перенос типов комплектаций из старой БД в новую"""
    if InstallationOption is None:
        print("\n[ПРОПУСК] Модель InstallationOption не найдена")
        return

    print("\n=== Перенос типов комплектаций ===")

    # Проверка существования таблицы в старой БД
    cursor = old_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_installationoption'")
    if not cursor.fetchone():
        print("Таблица products_installationoption отсутствует в старой БД. Пропуск.")
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
                print(f"[ПРОПУСК] Опция комплектации '{name}' уже существует")
                continue

            option = InstallationOption(
                id=opt_id,  # Сохраняем тот же ID
                name=name,
                extra_price=extra_price or 0
            )
            option.save(force_insert=True)  # Сохраняем с тем же ID
            print(f"[УСПЕХ] Опция комплектации '{name}' перенесена")

        print(f"Всего перенесено опций комплектации: {len(options)}")

    except Exception as e:
        print(f"Ошибка при переносе типов комплектаций: {e}")


def migrate_colors(old_conn, new_conn):
    """Перенос цветов из старой БД в новую"""
    if MatColor is None or BorderColor is None:
        print("\n[ПРОПУСК] Модели цветов не найдены")
        return

    print("\n=== Перенос цветов ковриков ===")

    # Проверка существования таблицы в старой БД
    cursor = old_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_matcolor'")
    if not cursor.fetchone():
        print("Таблица products_matcolor отсутствует в старой БД. Пропуск.")
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
                    print(f"[ПРОПУСК] Цвет коврика '{name}' уже существует")
                    continue

                mat_color = MatColor(
                    id=color_id,  # Сохраняем тот же ID
                    name=name,
                    code=code
                )
                mat_color.save(force_insert=True)  # Сохраняем с тем же ID
                print(f"[УСПЕХ] Цвет коврика '{name}' перенесен")

            print(f"Всего перенесено цветов ковриков: {len(mat_colors)}")

        except Exception as e:
            print(f"Ошибка при переносе цветов ковриков: {e}")

    print("\n=== Перенос цветов окантовки ===")

    # Проверка существования таблицы в старой БД
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_bordercolor'")
    if not cursor.fetchone():
        print("Таблица products_bordercolor отсутствует в старой БД. Пропуск.")
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
                print(f"[ПРОПУСК] Цвет окантовки '{name}' уже существует")
                continue

            border_color = BorderColor(
                id=color_id,  # Сохраняем тот же ID
                name=name,
                code=code
            )
            border_color.save(force_insert=True)  # Сохраняем с тем же ID
            print(f"[УСПЕХ] Цвет окантовки '{name}' перенесен")

        print(f"Всего перенесено цветов окантовки: {len(border_colors)}")

    except Exception as e:
        print(f"Ошибка при переносе цветов окантовки: {e}")


def migrate_products(old_conn, new_conn):
    """Перенос товаров из старой БД в новую"""
    if FloorMatProduct is None or InstallationOption is None:
        print("\n[ПРОПУСК] Модели продуктов не найдены")
        return

    print("\n=== Перенос товаров (автоковриков) ===")

    # Проверка существования таблицы в старой БД
    cursor = old_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_floormatproduct'")
    if not cursor.fetchone():
        print("Таблица products_floormatproduct отсутствует в старой БД. Пропуск.")
        return

    try:
        # Получаем схему таблицы
        cursor.execute("PRAGMA table_info(products_floormatproduct)")
        columns = [col[1] for col in cursor.fetchall()]
        required_columns = ['id', 'code', 'name', 'price']

        # Проверка наличия обязательных колонок
        if not all(col in columns for col in required_columns):
            print("В таблице products_floormatproduct отсутствуют обязательные колонки. Пропуск.")
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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_floormatproduct_installation_options'")
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
                print(f"Ошибка при получении опций комплектации: {e}")

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
                print(f"[ПРОПУСК] Товар '{code}' уже существует")
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
                            print(f"[ОШИБКА] Опция комплектации с ID {opt_id} не найдена")

                print(f"[УСПЕХ] Товар '{code}' перенесен")

            except Exception as e:
                print(f"[ОШИБКА] Не удалось перенести товар '{code}': {e}")

        print(f"Всего перенесено товаров: {len(products)}")

    except Exception as e:
        print(f"Ошибка при переносе товаров: {e}")


def main():
    """Основная функция переноса данных"""
    print("\n" + "="*70)
    print("Начинаем перенос данных из старой БД в новую...")
    print("="*70)

    # Проверяем наличие старой базы данных
    old_db_path = 'old_db.sqlite3'
    if not os.path.exists(old_db_path):
        print(f"ОШИБКА: Файл {old_db_path} не найден!")
        print("Пожалуйста, поместите старую базу данных в корневую папку проекта с именем old_db.sqlite3")
        sys.exit(1)

    # Проверяем наличие новой базы данных
    new_db_path = 'db.sqlite3'
    if not os.path.exists(new_db_path):
        print(f"ОШИБКА: Файл {new_db_path} не найден!")
        print("Пожалуйста, создайте новую базу данных, выполнив команду 'python manage.py migrate'")
        sys.exit(1)

    # Подключаемся к базам данных
    old_conn = sqlite3.connect(old_db_path)
    new_conn = sqlite3.connect(new_db_path)

    try:
        # Переносим данные
        migrate_blog_categories(old_conn, new_conn)
        migrate_installation_options(old_conn, new_conn)
        migrate_colors(old_conn, new_conn)
        migrate_products(old_conn, new_conn)

        print("\n" + "="*70)
        print("✅ Перенос данных успешно завершен!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ОШИБКА при переносе данных: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Закрываем соединения с базами данных
        old_conn.close()
        new_conn.close()


if __name__ == "__main__":
    main()