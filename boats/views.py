# 📁 boats/views.py - View функции для раздела лодок
# 🛥️ Представления для каталога лодок с использованием proxy-моделей
# ✅ БЕЗОПАСНО: Наследует логику от базовых views из products

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import BoatCategory, BoatProduct
from products.views import (
    add_to_cart,  # 🛒 Функция добавления в корзину
    add_to_wishlist,  # ❤️ Функция добавления в избранное
    get_product as base_get_product  # 📄 Базовая функция товара
)


def boat_category_list(request):
    """
    🛥️ Главная страница раздела "Лодки" - список всех категорий лодок
    """
    # 📂 Получаем только корневые категории лодок (без родителей)
    root_categories = BoatCategory.objects.filter(
        parent__isnull=True,
        is_active=True
    ).order_by('display_order', 'category_name')

    # 📊 Статистика по лодкам
    total_boat_products = BoatProduct.objects.count()
    newest_boats = BoatProduct.objects.filter(newest_product=True)[:6]

    context = {
        'categories': root_categories,
        'total_products': total_boat_products,
        'newest_products': newest_boats,
        'page_title': 'Лодочные коврики',
        'page_description': 'Каталог ковриков для лодок различных марок и моделей',
        'section_type': 'boats',  # 🏷️ Идентификатор раздела
    }

    return render(request, 'boats/category_list.html', context)


def boat_product_list(request, slug):
    """
    🛥️ Список товаров в конкретной категории лодок
    """
    # 📂 Получаем категорию лодки по slug
    category = get_object_or_404(BoatCategory, slug=slug, is_active=True)

    # 📦 Получаем все товары этой категории и подкатегорий
    if category.children.exists():
        # Если есть подкатегории, показываем товары из всех подкатегорий
        subcategory_ids = list(category.children.values_list('id', flat=True))
        subcategory_ids.append(category.id)
        products = BoatProduct.objects.filter(category_id__in=subcategory_ids)
    else:
        # Если подкатегорий нет, показываем только товары текущей категории
        products = BoatProduct.objects.filter(category=category)

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
        'page_title': f'{category.category_name} - Лодочные коврики',
        'page_description': category.meta_description or f'Коврики для лодок {category.category_name}',
        'section_type': 'boats',
    }

    return render(request, 'boats/product_list.html', context)


def boat_product_detail(request, slug):
    """
    🛥️ Детальная страница товара-лодки
    ✅ ИСПОЛЬЗУЕТ: Базовую логику, но адаптированную для лодок
    """
    # 📦 Получаем товар лодки по slug
    product = get_object_or_404(BoatProduct, slug=slug)

    # 🔄 Похожие товары из той же категории лодок
    similar_products = BoatProduct.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]

    # 📐 Особые данные для лодок (размеры)
    boat_dimensions = None
    if product.boat_mat_length or product.boat_mat_width:
        boat_dimensions = {
            'length': product.boat_mat_length,
            'width': product.boat_mat_width,
            'display': product.get_boat_dimensions()
        }

    context = {
        'product': product,
        'similar_products': similar_products,
        'boat_dimensions': boat_dimensions,  # 🛥️ Специальные данные для лодок
        'page_title': product.product_name,
        'page_description': product.meta_description or f'Коврик для лодки {product.product_name}',
        'section_type': 'boats',
    }

    return render(request, 'boats/product_detail.html', context)


@require_http_methods(["POST"])
@login_required
def boat_add_to_cart(request, uid):
    """
    🛒 Добавление товара-лодки в корзину
    ✅ НАСЛЕДУЕТ: Базовую логику add_to_cart
    """
    # Проверяем, что товар действительно лодка
    try:
        product = BoatProduct.objects.get(uid=uid)
    except BoatProduct.DoesNotExist:
        return JsonResponse({'status': False, 'message': 'Товар не найден'})

    # 🔄 Используем базовую функцию добавления в корзину
    return add_to_cart(request, uid)


@require_http_methods(["POST"])
@login_required
def boat_add_to_wishlist(request, uid):
    """
    ❤️ Добавление товара-лодки в избранное
    ✅ НАСЛЕДУЕТ: Базовую логику add_to_wishlist
    """
    # Проверяем, что товар действительно лодка
    try:
        product = BoatProduct.objects.get(uid=uid)
    except BoatProduct.DoesNotExist:
        return JsonResponse({'status': False, 'message': 'Товар не найден'})

    # 🔄 Используем базовую функцию добавления в избранное  
    return add_to_wishlist(request, uid)


def boat_search(request):
    """
    🔍 Поиск товаров среди лодок
    """
    query = request.GET.get('q', '').strip()
    results = []

    if len(query) >= 3:  # Поиск только при 3+ символах
        results = BoatProduct.objects.filter(
            product_name__icontains=query
        ).order_by('product_name')[:20]  # Ограничиваем 20 результатами

    context = {
        'query': query,
        'results': results,
        'total_found': results.count() if results else 0,
        'section_type': 'boats',
        'page_title': f'Поиск лодок: {query}' if query else 'Поиск лодок',
    }

    return render(request, 'boats/search.html', context)