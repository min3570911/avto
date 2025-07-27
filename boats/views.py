# 📁 boats/views.py - ИСПРАВЛЕННЫЕ View функции для раздела лодок
# 🛥️ Представления для каталога лодок с использованием proxy-моделей
# 🔧 ИСПРАВЛЕНО: Импорт references.models → products.models

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import BoatCategory, BoatProduct
from products.models import Color  # ✅ ИСПРАВЛЕНО: references → products
from products.views import (  # ✅ ИСПРАВЛЕНО: references → products
    add_to_cart,  # 🛒 Функция добавления в корзину
    add_to_wishlist,  # ❤️ Функция добавления в избранное
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
    ✅ ИСПРАВЛЕНО: Завершена функция
    """
    # 📂 Получаем категорию лодок по slug
    category = get_object_or_404(BoatCategory, slug=slug, is_active=True)

    # 📦 Получаем все товары этой категории и подкатегорий
    products = BoatProduct.objects.filter(
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
    subcategories = BoatCategory.objects.filter(parent=category, is_active=True)

    context = {
        'category': category,
        'subcategories': subcategories,
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_products': products.count(),
        'page_title': f'Лодочные коврики {category.category_name}',
        'page_description': category.get_seo_description() if hasattr(category, 'get_seo_description') else f'Коврики для лодок {category.category_name}',
        'section_type': 'boats',
    }

    return render(request, 'boats/product_list.html', context)


def boat_product_detail(request, slug):
    """
    🛥️ Детальная страница товара лодки
    ✅ ИСПРАВЛЕНО: Завершена функция с поддержкой размеров лодок
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

    # 🎨 Цвета для лодок (коврики и окантовка)
    carpet_colors = Color.objects.filter(color_type='carpet', is_available=True)
    border_colors = Color.objects.filter(color_type='border', is_available=True)

    context = {
        'product': product,
        'similar_products': similar_products,
        'boat_dimensions': boat_dimensions,  # 🛥️ Специальные данные для лодок
        'carpet_colors': carpet_colors,  # 🛥️ Цвета ковриков для лодок
        'border_colors': border_colors,  # 🛥️ Цвета окантовки для лодок
        'page_title': product.product_name,
        'page_description': product.meta_description or f'Коврик для лодки {product.product_name}',
        'section_type': 'boats',
        'show_boat_features': True,  # 🛥️ Показываем особенности лодок
    }

    return render(request, 'boats/product_detail.html', context)


@require_http_methods(["POST"])
@login_required
def boat_add_to_cart(request, uid):
    """
    🛒 Добавление лодочного товара в корзину
    ✅ ИСПРАВЛЕНО: Используем базовую функцию с правильными параметрами
    """
    return add_to_cart(request, uid)


@require_http_methods(["POST"])
@login_required
def boat_add_to_wishlist(request, uid):
    """
    ❤️ Добавление лодочного товара в избранное
    ✅ ИСПРАВЛЕНО: Используем базовую функцию
    """
    return add_to_wishlist(request, uid)


def boat_search(request):
    """
    🔍 Поиск среди лодочных товаров
    ✅ НОВАЯ функция - специальная для лодок
    """
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'name')

    products = BoatProduct.objects.none()

    if query:
        # 🔍 Поиск по названию, описанию и артикулу
        products = BoatProduct.objects.filter(
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
        'page_title': f'Поиск лодок: {query}' if query else 'Поиск лодок',
        'section_type': 'boats',
    }

    return render(request, 'boats/search_results.html', context)

# 🔧 ИСПРАВЛЕНИЯ:
# ✅ ЗАМЕНЕНО: from references.models → from products.models
# ✅ ЗАМЕНЕНО: from references.views → from products.views
# ✅ ЗАВЕРШЕНЫ: Все неполные функции с правильной логикой
# ✅ ДОБАВЛЕНА: Поддержка размеров лодок в product_detail
# ✅ ДОБАВЛЕНА: Функция поиска boat_search
# ✅ СОХРАНЕНО: Лодочная логика без комплектаций и подпятника