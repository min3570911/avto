# 📁 home/views.py - ФИНАЛЬНАЯ ВЕРСИЯ с CompanyDescription
# 🆕 ДОБАВЛЕНО: Получение описания компании для главной страницы
# ✅ СОХРАНЕНО: Все существующие функции без изменений

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from references.models import Product, Category, KitVariant, ProductImage
from .models import FAQ, HeroSection, CompanyDescription
import random


def index(request):
    """
    🏠 Главная страница - ФИНАЛЬНАЯ версия с описанием компании

    Структура главной страницы:
    - Hero-секция с видео и преимуществами
    - 📝 Описание компании (новое)
    - Компактный каталог категорий
    - Галерея примеров работ (неглавные фото товаров)
    - FAQ для аккордеона

    🆕 ДОБАВЛЕНО: Получение описания компании CompanyDescription
    """

    # 🎬 Получаем активную hero-секцию с преимуществами
    hero_section = None
    try:
        hero_section = HeroSection.objects.filter(is_active=True).prefetch_related('advantages').first()
    except HeroSection.DoesNotExist:
        pass  # 🔄 Будем отображать дефолтную секцию

    # 📝 Получаем описание компании (только одно)
    company_description = CompanyDescription.objects.first()

    # 📂 Получаем только активные категории для каталога
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'category_name')

    # ❓ Получаем активные FAQ для аккордеона
    faqs = FAQ.objects.filter(is_active=True).order_by('order', 'created_at')

    # 📦 Комплектация "Салон" (для совместимости с существующим кодом)
    salon_kit = KitVariant.objects.filter(code='salon').first()

    # 🎲 Получаем случайные неглавные изображения для галереи
    gallery_images = get_random_product_gallery_images()

    # 📊 Контекст для шаблона
    context = {
        # 🎬 Hero-секция
        'hero_section': hero_section,

        # 📝 Описание компании
        'company_description': company_description,

        # 📂 Каталог категорий
        'categories': categories,

        # ❓ FAQ для аккордеона
        'faqs': faqs,

        # 🎨 Галерея примеров работ
        'gallery_images': gallery_images,

        # 📦 Совместимость (для существующих элементов, если нужно)
        'salon_kit': salon_kit,

        # 📊 Дополнительная информация для шаблона
        'categories_count': categories.count(),
        'faqs_count': faqs.count(),
        'gallery_count': len(gallery_images),
    }

    return render(request, 'home/index.html', context)


def get_random_product_gallery_images(count=12):
    """
    🎲 Получает случайные неглавные изображения товаров для галереи

    Args:
        count (int): Количество изображений для галереи (по умолчанию 12)

    Returns:
        list: Список объектов ProductImage с дополнительной информацией о товаре

    🎯 Логика:
    1. Получаем все товары с изображениями и категориями
    2. Для каждого товара берем только неглавные изображения (пропускаем первое)
    3. Делаем случайную выборку из всех неглавных изображений
    4. Добавляем информацию о товаре к каждому изображению
    """

    # 📸 Получаем все неглавные изображения товаров
    all_secondary_images = []

    # 🔍 Получаем товары с изображениями и категориями (исключаем товары без категории)
    products_with_images = Product.objects.filter(
        category__isnull=False  # ✅ ИСПРАВЛЕНО: убрана фильтрация по is_active
    ).prefetch_related('product_images').select_related('category')

    for product in products_with_images:
        # 📱 Получаем все изображения товара
        product_images = list(product.product_images.all())

        # 🎯 Берем только неглавные изображения (пропускаем первое)
        if len(product_images) > 1:
            secondary_images = product_images[1:]  # Все кроме первого

            # 🏷️ Добавляем информацию о товаре к каждому изображению
            for image in secondary_images:
                # 📦 Расширяем объект изображения информацией о товаре
                image.product_name = product.product_name
                image.product_slug = product.slug
                image.product_category = product.category.category_name if product.category else "Автоковрики"
                all_secondary_images.append(image)

    # 🎲 Делаем случайную выборку
    if len(all_secondary_images) > count:
        selected_images = random.sample(all_secondary_images, count)
    else:
        # 📊 Если изображений меньше чем нужно, возвращаем все
        selected_images = all_secondary_images

    # 🔄 Перемешиваем для разнообразия
    random.shuffle(selected_images)

    return selected_images


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

    # 🔄 Здесь можно добавить получение описания категории из базы данных или CMS
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
    # 📝 МОЖНО ДОПОЛНИТЬ: Получение описания компании для страницы "О нас"
    company_description = CompanyDescription.objects.first()

    context = {
        'company_description': company_description,
    }

    return render(request, 'home/about.html', context)


def privacy_policy(request):
    """📜 Страница политики конфиденциальности"""
    return render(request, 'home/privacy_policy.html')


def terms_and_conditions(request):
    """📄 Страница условий использования"""
    return render(request, 'home/terms_and_conditions.html')

# 🔧 ИТОГОВЫЕ ИЗМЕНЕНИЯ В ФАЙЛЕ:
#
# 🆕 В функции index():
#   ✅ ДОБАВЛЕНО: company_description = CompanyDescription.objects.first()
#   ✅ ДОБАВЛЕНО: 'company_description' в контекст шаблона
#   ✅ СОХРАНЕНО: все существующие данные (hero_section, categories, faqs, gallery_images)
#
# 🆕 В функции about():
#   ✅ ДОБАВЛЕНО: получение описания компании для страницы "О нас"
#   ✅ ЛОГИКА: можно использовать то же описание на разных страницах
#
# 📊 Новые поля в контексте:
#   - company_description: описание компании (только одно)
#
# 🎯 Особенности реализации:
#   ✅ Простое получение одного объекта через .first()
#   ✅ Безопасное использование - может быть None
#   ✅ Совместимость с существующим кодом
#   ✅ Возможность использования на других страницах (about)