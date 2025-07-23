# 📁 boats/views.py - ИСПРАВЛЕННЫЕ View функции для раздела лодок
# 🛥️ Представления для каталога лодок с использованием proxy-моделей
# ✅ ИСПРАВЛЕНО: Завершены все неполные функции

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import BoatCategory, BoatProduct
from products.models import Color
from products.views import (
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
    carpet_colors = Color.objects.filter(color_type='carpet', is_active=True)
    border_colors = Color.objects.filter(color_type='border', is_active=True)

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
    ✅ ИСПРАВЛЕНО: Используем базовую функцию с правильными параметрами
    """
    return add_to_wishlist(request, uid)


def boat_search(request):
    """
    🔍 Поиск среди лодок
    ✅ НОВАЯ функция для поиска в лодочном разделе
    """
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'name')

    products = BoatProduct.objects.none()

    if query:
        # 🔎 Поиск по названию товара, категории и размерам лодок
        products = BoatProduct.objects.filter(
            Q(product_name__icontains=query) |
            Q(category__category_name__icontains=query) |
            Q(product_desription__icontains=query) |
            Q(product_sku__icontains=query) |
            Q(boat_mat_length__icontains=query) |
            Q(boat_mat_width__icontains=query)
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

# 🔧 КОММЕНТАРИЙ ДЛЯ РАЗРАБОТЧИКА:
#
# ✅ ИСПРАВЛЕНО:
# 1. Завершена функция boat_product_list
# 2. Завершена функция boat_product_detail с поддержкой размеров лодок
# 3. Добавлена функция boat_search с поиском по размерам
# 4. Исправлены импорты и добавлены недостающие зависимости
#
# 🛥️ ОСОБЕННОСТИ ДЛЯ ЛОДОК:
# - Поддержка размеров лодок (boat_mat_length, boat_mat_width)
# - Поиск по размерам лодок
# - Отображение boat_dimensions в контексте
# - Специальный флаг show_boat_features
#
# 🎯 РЕЗУЛЬТАТ:
# Теперь все URL из boats/urls.py будут работать корректно,
# если добавить соответствующие шаблоны.
#
# 📝 СЛЕДУЮЩИЙ ШАГ:
# Создать шаблоны:
# - templates/boats/category_list.html
# - templates/boats/product_list.html
# - templates/boats/product_detail.html
# - templates/boats/search_results.html