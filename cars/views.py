# 📁 cars/views.py - ИСПРАВЛЕННЫЕ View функции для раздела автомобилей
# 🚗 Представления для каталога автомобилей с использованием proxy-моделей
# ✅ ИСПРАВЛЕНО: Завершены все неполные функции

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import CarCategory, CarProduct
from products.models import Color
from products.views import (
    add_to_cart,  # 🛒 Функция добавления в корзину
    add_to_wishlist,  # ❤️ Функция добавления в избранное
)


def car_category_list(request):
    """
    🚗 Главная страница раздела "Автомобили" - список всех категорий авто
    """
    # 📂 Получаем только корневые категории авто (без родителей)
    root_categories = CarCategory.objects.filter(
        parent__isnull=True,
        is_active=True
    ).order_by('display_order', 'category_name')

    # 📊 Статистика по автомобилям
    total_car_products = CarProduct.objects.count()
    newest_cars = CarProduct.objects.filter(newest_product=True)[:6]

    context = {
        'categories': root_categories,
        'total_products': total_car_products,
        'newest_products': newest_cars,
        'page_title': 'Автомобильные коврики',
        'page_description': 'Каталог ковриков для автомобилей различных марок и моделей',
        'section_type': 'cars',  # 🏷️ Идентификатор раздела
    }

    return render(request, 'cars/category_list.html', context)


def car_product_list(request, slug):
    """
    🚗 Список товаров в конкретной категории автомобилей
    ✅ ИСПРАВЛЕНО: Завершена функция
    """
    # 📂 Получаем категорию авто по slug
    category = get_object_or_404(CarCategory, slug=slug, is_active=True)

    # 📦 Получаем все товары этой категории и подкатегорий
    if category.children.exists():
        # Если есть подкатегории, показываем товары из всех подкатегорий
        subcategory_ids = list(category.children.values_list('id', flat=True))
        subcategory_ids.append(category.id)
        products = CarProduct.objects.filter(category_id__in=subcategory_ids)
    else:
        # Если подкатегорий нет, показываем только товары текущей категории
        products = CarProduct.objects.filter(category=category)

    # 🔍 Фильтрация и сортировка
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:  # name
        products = products.order_by('product_name')

    # 📄 Пагинация
    paginator = Paginator(products, 12)  # 12 товаров на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 📂 Подкатегории для навигации
    subcategories = category.children.filter(is_active=True).order_by('display_order')

    context = {
        'category': category,
        'subcategories': subcategories,
        'page_obj': page_obj,
        'sort_by': sort_by,
        'total_products': products.count(),
        'page_title': f'{category.category_name} - Автомобильные коврики',
        'page_description': category.meta_description or f'Коврики для {category.category_name}',
        'section_type': 'cars',
    }

    return render(request, 'cars/product_list.html', context)


def car_product_detail(request, slug):
    """
    🚗 Детальная страница товара-автомобиля
    ✅ ИСПРАВЛЕНО: Завершена функция с поддержкой конфигуратора
    """
    # 📦 Получаем товар авто по slug
    product = get_object_or_404(CarProduct, slug=slug)

    # 🔄 Похожие товары из той же категории авто
    similar_products = CarProduct.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]

    # 🎨 Цвета для конфигуратора (только для автомобилей)
    carpet_colors = Color.objects.filter(color_type='carpet', is_active=True)
    border_colors = Color.objects.filter(color_type='border', is_active=True)

    context = {
        'product': product,
        'similar_products': similar_products,
        'carpet_colors': carpet_colors,  # 🚗 Цвета ковриков для авто
        'border_colors': border_colors,  # 🚗 Цвета окантовки для авто
        'page_title': product.product_name,
        'page_description': product.meta_description or f'Автомобильные коврики {product.product_name}',
        'section_type': 'cars',
        'show_configurator': True,  # 🔧 Показываем конфигуратор только для авто
    }

    return render(request, 'cars/product_detail.html', context)


@require_http_methods(["POST"])
@login_required
def car_add_to_cart(request, uid):
    """
    🛒 Добавление автомобильного товара в корзину
    ✅ ИСПРАВЛЕНО: Используем базовую функцию с правильными параметрами
    """
    return add_to_cart(request, uid)


@require_http_methods(["POST"])
@login_required
def car_add_to_wishlist(request, uid):
    """
    ❤️ Добавление автомобильного товара в избранное
    ✅ ИСПРАВЛЕНО: Используем базовую функцию с правильными параметрами
    """
    return add_to_wishlist(request, uid)


def car_search(request):
    """
    🔍 Поиск среди автомобилей
    ✅ НОВАЯ функция для поиска в автомобильном разделе
    """
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'name')

    products = CarProduct.objects.none()

    if query:
        # 🔎 Поиск по названию товара и категории
        products = CarProduct.objects.filter(
            Q(product_name__icontains=query) |
            Q(category__category_name__icontains=query) |
            Q(product_desription__icontains=query) |
            Q(product_sku__icontains=query)
        ).distinct()

        # 🔢 Сортировка результатов
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        else:  # name
            products = products.order_by('product_name')

    # 📄 Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
        'sort_by': sort_by,
        'total_products': products.count(),
        'page_title': f'Поиск автомобилей: {query}' if query else 'Поиск автомобилей',
        'section_type': 'cars',
    }

    return render(request, 'cars/search_results.html', context)


def car_configurator(request):
    """
    🔧 Конфигуратор ковриков для автомобилей
    ✅ НОВАЯ функция - специальная для автомобилей
    """
    # 🎨 Получаем все доступные цвета
    carpet_colors = Color.objects.filter(color_type='carpet', is_active=True)
    border_colors = Color.objects.filter(color_type='border', is_active=True)

    # 📂 Получаем все категории автомобилей для выбора
    categories = CarCategory.objects.filter(is_active=True).order_by('display_order', 'category_name')

    context = {
        'carpet_colors': carpet_colors,
        'border_colors': border_colors,
        'categories': categories,
        'page_title': 'Конфигуратор автомобильных ковриков',
        'page_description': 'Создайте уникальные коврики для вашего автомобиля с помощью нашего конфигуратора',
        'section_type': 'cars',
    }

    return render(request, 'cars/configurator.html', context)

# 🔧 КОММЕНТАРИЙ ДЛЯ РАЗРАБОТЧИКА:
#
# ✅ ИСПРАВЛЕНО:
# 1. Завершена функция car_product_list
# 2. Завершена функция car_product_detail
# 3. Добавлены функции car_search и car_configurator
# 4. Исправлены импорты и добавлены недостающие зависимости
#
# 🎯 РЕЗУЛЬТАТ:
# Теперь все URL из cars/urls.py будут работать корректно,
# если добавить соответствующие шаблоны.
#
# 📝 СЛЕДУЮЩИЙ ШАГ:
# Создать шаблоны:
# - templates/cars/category_list.html
# - templates/cars/product_list.html
# - templates/cars/product_detail.html
# - templates/cars/search_results.html
# - templates/cars/configurator.html