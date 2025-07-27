# 📁 boats/views.py - VIEWS ДЛЯ ОТДЕЛЬНЫХ МОДЕЛЕЙ BOATS
# 🛥️ Представления для каталога лодок с отдельными таблицами
# ✅ РАБОТАЕТ С: BoatCategory, BoatProduct, BoatProductImage (отдельные модели)

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Min, Max
from django.db import models

# 🛥️ ОТДЕЛЬНЫЕ МОДЕЛИ: Импорт из boats (независимые таблицы)
from .models import BoatCategory, BoatProduct, BoatProductImage

# 🎨 Цвета используем из products (общие)
from products.models import Color

# 🛒 Функции корзины и избранного из products (работают с любыми товарами)
from products.views import add_to_cart, add_to_wishlist


def boat_category_list(request):
    """
    🛥️ Главная страница раздела "Лодки" - список всех категорий лодок
    ✅ РАБОТАЕТ С: BoatCategory (отдельная таблица)
    """

    # 📂 Получаем все активные категории лодок (плоская структура)
    categories = BoatCategory.objects.filter(
        is_active=True
    ).order_by('display_order', 'category_name')

    # 📊 Статистика по лодкам
    total_boat_products = BoatProduct.objects.filter(is_active=True).count()
    newest_boats = BoatProduct.objects.filter(
        newest_product=True,
        is_active=True
    ).select_related('category').prefetch_related('images')[:6]

    # 🎯 Рекомендуемые лодки
    featured_boats = BoatProduct.objects.filter(
        is_featured=True,
        is_active=True
    ).select_related('category').prefetch_related('images')[:8]

    # 📊 Статистика размеров для главной страницы
    size_stats = BoatProduct.objects.filter(is_active=True).aggregate(
        min_length=Min('boat_mat_length'),
        max_length=Max('boat_mat_length'),
        min_width=Min('boat_mat_width'),
        max_width=Max('boat_mat_width'),
        total_with_sizes=models.Count('id', filter=Q(boat_mat_length__isnull=False, boat_mat_width__isnull=False))
    )

    context = {
        'categories': categories,
        'total_products': total_boat_products,
        'newest_products': newest_boats,
        'featured_products': featured_boats,
        'size_stats': size_stats,  # 🛥️ Статистика размеров
        'page_title': 'Лодочные коврики',
        'page_description': 'Каталог ковриков для лодок различных марок и моделей. Размеры, цвета, быстрая доставка.',
        'section_type': 'boats',  # 🏷️ Идентификатор раздела
    }

    return render(request, 'boats/category_list.html', context)


def boat_product_list(request, slug):
    """
    🛥️ Список товаров в конкретной категории лодок
    ✅ РАБОТАЕТ С: BoatCategory, BoatProduct (отдельные таблицы)
    """

    # 📂 Получаем категорию лодок по slug
    category = get_object_or_404(BoatCategory, slug=slug, is_active=True)

    # 📦 Получаем товары этой категории (плоская структура)
    products = BoatProduct.objects.filter(
        category=category,
        is_active=True
    ).select_related('category').prefetch_related('images')

    # 🔍 Поиск по лодкам
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )

    # 📊 УНИКАЛЬНЫЕ ФИЛЬТРЫ ДЛЯ ЛОДОК: Фильтрация по размерам
    min_length = request.GET.get('min_length')
    max_length = request.GET.get('max_length')
    min_width = request.GET.get('min_width')
    max_width = request.GET.get('max_width')

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

    # 📊 Сортировка (включая сортировку по размерам)
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'size_asc':  # 🛥️ Сортировка по размеру (уникально для лодок)
        products = products.order_by('boat_mat_length', 'boat_mat_width')
    elif sort_by == 'size_desc':
        products = products.order_by('-boat_mat_length', '-boat_mat_width')
    else:  # name
        products = products.order_by('product_name')

    # 📄 Пагинация
    per_page = request.GET.get('per_page', '12')
    if per_page == 'all':
        page_obj = products
        paginator = None
    else:
        try:
            per_page = int(per_page)
        except ValueError:
            per_page = 12

        paginator = Paginator(products, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

    # 📊 Статистика размеров для фильтров
    category_size_stats = products.aggregate(
        min_length=Min('boat_mat_length'),
        max_length=Max('boat_mat_length'),
        min_width=Min('boat_mat_width'),
        max_width=Max('boat_mat_width')
    )

    context = {
        'category': category,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'sort_by': sort_by,
        'per_page': per_page,
        'total_products': products.count(),
        'size_stats': category_size_stats,  # 🛥️ Статистика размеров для фильтров
        'current_filters': {  # 🛥️ Текущие фильтры размеров
            'min_length': min_length,
            'max_length': max_length,
            'min_width': min_width,
            'max_width': max_width
        },
        'page_title': f'Лодочные коврики {category.category_name}',
        'page_description': category.meta_description or f'Коврики для лодок {category.category_name}. Различные размеры, цвета, быстрая доставка.',
        'section_type': 'boats',
    }

    return render(request, 'boats/product_list.html', context)


def boat_product_detail(request, slug):
    """
    🛥️ Детальная страница товара лодки
    ✅ РАБОТАЕТ С: BoatProduct, BoatProductImage (отдельные таблицы)
    """

    # 📦 Получаем товар лодки по slug
    product = get_object_or_404(
        BoatProduct.objects.select_related('category').prefetch_related('images'),
        slug=slug,
        is_active=True
    )

    # 🔄 Похожие товары из той же категории лодок
    similar_products = BoatProduct.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).select_related('category').prefetch_related('images')[:4]

    # 📐 СПЕЦИАЛЬНЫЕ ДАННЫЕ ДЛЯ ЛОДОК: размеры коврика
    boat_dimensions = product.get_dimensions_display()

    # 🎨 Цвета для лодок (используем из products.models.Color)
    carpet_colors = Color.objects.filter(
        color_type='carpet',
        is_available=True
    ).order_by('display_order', 'name')

    border_colors = Color.objects.filter(
        color_type='border',
        is_available=True
    ).order_by('display_order', 'name')

    # 🖼️ Изображения товара лодки
    product_images = product.images.filter().order_by('display_order', 'created_at')
    main_image = product.get_main_image()

    # 🧭 Хлебные крошки
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Лодки', 'url': '/boats/'},
        {'name': product.category.category_name, 'url': product.category.get_absolute_url()},
        {'name': product.product_name, 'url': ''}
    ]

    # 📊 Дополнительная информация для лодок
    related_by_size = []
    if boat_dimensions:
        # Товары с похожими размерами
        related_by_size = BoatProduct.objects.filter(
            boat_mat_length__range=[
                boat_dimensions['length'] - 20,
                boat_dimensions['length'] + 20
            ],
            boat_mat_width__range=[
                boat_dimensions['width'] - 20,
                boat_dimensions['width'] + 20
            ],
            is_active=True
        ).exclude(id=product.id)[:3]

    context = {
        'product': product,
        'similar_products': similar_products,
        'related_by_size': related_by_size,  # 🛥️ Товары с похожими размерами
        'boat_dimensions': boat_dimensions,  # 🛥️ Размеры коврика
        'carpet_colors': carpet_colors,  # 🎨 Цвета ковриков
        'border_colors': border_colors,  # 🎨 Цвета окантовки
        'product_images': product_images,  # 🖼️ Все изображения
        'main_image': main_image,  # 🖼️ Главное изображение
        'breadcrumbs': breadcrumbs,  # 🧭 Навигация
        'page_title': product.meta_title or product.product_name,
        'page_description': product.meta_description or f'Лодочный коврик {product.product_name}. {product.get_mat_dimensions()}',
        'section_type': 'boats',
        'show_boat_features': True,  # 🛥️ Показываем особенности лодок
    }

    return render(request, 'boats/product_detail.html', context)


def boat_search(request):
    """
    🔍 Поиск среди лодочных товаров
    ✅ РАБОТАЕТ С: BoatProduct (отдельная таблица)
    """

    query = request.GET.get('q', '')

    if not query:
        return render(request, 'boats/search_results.html', {
            'query': '',
            'results': [],
            'total_results': 0,
            'message': 'Введите запрос для поиска лодочных ковриков'
        })

    # 🔍 Поиск по всем полям лодочных товаров
    results = BoatProduct.objects.filter(
        Q(product_name__icontains=query) |
        Q(description__icontains=query) |
        Q(short_description__icontains=query) |
        Q(sku__icontains=query) |
        Q(category__category_name__icontains=query),
        is_active=True
    ).select_related('category').prefetch_related('images')

    # 📊 Фильтр по размерам в поиске
    size_filter = request.GET.get('size')
    if size_filter:
        try:
            length, width = map(int, size_filter.split('x'))
            results = results.filter(
                boat_mat_length=length,
                boat_mat_width=width
            )
        except ValueError:
            pass

    # 📊 Сортировка результатов поиска
    sort_by = request.GET.get('sort', 'relevance')
    if sort_by == 'price_asc':
        results = results.order_by('price')
    elif sort_by == 'price_desc':
        results = results.order_by('-price')
    elif sort_by == 'name':
        results = results.order_by('product_name')
    elif sort_by == 'size':
        results = results.order_by('boat_mat_length', 'boat_mat_width')
    else:  # relevance
        results = results.order_by('-is_featured', '-newest_product', 'product_name')

    # 📄 Пагинация результатов
    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
        'total_results': results.count(),
        'sort_by': sort_by,
        'size_filter': size_filter,
        'page_title': f'Поиск лодочных ковриков: {query}',
        'page_description': f'Результаты поиска "{query}" среди лодочных ковриков',
        'section_type': 'boats',
    }

    return render(request, 'boats/search_results.html', context)


@require_http_methods(["POST"])
@login_required
def boat_add_to_cart(request, uid):
    """
    🛒 Добавление лодочного товара в корзину
    ✅ ИСПОЛЬЗУЕТ базовую функцию add_to_cart из products
    """
    return add_to_cart(request, uid)


@require_http_methods(["POST"])
@login_required
def boat_add_to_wishlist(request, uid):
    """
    ❤️ Добавление лодочного товара в избранное
    ✅ ИСПОЛЬЗУЕТ базовую функцию add_to_wishlist из products
    """
    return add_to_wishlist(request, uid)


def boat_get_product_info(request, slug):
    """
    📊 AJAX: Получение информации о товаре лодки
    ✅ РАБОТАЕТ С: BoatProduct (отдельная таблица)
    """

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        product = get_object_or_404(
            BoatProduct.objects.select_related('category'),
            slug=slug,
            is_active=True
        )

        # 📐 Информация о размерах
        dimensions = product.get_dimensions_display()

        data = {
            'id': product.id,
            'name': product.product_name,
            'price': float(product.price),
            'price_formatted': product.get_display_price(),
            'category': product.category.category_name,
            'dimensions': dimensions,  # 🛥️ Полная информация о размерах
            'main_image': product.get_main_image().image.url if product.get_main_image() else None,
            'is_featured': product.is_featured,
            'newest_product': product.newest_product,
            'in_stock': product.is_in_stock(),
            'stock_quantity': product.stock_quantity,
            'url': product.get_absolute_url()
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


def boat_category_products_count(request):
    """
    📊 AJAX: Количество товаров в категориях (для главной страницы)
    ✅ РАБОТАЕТ С: BoatCategory, BoatProduct (отдельные таблицы)
    """

    categories_data = []

    for category in BoatCategory.objects.filter(is_active=True):
        products_count = category.get_products_count()

        categories_data.append({
            'id': category.id,
            'name': category.category_name,
            'slug': category.slug,
            'products_count': products_count,
            'url': category.get_absolute_url(),
            'image': category.category_image.url if category.category_image else None
        })

    return JsonResponse({'categories': categories_data})

# 📝 КОММЕНТАРИИ:
#
# ✅ СОЗДАНЫ VIEWS ДЛЯ ОТДЕЛЬНЫХ МОДЕЛЕЙ BOATS:
# 1. boat_category_list - главная страница лодок
# 2. boat_product_list - список товаров категории
# 3. boat_product_detail - детальная страница товара
# 4. boat_search - поиск среди лодок
# 5. boat_add_to_cart - добавление в корзину
# 6. boat_add_to_wishlist - добавление в избранное
# 7. boat_get_product_info - AJAX информация о товаре
# 8. boat_category_products_count - AJAX счетчики
#
# 🛥️ УНИКАЛЬНЫЕ ОСОБЕННОСТИ ДЛЯ ЛОДОК:
# • Фильтрация по размерам (min/max length/width)
# • Сортировка по размерам (size_asc, size_desc)
# • Поиск с фильтром размеров (120x80)
# • related_by_size - товары с похожими размерами
# • boat_dimensions контекст для шаблонов
# • Использование цветов из products.models.Color
#
# 📊 НОВЫЕ КОНТЕКСТЫ ДЛЯ ШАБЛОНОВ:
# • boat_dimensions - размеры коврика
# • size_stats - статистика размеров для фильтров
# • current_filters - текущие фильтры размеров
# • related_by_size - товары с похожими размерами
# • show_boat_features - флаг показа особенностей лодок
#
# 🎯 РАБОТАЕТ С ОТДЕЛЬНЫМИ ТАБЛИЦАМИ:
# • boats_boatcategory - независимые категории лодок
# • boats_boatproduct - независимые товары лодок
# • boats_boatproductimage - независимые изображения лодок
# • products_color - общие цвета (используются совместно)