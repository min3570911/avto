import os
import django
import random
import uuid
from django.db import transaction

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecomm.settings")
django.setup()

# Импортируем модель напрямую из вашего проекта
from products.models import Product, Category


def get_unique_slug(base_name):
    """Генерирует гарантированно уникальный slug на основе UUID"""
    random_uuid = str(uuid.uuid4())[:8]
    return f"{base_name.lower().replace(' ', '-')}-{random_uuid}"


# Печатаем структуру моделей для диагностики
print("Структура модели Category:")
print(f"Поля модели: {[field.name for field in Category._meta.fields]}")

print("\nСтруктура модели Product:")
print(f"Поля модели: {[field.name for field in Product._meta.fields]}")

try:
    with transaction.atomic():
        # Обрабатываем существующие категории
        existing_categories = list(Category.objects.all())
        print(f"\nНайдено существующих категорий: {len(existing_categories)}")
        for cat in existing_categories:
            print(f"UID: {cat.uid}, Название: {cat.category_name}, Slug: '{cat.slug}'")

            # Если slug пустой, добавляем его
            if not cat.slug:
                cat.slug = get_unique_slug(cat.category_name)
                cat.save()
                print(f"  → Обновлен slug: '{cat.slug}'")

        # Создаем новые категории если необходимо
        category_names = ["Автоковрики", "Аксессуары", "Чехлы"]
        category_objects = []

        for name in category_names:
            # Ищем категорию по имени
            category = Category.objects.filter(category_name=name).first()

            if category:
                print(f"Категория '{name}' уже существует")
                category_objects.append(category)
            else:
                # Создаем новую категорию с уникальным slug
                unique_slug = get_unique_slug(name)
                category = Category.objects.create(
                    category_name=name,
                    slug=unique_slug
                )
                print(f"Создана новая категория: {name} со slug: '{unique_slug}'")
                category_objects.append(category)

        # Создаем продукты
        products_data = [
            {
                "product_name": "Автоковрик универсальный EVA",
                "price": 2500,
                "product_desription": "Универсальный автомобильный коврик из материала EVA."
            },
            {
                "product_name": "Коврик EVA для седана",
                "price": 3200,
                "product_desription": "Специальный коврик из материала EVA для седанов."
            },
            {
                "product_name": "Резиновый коврик для багажника",
                "price": 1800,
                "product_desription": "Прочный резиновый коврик для защиты багажника от грязи."
            },
            {
                "product_name": "Премиум автоковрик",
                "price": 4500,
                "product_desription": "Премиальный автоковрик с повышенной износостойкостью."
            },
            {
                "product_name": "Текстильные коврики (комплект)",
                "price": 2900,
                "product_desription": "Комплект текстильных ковриков для салона автомобиля."
            }
        ]

        products_created = 0
        for data in products_data:
            # Проверяем, существует ли продукт с таким именем
            if Product.objects.filter(product_name=data["product_name"]).exists():
                print(f"Продукт уже существует: {data['product_name']}")
                continue

            # Создаем уникальный slug
            unique_slug = get_unique_slug(data["product_name"])

            # Создаем продукт
            product = Product.objects.create(
                product_name=data["product_name"],
                price=data["price"],
                product_desription=data["product_desription"],
                slug=unique_slug,
                category=random.choice(category_objects)
            )
            print(f"Создан продукт: {product.product_name} (slug: '{product.slug}')")
            products_created += 1

        print(f"\nВсего создано: {products_created} продуктов")
        print(f"Всего категорий: {Category.objects.count()}")
        print(f"Всего продуктов: {Product.objects.count()}")

except Exception as e:
    print(f"Произошла ошибка: {str(e)}")
    import traceback

    traceback.print_exc()