# 📁 home/views.py - ОБНОВЛЕНО для новой структуры главной страницы
# 🔄 ИЗМЕНЕНО: index() функция для hero-секции и FAQ
# ✅ СОХРАНЕНО: Все остальные функции без изменений

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from products.models import Product, Category, KitVariant
from .models import FAQ, HeroSection  # 🆕 Добавлены импорты для новых моделей


def index(request):
    """
    🏠 Главная страница - ОБНОВЛЕННАЯ версия

    Новая структура:
    - Hero-секция с видео и преимуществами
    - Компактный каталог категорий (БЕЗ товаров)
    - FAQ для аккордеона

    🗑️ УБРАНО: Отображение товаров (перенесено в каталог)
    🗑️ УБРАНО: Фильтры и сортировка
    """

    # 🎬 Получаем активную hero-секцию с преимуществами
    hero_section = None
    try:
        hero_section = HeroSection.objects.filter(is_active=True).prefetch_related('advantages').first()
    except HeroSection.DoesNotExist:
        pass  # Будем отображать дефолтную секцию

    # 📂 Получаем только активные категории для каталога
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'category_name')

    # ❓ Получаем активные FAQ для аккордеона
    faqs = FAQ.objects.filter(is_active=True).order_by('order', 'created_at')

    # 📦 Комплектация "Салон" (для совместимости с существующим кодом)
    salon_kit = KitVariant.objects.filter(code='salon').first()

    # 📊 Контекст для шаблона
    context = {
        # 🎬 Hero-секция
        'hero_section': hero_section,

        # 📂 Каталог категорий
        'categories': categories,

        # ❓ FAQ для аккордеона
        'faqs': faqs,

        # 📦 Совместимость (для существующих элементов, если нужно)
        'salon_kit': salon_kit,

        # 📊 Дополнительная информация
        'categories_count': categories.count(),
        'faqs_count': faqs.count(),
    }

    return render(request, 'home/index.html', context)


# ✅ ВСЕ ОСТАЛЬНЫЕ ФУНКЦИИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ

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

    # 🔧 ИСПРАВЛЕНО: Убран filter(parent=None)
    # Получаем все продукты этой категории
    products_query = Product.objects.filter(category=category)

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

# 💡 ОСНОВНЫЕ ИЗМЕНЕНИЯ В ФАЙЛЕ:
#
# 🔄 index() функция:
#   ❌ УБРАНО: получение товаров, фильтры, сортировка, пагинация
#   ✅ ДОБАВЛЕНО: hero_section с преимуществами
#   ✅ ДОБАВЛЕНО: faqs для аккордеона
#   ✅ СОХРАНЕНО: categories для каталога
#   ✅ СОХРАНЕНО: salon_kit для совместимости
#
# 📊 Новый контекст передает:
#   - hero_section: активная hero-секция с преимуществами
#   - categories: активные категории для компактного каталога
#   - faqs: активные вопросы для аккордеона
#   - статистику количества элементов
#
# ✅ Все остальные функции (category_view, product_search, contact, about, etc.)
#    остались без изменений для обратной совместимости
#
# 🎯 Главная страница теперь фокусируется на:
#    1. Презентации (hero с видео)
#    2. Навигации (категории)
#    3. Поддержке клиентов (FAQ)
#    А не на отображении товаров (это теперь в каталоге)