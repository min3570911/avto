# 📁 cars/views.py - ИСПРАВЛЕННЫЕ View функции для раздела автомобилей
# 🚗 Представления для каталога автомобилей с использованием proxy-моделей
# 🔧 ИСПРАВЛЕНО: Импорт products.models → references.models

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import CarCategory, CarProduct
from references.models import Color  # ✅ ИСПРАВЛЕНО: products → references
from references.views import (  # ✅ ИСПРАВЛЕНО: products → references
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
    products = CarProduct.objects.filter(
        Q(category=category) | Q(category__parent=category)
    ).select_related('category').prefetch_related('product_images')

    # 🔍 Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(product_desription__icontains=search_query)
        )

    # 📊 Сортировка
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
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 📂 Дочерние категории
    subcategories = CarCategory.objects.filter(parent=category, is_active=True)

    context = {
        'category': category,
        'subcategories': subcategories,
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_products': products.count(),
        'page_title': f'Автомобильные коврики {category.category_name}',
        'page_description': category.get_seo_description(),
        'section_type': 'cars',
    }

    return render(request, 'cars/product_list.html', context)


def car_product_detail(request, slug):
    """
    🚗 Детальная страница товара автомобиля
    ✅ ИСПРАВЛЕНО: Завершена функция с комплектациями и подпятником
    """
    # 📦 Получаем товар автомобиля по slug
    product = get_object_or_404(CarProduct, slug=slug)

    # 🔄 Похожие товары из той же категории автомобилей
    similar_products = CarProduct.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]

    # 📦 Комплектации для автомобилей
    from references.models import KitVariant  # ✅ ИСПРАВЛЕНО: products → references
    kit_variants = KitVariant.objects.filter(is_option=False).order_by('order')
    additional_options = KitVariant.objects.filter(is_option=True).order_by('order')

    # 🎨 Цвета для автомобилей
    carpet_colors = Color.objects.filter(color_type='carpet', is_available=True)
    border_colors = Color.objects.filter(color_type='border', is_available=True)

    # 💰 Базовая цена и расчеты
    selected_kit_code = request.GET.get('kit', 'salon')  # Комплектация по умолчанию
    selected_kit = kit_variants.filter(code=selected_kit_code).first()

    updated_price = product.price or 0
    if selected_kit:
        updated_price += float(selected_kit.price_modifier)

    context = {
        'product': product,
        'similar_products': similar_products,
        'kit_variants': kit_variants,  # 🚗 Комплектации для автомобилей
        'additional_options': additional_options,  # 🚗 Дополнительные опции
        'carpet_colors': carpet_colors,
        'border_colors': border_colors,
        'selected_kit': selected_kit,
        'updated_price': updated_price,
        'page_title': product.product_name,
        'page_description': product.meta_description or f'Автомобильные коврики {product.product_name}',
        'section_type': 'cars',
        'show_car_features': True,  # 🚗 Показываем особенности автомобилей
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
    ✅ ИСПРАВЛЕНО: Используем базовую функцию
    """
    return add_to_wishlist(request, uid)


def car_search(request):
    """
    🔍 Поиск среди автомобильных товаров
    ✅ НОВАЯ функция - специальная для автомобилей
    """
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'name')

    products = CarProduct.objects.none()

    if query:
        # 🔍 Поиск по названию, описанию и артикулу
        products = CarProduct.objects.filter(
            Q(product_name__icontains=query) |
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
    carpet_colors = Color.objects.filter(color_type='carpet', is_available=True)
    border_colors = Color.objects.filter(color_type='border', is_available=True)

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
# 1. Импорт products.models → references.models
# 2. Импорт products.views → references.views
# 3. Завершены все неполные функции
# 4. Добавлена поддержка комплектаций в car_product_detail
# 5. Добавлены функции car_search и car_configurator
#
# 🚗 ОСОБЕННОСТИ ДЛЯ АВТОМОБИЛЕЙ:
# - Комплектации и дополнительные опции
# - Расчет цены с учетом комплектации
# - Конфигуратор ковриков
# - Поддержка подпятника
#
# 📝 СЛЕДУЮЩИЙ ШАГ:
# Создать шаблоны:
# - templates/cars/category_list.html
# - templates/cars/product_list.html
# - templates/cars/product_detail.html
# - templates/cars/search_results.html
# - templates/cars/configurator.html