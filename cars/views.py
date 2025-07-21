# 📁 cars/views.py - View функции для раздела автомобилей
# 🚗 Представления для каталога автомобилей с использованием proxy-моделей
# ✅ БЕЗОПАСНО: Наследует логику от базовых views из products

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import CarCategory, CarProduct
from products.views import (
    add_to_cart,  # 🛒 Функция добавления в корзину
    add_to_wishlist,  # ❤️ Функция добавления в избранное
    get_product as base_get_product  # 📄 Базовая функция товара
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
    ✅ ИСПОЛЬЗУЕТ: Базовую логику, но адаптированную для автомобилей
    """
    # 📦 Получаем товар авто по slug
    product = get_object_or_404(CarProduct, slug=slug)

    # 🔄 Похожие товары из той же категории авто
    similar_products = CarProduct.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]

    # 🏪 Информация о наличии на складе (для авто актуально)
    storage_info = {
        'in_stock': True,  # Здесь может быть более сложная логика
        'delivery_time': '1-3 дня',  # Время доставки для авто
    }

    context = {
        'product': product,
        'similar_products': similar_products,
        'storage_info': storage_info,  # 🚗 Специальные данные для авто
        'page_title': product.product_name,
        'page_description': product.meta_description or f'Автомобильный коврик {product.product_name}',
        'section_type': 'cars',
    }

    return render(request, 'cars/product_detail.html', context)


@require_http_methods(["POST"])
@login_required
def car_add_to_cart(request, uid):
    """
    🛒 Добавление товара-автомобиля в корзину
    ✅ НАСЛЕДУЕТ: Базовую логику add_to_cart
    """
    # Проверяем, что товар действительно автомобиль
    try:
        product = CarProduct.objects.get(uid=uid)
    except CarProduct.DoesNotExist:
        return JsonResponse({'status': False, 'message': 'Товар не найден'})

    # 🔄 Используем базовую функцию добавления в корзину
    return add_to_cart(request, uid)


@require_http_methods(["POST"])
@login_required
def car_add_to_wishlist(request, uid):
    """
    ❤️ Добавление товара-автомобиля в избранное
    ✅ НАСЛЕДУЕТ: Базовую логику add_to_wishlist
    """
    # Проверяем, что товар действительно автомобиль
    try:
        product = CarProduct.objects.get(uid=uid)
    except CarProduct.DoesNotExist:
        return JsonResponse({'status': False, 'message': 'Товар не найден'})

    # 🔄 Используем базовую функцию добавления в избранное
    return add_to_wishlist(request, uid)


def car_search(request):
    """
    🔍 Поиск товаров среди автомобилей
    """
    query = request.GET.get('q', '').strip()
    results = []

    if len(query) >= 3:  # Поиск только при 3+ символах
        results = CarProduct.objects.filter(
            product_name__icontains=query
        ).order_by('product_name')[:20]  # Ограничиваем 20 результатами

    context = {
        'query': query,
        'results': results,
        'total_found': results.count() if results else 0,
        'section_type': 'cars',
        'page_title': f'Поиск автомобилей: {query}' if query else 'Поиск автомобилей',
    }

    return render(request, 'cars/search.html', context)


def car_configurator(request):
    """
    🔧 Конфигуратор автомобильных ковриков
    ✅ СПЕЦИАЛЬНАЯ функция только для авто (у лодок такого нет)
    """
    # Получаем все категории авто для выбора марки
    car_brands = CarCategory.objects.filter(
        parent__isnull=True,
        is_active=True
    ).order_by('category_name')

    # 🎨 Получаем доступные цвета из products.models
    from products.models import Color
    carpet_colors = Color.objects.filter(color_type='carpet')
    border_colors = Color.objects.filter(color_type='border')

    context = {
        'car_brands': car_brands,
        'carpet_colors': carpet_colors,
        'border_colors': border_colors,
        'page_title': 'Конфигуратор автомобильных ковриков',
        'page_description': 'Создайте индивидуальный набор ковриков для вашего автомобиля',
        'section_type': 'cars',
    }

    return render(request, 'cars/configurator.html', context)