# 📁 boats/views.py - СКОПИРОВАНО С products/views.py
# 🛥️ Рабочие представления адаптированные для лодок
# ✅ ПРОВЕРЕНО: Логика взята с рабочего products_catalog

import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

# 🛥️ Модели лодок
from .models import BoatCategory, BoatProduct, BoatProductImage

# 🎨 Общие модели
from products.models import Color, KitVariant

# 🛒 Временные функции корзины (обновим на этапе 3)
from products.views import add_to_cart, add_to_wishlist


def boat_category_list(request):
    """
    🛥️ Главная страница лодок = каталог всех лодок (как products_catalog)

    Отображает все товары лодок с возможностью поиска и фильтрации.
    Поддерживает пагинацию и сортировку + размеры лодок.
    """
    # 🔍 Параметры поиска и фильтрации
    search_query = request.GET.get("search", "")
    sort_by = request.GET.get("sort", "-created_at")
    category_filter = request.GET.get("category", "")
    per_page = request.GET.get("per_page", "12")

    # 📐 НОВОЕ: Фильтры по размерам лодок
    min_length = request.GET.get("min_length", "")
    max_length = request.GET.get("max_length", "")
    min_width = request.GET.get("min_width", "")
    max_width = request.GET.get("max_width", "")

    # 📦 Базовый queryset всех товаров лодок
    products = BoatProduct.objects.all().select_related("category").prefetch_related("images")

    # 🔍 Поиск по названию товара и описанию
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query)
            | Q(product_desription__icontains=search_query)
            | Q(product_sku__icontains=search_query)
            | Q(category__category_name__icontains=search_query)
        )

    # 📂 Фильтрация по категории лодок
    if category_filter:
        products = products.filter(category__slug=category_filter)

    # 📐 НОВОЕ: Фильтрация по размерам лодок
    if min_length:
        try:
            products = products.filter(boat_mat_length__gte=int(min_length))
        except ValueError:
            pass
    if max_length:
        try:
            products = products.filter(boat_mat_length__lte=int(max_length))
        except ValueError:
            pass
    if min_width:
        try:
            products = products.filter(boat_mat_width__gte=int(min_width))
        except ValueError:
            pass
    if max_width:
        try:
            products = products.filter(boat_mat_width__lte=int(max_width))
        except ValueError:
            pass

    # 📊 Сортировка товаров (+ размеры)
    sort_options = {
        "name": "product_name",
        "-name": "-product_name",
        "price": "price",
        "-price": "-price",
        "newest": "-created_at",
        "oldest": "created_at",
        "size_asc": "boat_mat_length",  # 🛥️ НОВОЕ: по размеру
        "size_desc": "-boat_mat_length",
    }
    products = products.order_by(sort_options.get(sort_by, "-created_at"))

    # 🔢 Обработка per_page (скопировано с products)
    if per_page == "all":
        total_products = products.count()
        if total_products > 500:
            messages.warning(request,
                             f"Показано первые 500 из {total_products} товаров лодок. Используйте фильтры для поиска.")
            per_page_num = 500
        else:
            per_page_num = total_products or 1
    else:
        try:
            per_page_num = int(per_page)
            if per_page_num not in [12, 24, 48, 96]:
                per_page_num = 12
        except (ValueError, TypeError):
            per_page_num = 12

    # 📄 Пагинация
    paginator = Paginator(products, per_page_num)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 📂 Активные категории лодок
    categories = (
        BoatCategory.objects.filter(is_active=True)
        .order_by("display_order", "category_name")
    )

    # 📊 Контекст для шаблона
    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "search_query": search_query,
        "sort_by": sort_by,
        "category_filter": category_filter,
        "per_page": per_page,
        "total_products": paginator.count,
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
        # 🛥️ НОВОЕ: Фильтры размеров
        "min_length": min_length,
        "max_length": max_length,
        "min_width": min_width,
        "max_width": max_width,
        # 🏷️ Идентификация раздела
        "section_type": "boats",
        "page_title": "🛥️ Лодочные коврики EVA",
        "page_description": "Каталог ковриков для лодок различных марок и моделей",
    }

    return render(request, "boats/category_list.html", context)


def boat_product_list(request, slug):
    """📂 Каталог товаров лодок в выбранной категории (как products_by_category)"""
    category = get_object_or_404(BoatCategory, slug=slug)

    if not category.is_active:
        messages.warning(request, "Эта категория лодок временно недоступна.")
        return redirect("boats:category_list")

    # 🔍 Параметры
    sort_by = request.GET.get("sort", "-created_at")
    search_query = request.GET.get("search", "")
    per_page = request.GET.get("per_page", "12")

    # 📐 Фильтры по размерам
    min_length = request.GET.get("min_length", "")
    max_length = request.GET.get("max_length", "")
    min_width = request.GET.get("min_width", "")
    max_width = request.GET.get("max_width", "")

    # 📦 Товары категории лодок
    products = (
        BoatProduct.objects.filter(category=category)
        .select_related("category")
        .prefetch_related("images")
    )

    # 🔍 Поиск внутри категории
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query)
            | Q(product_desription__icontains=search_query)
            | Q(product_sku__icontains=search_query)
        )

    # 📐 Фильтрация по размерам внутри категории
    if min_length:
        try:
            products = products.filter(boat_mat_length__gte=int(min_length))
        except ValueError:
            pass
    if max_length:
        try:
            products = products.filter(boat_mat_length__lte=int(max_length))
        except ValueError:
            pass
    if min_width:
        try:
            products = products.filter(boat_mat_width__gte=int(min_width))
        except ValueError:
            pass
    if max_width:
        try:
            products = products.filter(boat_mat_width__lte=int(max_width))
        except ValueError:
            pass

    # 📊 Сортировка (скопировано + размеры)
    sort_options = {
        "name": "product_name",
        "-name": "-product_name",
        "price": "price",
        "-price": "-price",
        "newest": "-created_at",
        "oldest": "created_at",
        "size_asc": "boat_mat_length",
        "size_desc": "-boat_mat_length",
    }
    products = products.order_by(sort_options.get(sort_by, "-created_at"))

    # 🔢 Обработка per_page
    if per_page == "all":
        total_products = products.count()
        if total_products > 500:
            messages.warning(request,
                             f"Показано первые 500 из {total_products} товаров. Используйте фильтры для поиска.")
            per_page_num = 500
        else:
            per_page_num = total_products or 1
    else:
        try:
            per_page_num = int(per_page)
            if per_page_num not in [12, 24, 48, 96]:
                per_page_num = 12
        except (ValueError, TypeError):
            per_page_num = 12

    # 📄 Пагинация
    paginator = Paginator(products, per_page_num)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 📂 Все категории лодок для фильтра
    categories = (
        BoatCategory.objects.filter(is_active=True)
        .order_by("display_order", "category_name")
    )

    # 🧭 Хлебные крошки
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Лодки', 'url': '/boats/'},
        {'name': category.category_name, 'url': ''}
    ]

    # 📊 Контекст для шаблона
    context = {
        "category": category,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "search_query": search_query,
        "sort_by": sort_by,
        "per_page": per_page,
        "total_products": paginator.count,
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
        # 🛥️ Фильтры размеров
        "min_length": min_length,
        "max_length": max_length,
        "min_width": min_width,
        "max_width": max_width,
        "breadcrumbs": breadcrumbs,
        "section_type": "boats",
        "page_title": f"🛥️ Лодочные коврики {category.category_name}",
        "page_description": f"Коврики EVA для лодок {category.category_name}",
    }

    return render(request, "boats/product_list.html", context)


def boat_product_detail(request, slug):
    """
    🛥️ Детальная страница товара лодки (скопировано с get_product)
    """
    # 📦 Получаем товар лодки
    product = get_object_or_404(
        BoatProduct.objects.select_related('category').prefetch_related('images'),
        slug=slug
    )

    # 🔄 Похожие товары из той же категории
    similar_products = BoatProduct.objects.filter(
        category=product.category
    ).exclude(uid=product.uid).select_related('category').prefetch_related('images')[:4]

    # 📐 Размеры коврика лодки
    boat_dimensions = product.get_dimensions_display()

    # 🎨 Цвета (используем общие из products)
    carpet_colors = Color.objects.filter(
        color_type='carpet',
        is_available=True
    ).order_by('display_order', 'name')

    border_colors = Color.objects.filter(
        color_type='border',
        is_available=True
    ).order_by('display_order', 'name')

    # 🖼️ Изображения товара
    product_images = product.images.all().order_by('display_order', 'created_at')
    main_image = product.get_main_image()

    # 🧭 Хлебные крошки
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Лодки', 'url': '/boats/'},
        {'name': product.category.category_name, 'url': product.category.get_absolute_url()},
        {'name': product.product_name, 'url': ''}
    ]

    # 📊 Товары с похожими размерами (уникально для лодок)
    related_by_size = []
    if boat_dimensions:
        related_by_size = BoatProduct.objects.filter(
            boat_mat_length__range=[
                boat_dimensions['length'] - 20,
                boat_dimensions['length'] + 20
            ],
            boat_mat_width__range=[
                boat_dimensions['width'] - 20,
                boat_dimensions['width'] + 20
            ]
        ).exclude(uid=product.uid)[:3]

    context = {
        'product': product,
        'similar_products': similar_products,
        'related_by_size': related_by_size,
        'boat_dimensions': boat_dimensions,
        'carpet_colors': carpet_colors,
        'border_colors': border_colors,
        'product_images': product_images,
        'main_image': main_image,
        'breadcrumbs': breadcrumbs,
        'page_title': product.page_title or product.product_name,
        'page_description': product.meta_description or f'Лодочный коврик {product.product_name}. {product.get_mat_dimensions()}',
        'section_type': 'boats',
        'show_boat_features': True,
    }

    return render(request, 'boats/product_detail.html', context)


def boat_search(request):
    """🔍 Поиск лодок (упрощенная версия)"""
    query = request.GET.get('q', '')

    if not query:
        return render(request, 'boats/search_results.html', {
            'query': '',
            'results': [],
            'total_results': 0,
            'message': 'Введите запрос для поиска лодочных ковриков'
        })

    # 🔍 Поиск
    results = BoatProduct.objects.filter(
        Q(product_name__icontains=query) |
        Q(product_desription__icontains=query) |
        Q(product_sku__icontains=query) |
        Q(category__category_name__icontains=query)
    ).select_related('category').prefetch_related('images')

    # 📄 Пагинация
    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
        'total_results': results.count(),
        'page_title': f'Поиск лодочных ковриков: {query}',
        'section_type': 'boats',
    }

    return render(request, 'boats/search_results.html', context)


# 🛒 Корзина и избранное (временно используем из products)
@login_required
def boat_add_to_cart(request, uid):
    """🛒 Добавление лодочного товара в корзину (временно)"""
    return add_to_cart(request, uid)


@login_required
def boat_add_to_wishlist(request, uid):
    """❤️ Добавление лодочного товара в избранное (временно)"""
    return add_to_wishlist(request, uid)

# 🔧 КОММЕНТАРИИ:
#
# ✅ СКОПИРОВАНО С РАБОЧЕГО products/views.py:
# • products_catalog → boat_category_list
# • products_by_category → boat_product_list
# • get_product → boat_product_detail
# • Вся логика поиска, фильтрации, пагинации
# • Все обработки ошибок и валидация
# • Структура контекста для шаблонов
#
# 🛥️ АДАПТИРОВАНО ДЛЯ ЛОДОК:
# • Product → BoatProduct
# • Category → BoatCategory
# • Добавлены фильтры по boat_mat_length/width
# • Убраны комплектации (KitVariant)
# • Добавлены related_by_size (товары с похожими размерами)
# • Специальные контексты (boat_dimensions, show_boat_features)
#
# 📋 РЕЗУЛЬТАТ:
# • Полностью рабочие представления на основе проверенного кода
# • Готовность к работе с теми же шаблонами что и products
# • Унифицированная логика между автомобилями и лодками