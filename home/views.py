# home/views.py
from django.shortcuts import render, get_object_or_404
from products.models import Product, Category, KitVariant
from django.core.paginator import Paginator


def index(request):
    """📱 Отображение главной страницы с товарами"""
    # Получаем параметры фильтрации из GET-запроса
    category_filter = request.GET.get('category')
    sort_option = request.GET.get('sort')

    # Базовый запрос всех товаров
    products_query = Product.objects.filter(parent=None)

    # Применяем фильтр по категории, если выбран
    if category_filter:
        categories = Category.objects.filter(category_name=category_filter)
        if categories.exists():
            products_query = products_query.filter(category__in=categories)

    # Применяем сортировку, если выбрана
    if sort_option == 'newest':
        products_query = products_query.filter(newest_product=True)
    elif sort_option == 'priceAsc':
        products_query = products_query.order_by('price')
    elif sort_option == 'priceDesc':
        products_query = products_query.order_by('-price')

    # Получение данных для фильтра категорий
    categories = Category.objects.all()

    # Получаем комплектацию "Салон"
    salon_kit = KitVariant.objects.filter(code='salon').first()

    # Пагинация
    page = request.GET.get('page', 1)
    paginator = Paginator(products_query, 8)  # 8 товаров на страницу
    products = paginator.get_page(page)

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_filter,
        'selected_sort': sort_option,
        'salon_kit': salon_kit,  # Передаем информацию о комплектации в шаблон
    }

    return render(request, 'home/index.html', context)


def category_view(request, slug):
    """
    🛍️ Отображение страницы категории с товарами

    Args:
        request: HTTP-запрос
        slug: Слаг категории из URL

    Returns:
        Отрендеренный шаблон со списком товаров выбранной категории и описанием внизу
    """
    # Получаем категорию или возвращаем 404
    category = get_object_or_404(Category, slug=slug)

    # Получаем все продукты этой категории
    products_query = Product.objects.filter(category=category, parent=None)

    # Сортировка товаров (аналогично index view)
    sort_option = request.GET.get('sort')
    if sort_option == 'newest':
        products_query = products_query.filter(newest_product=True)
    elif sort_option == 'priceAsc':
        products_query = products_query.order_by('price')
    elif sort_option == 'priceDesc':
        products_query = products_query.order_by('-price')

    # Пагинация
    page = request.GET.get('page', 1)
    paginator = Paginator(products_query, 12)  # 12 товаров на странице
    products = paginator.get_page(page)

    # Получаем все категории для фильтра
    categories = Category.objects.all()

    # Здесь можно добавить получение описания категории из базы данных или CMS
    # Например, если бы у модели Category было поле description:
    # category_description = category.description
    category_description = None  # Пока используем значение по умолчанию в шаблоне

    # Получаем комплектацию "Салон"
    salon_kit = KitVariant.objects.filter(code='salon').first()

    context = {
        'category': category,
        'products': products,
        'categories': categories,
        'selected_sort': sort_option,
        'category_description': category_description,
        'salon_kit': salon_kit,
    }

    return render(request, 'home/category.html', context)


# ВАЖНО: Здесь функция называется product_search в соответствии с urls.py
def product_search(request):
    """🔍 Поиск товаров по запросу"""
    query = request.GET.get('q', '')
    products = None

    if query:
        products = Product.objects.filter(product_name__icontains=query)

    context = {
        'query': query,
        'products': products,
    }

    return render(request, 'home/search.html', context)


def contact(request):
    """📞 Страница контактов"""
    form_id = "xrgpdzwe"  # ID формы Formspree
    return render(request, 'home/contact.html', {'form_id': form_id})


def about(request):
    """ℹ️ Страница о нас"""
    return render(request, 'home/about.html')


def privacy_policy(request):
    """📜 Страница политики конфиденциальности"""
    return render(request, 'home/privacy_policy.html')


def terms_and_conditions(request):
    """📄 Страница условий использования"""
    return render(request, 'home/terms_and_conditions.html')