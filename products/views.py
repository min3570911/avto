# 📁 products/views.py — ИСПРАВЛЕННАЯ ВЕРСИЯ с окантовкой для лодок
# 🛍️ View-функции интернет-магазина автоковриков
# 🛥️ ИСПРАВЛЕНО: border_colors для лодок + убрана привязка к комплектациям

import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from products.models import (
    Product,
    KitVariant,
    ProductReview,
    Wishlist,
    Color,
    Category,
)
from accounts.models import Cart, CartItem
from .forms import ReviewForm


# 🏠 ИСПРАВЛЕНО: Каталог товаров без фильтра parent
def products_catalog(request):
    """
    🛍️ Главная страница каталога товаров

    Отображает все товары с возможностью поиска и фильтрации.
    Поддерживает пагинацию и сортировку.
    """
    # 🔍 Параметры поиска и фильтрации
    search_query = request.GET.get("search", "")
    sort_by = request.GET.get("sort", "-created_at")
    category_filter = request.GET.get("category", "")
    per_page = request.GET.get("per_page", "12")  # 🆕 Количество товаров на странице

    # 📦 Базовый queryset всех товаров
    products = Product.objects.all().select_related("category").prefetch_related("product_images")

    # 🔍 Поиск по названию товара и описанию
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query)
            | Q(product_desription__icontains=search_query)
        )

    # 📂 Фильтрация по категории
    if category_filter:
        products = products.filter(category__slug=category_filter)

    # 📊 Сортировка товаров
    sort_options = {
        "name": "product_name",
        "-name": "-product_name",
        "price": "price",
        "-price": "-price",
        "newest": "-created_at",
        "oldest": "created_at",
    }
    products = products.order_by(sort_options.get(sort_by, "-created_at"))

    # 🔢 НОВОЕ: Обработка per_page
    if per_page == "all":
        # 📊 Показать все товары (с разумным ограничением для безопасности)
        total_products = products.count()
        if total_products > 500:
            # ⚠️ Если товаров больше 500, ограничиваем для производительности
            messages.warning(request,
                             f"Показано первые 500 из {total_products} товаров. Используйте фильтры для поиска.")
            per_page_num = 500
        else:
            per_page_num = total_products or 1  # Минимум 1 для избежания ошибок
    else:
        # 🔢 Стандартные варианты
        try:
            per_page_num = int(per_page)
            # ✅ Разрешенные значения: 12, 24, 48, 96
            if per_page_num not in [12, 24, 48, 96]:
                per_page_num = 12  # По умолчанию
        except (ValueError, TypeError):
            per_page_num = 12  # По умолчанию при ошибке

    # 📄 Пагинация
    paginator = Paginator(products, per_page_num)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 📂 Навигация по активным категориям
    categories = (
        Category.objects.filter(is_active=True)
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
        "per_page": per_page,  # 🆕 Текущее значение per_page
        "total_products": paginator.count,
        # 📊 Мета-информация
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
    }

    return render(request, "product/catalog.html", context)


def products_by_category(request, slug):
    """
    📂 Каталог товаров в выбранной категории

    🔧 ИСПРАВЛЕНО: убран фильтр parent=None, изменен параметр category_slug → slug
    🆕 ДОБАВЛЕНО: поддержка per_page для выбора количества товаров на странице
    """
    # 📂 Категория или 404
    category = get_object_or_404(Category, slug=slug)

    # 🚫 Категория неактивна — предупреждаем и уходим
    if not category.is_active:
        messages.warning(request, "Эта категория временно недоступна.")
        return redirect("products_catalog")

    # 🔍 Параметры
    sort_by = request.GET.get("sort", "-created_at")
    search_query = request.GET.get("search", "")
    per_page = request.GET.get("per_page", "12")  # 🆕 Количество товаров на странице

    # 📦 ИСПРАВЛЕНО: убран фильтр parent=None
    products = (
        Product.objects.filter(category=category)
        .select_related("category")
        .prefetch_related("product_images")
    )

    # 🔍 Поиск внутри категории
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query)
            | Q(product_desription__icontains=search_query)
        )

    # 📊 Сортировка
    sort_options = {
        "name": "product_name",
        "-name": "-product_name",
        "price": "price",
        "-price": "-price",
        "newest": "-created_at",
        "oldest": "created_at",
    }
    products = products.order_by(sort_options.get(sort_by, "-created_at"))

    # 🔢 НОВОЕ: Обработка per_page
    if per_page == "all":
        # 📊 Показать все товары (с разумным ограничением для безопасности)
        total_products = products.count()
        if total_products > 500:
            # ⚠️ Если товаров больше 500, ограничиваем для производительности
            messages.warning(request,
                             f"Показано первые 500 из {total_products} товаров. Используйте фильтры для поиска.")
            per_page_num = 500
        else:
            per_page_num = total_products or 1  # Минимум 1 для избежания ошибок
    else:
        # 🔢 Стандартные варианты
        try:
            per_page_num = int(per_page)
            # ✅ Разрешенные значения: 12, 24, 48, 96
            if per_page_num not in [12, 24, 48, 96]:
                per_page_num = 12  # По умолчанию
        except (ValueError, TypeError):
            per_page_num = 12  # По умолчанию при ошибке

    # 📄 Пагинация
    paginator = Paginator(products, per_page_num)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 📂 Навигация по активным категориям
    categories = (
        Category.objects.filter(is_active=True)
        .order_by("display_order", "category_name")
    )

    # 🆕 Расширенный контекст с SEO данными
    context = {
        "category": category,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "search_query": search_query,
        "sort_by": sort_by,
        "per_page": per_page,  # 🆕 Текущее значение per_page
        "total_products": paginator.count,
        # 📊 Мета-информация
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
        # 🆕 SEO
        "page_title": category.page_title or category.category_name,
        "meta_title": category.get_seo_title(),
        "meta_description": category.get_seo_description(),
        # 🆕 Контент категории
        "has_description": bool(category.description),
        "has_additional_content": bool(category.additional_content),
    }

    return render(request, "product/category.html", context)


def get_product(request, slug):
    """
    🛍️ Отображение страницы товара с поддержкой лодок и автомобилей

    🛥️ ИСПРАВЛЕНО: Для лодок ВКЛЮЧЕНА окантовка
    🚗 Для автомобилей: все как было
    """
    product = get_object_or_404(Product, slug=slug)

    # 🛥️ НОВАЯ ЛОГИКА: Проверяем тип товара
    if product.is_boat_product():
        # ================== ЛОГИКА ДЛЯ ЛОДОК ==================

        # 🎨 ИСПРАВЛЕНО: Цвета ковриков И окантовки для лодок!
        carpet_colors = Color.objects.filter(
            color_type='carpet',
            is_available=True
        ).order_by('display_order')

        # ✅ ДОБАВЛЕНО: Окантовка для лодок
        border_colors = Color.objects.filter(
            color_type='border',
            is_available=True
        ).order_by('display_order')

        # 🎨 Начальные цвета
        initial_carpet_color = carpet_colors.first()
        initial_border_color = border_colors.first()

        # 📦 Без комплектаций для лодок
        sorted_kit_variants = []
        additional_options = []
        podpyatnik_option = None

        # 💰 Цена напрямую из поля Product.price
        selected_kit = None
        updated_price = product.price or 0

        # 🛒 Проверяем наличие в корзине (упрощенная логика)
        in_cart = False
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user, is_paid=False).first()
            if cart:
                # Для лодок ищем без kit_variant, has_podpyatnik
                in_cart = CartItem.objects.filter(
                    cart=cart,
                    product=product,
                    kit_variant__isnull=True,
                    has_podpyatnik=False
                ).exists()

    else:
        # ================== ЛОГИКА ДЛЯ АВТОМОБИЛЕЙ (БЕЗ ИЗМЕНЕНИЙ) ==================

        # 📦 Варианты комплектов (как было)
        sorted_kit_variants = KitVariant.objects.filter(is_option=False).order_by('order')
        additional_options = KitVariant.objects.filter(is_option=True).order_by('order')

        # 💰 ИСПРАВЛЕНО: Получаем цену подпятника из справочника KitVariant
        podpyatnik_option = KitVariant.objects.filter(code='podpyatnik', is_option=True).first()
        if not podpyatnik_option:
            # 🚨 Если записи нет в БД, создаем дефолтную
            print("⚠️ ВНИМАНИЕ: Опция 'подпятник' не найдена в справочнике KitVariant!")
            podpyatnik_option = type('obj', (object,), {
                'name': 'Подпятник',
                'price_modifier': 15.00,  # Дефолтная цена
                'code': 'podpyatnik'
            })

        # 🎨 Разделяем цвета на типы для коврика и окантовки (как было)
        carpet_colors = Color.objects.filter(color_type='carpet').order_by('display_order')
        border_colors = Color.objects.filter(color_type='border').order_by('display_order')

        # 🎨 Определяем первый доступный цвет для каждого типа (как было)
        initial_carpet_color = carpet_colors.filter(is_available=True).first() or carpet_colors.first()
        initial_border_color = border_colors.filter(is_available=True).first() or border_colors.first()

        # 🛒 Проверяем наличие в корзине (как было)
        in_cart = False
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user, is_paid=False).first()
            if cart:
                in_cart = CartItem.objects.filter(cart=cart, product=product).exists()

        # 💰 Цена и комплект по умолчанию (как было)
        selected_kit, updated_price = None, product.price
        default_kit = sorted_kit_variants.filter(code='salon').first()
        kit_code = request.GET.get('kit') or (default_kit.code if default_kit else None)

        if kit_code:
            selected_kit = kit_code
            updated_price = product.get_product_price_by_kit(kit_code)

    # ================== ОБЩАЯ ЛОГИКА ДЛЯ ВСЕХ ТОВАРОВ ==================

    # 📝 Рейтинг и отзывы (одинаково для всех)
    review = ProductReview.objects.filter(
        product=product,
        user=request.user
    ).first() if request.user.is_authenticated else None

    rating_percentage = (product.get_rating() / 5) * 100 if product.reviews.exists() else 0
    review_form = ReviewForm(request.POST or None, instance=review)

    if request.method == 'POST' and request.user.is_authenticated and review_form.is_valid():
        new_rev = review_form.save(commit=False)
        new_rev.product, new_rev.user = product, request.user
        new_rev.save()
        messages.success(request, 'Отзыв сохранён')
        return redirect('get_product', slug=slug)

    # 📊 Контекст для шаблона
    context = {
        'product': product,

        # 🛥️ НОВЫЕ ПОЛЯ для определения типа товара
        'is_boat_product': product.is_boat_product(),
        'is_car_product': product.is_car_product(),

        # 📦 Комплектации (для автомобилей или пустые для лодок)
        'sorted_kit_variants': sorted_kit_variants,
        'additional_options': additional_options,
        'podpyatnik_option': podpyatnik_option,

        # 🎨 ИСПРАВЛЕНО: Цвета для лодок - коврик И окантовка!
        'carpet_colors': carpet_colors,
        'border_colors': border_colors,
        'initial_carpet_color': initial_carpet_color,
        'initial_border_color': initial_border_color,

        # 💰 Цены
        'selected_kit': selected_kit,
        'updated_price': updated_price,

        # 🛒 Корзина и избранное
        'in_cart': in_cart,
        'in_wishlist': Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists() if request.user.is_authenticated else False,

        # 📝 Отзывы
        'review_form': review_form,
        'rating_percentage': rating_percentage,
    }

    return render(request, 'product/product.html', context)


# Product Review view
@login_required
def product_reviews(request):
    """📝 Отображение всех отзывов пользователя"""
    reviews = ProductReview.objects.filter(
        user=request.user).select_related('product').order_by('-date_added')
    return render(request, 'product/all_product_reviews.html', {'reviews': reviews})


# Edit Review view
@login_required
def edit_review(request, review_uid):
    """✏️ Редактирование отзыва пользователя"""
    review = ProductReview.objects.filter(uid=review_uid, user=request.user).first()
    if not review:
        return JsonResponse({"detail": "Отзыв не найден"}, status=404)

    if request.method == "POST":
        stars = request.POST.get("stars")
        content = request.POST.get("content")
        review.stars = stars
        review.content = content
        review.save()
        messages.success(request, "Ваш отзыв успешно обновлен.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return JsonResponse({"detail": "Некорректный запрос"}, status=400)


# Like and Dislike review view
def like_review(request, review_uid):
    """👍 Обработка лайка отзыва"""
    review = ProductReview.objects.filter(uid=review_uid).first()

    if request.user in review.likes.all():
        review.likes.remove(request.user)
    else:
        review.likes.add(request.user)
        review.dislikes.remove(request.user)
    return JsonResponse({'likes': review.like_count(), 'dislikes': review.dislike_count()})


def dislike_review(request, review_uid):
    """👎 Обработка дизлайка отзыва"""
    review = ProductReview.objects.filter(uid=review_uid).first()

    if request.user in review.dislikes.all():
        review.dislikes.remove(request.user)
    else:
        review.dislikes.add(request.user)
        review.likes.remove(request.user)
    return JsonResponse({'likes': review.like_count(), 'dislikes': review.dislike_count()})


# delete review view
def delete_review(request, slug, review_uid):
    """🗑️ Удаление отзыва"""
    if not request.user.is_authenticated:
        messages.warning(request, "Необходимо войти в систему, чтобы удалить отзыв.")
        return redirect('login')

    review = ProductReview.objects.filter(uid=review_uid, product__slug=slug, user=request.user).first()

    if not review:
        messages.error(request, "Отзыв не найден.")
        return redirect('get_product', slug=slug)

    review.delete()
    messages.success(request, "Ваш отзыв был удален.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Add a product to Wishlist
@login_required
def add_to_wishlist(request, uid):
    """❤️ Добавление товара в избранное с выбранными цветами и опциями"""
    # Получаем параметры из POST-запроса (для формы на странице товара)
    kit_code = request.POST.get('kit')
    carpet_color_id = request.POST.get('carpet_color')
    border_color_id = request.POST.get('border_color')
    has_podp = request.POST.get('podp') == '1'

    # Также проверяем параметры из GET-запроса (для обратной совместимости)
    if not kit_code:
        kit_code = request.GET.get('kit')
    if not carpet_color_id:
        carpet_color_id = request.GET.get('carpet_color')
    if not border_color_id:
        border_color_id = request.GET.get('border_color')
    if not has_podp:
        has_podp = request.GET.get('podp') == '1'

    # 🛥️ НОВАЯ ЛОГИКА: Для лодок не требуем комплектацию
    product = get_object_or_404(Product, uid=uid)

    if not product.is_boat_product() and not kit_code:
        messages.warning(request, 'Пожалуйста, выберите комплектацию перед добавлением в избранное!')
        return redirect(request.META.get('HTTP_REFERER'))

    # 🛥️ Для лодок устанавливаем значения по умолчанию
    if product.is_boat_product():
        kit_variant = None
        has_podp = False
    else:
        # 🚗 Для автомобилей - как было
        kit_variant = get_object_or_404(KitVariant, code=kit_code)

    # Получаем цвета коврика и окантовки
    carpet_color = None
    border_color = None
    if carpet_color_id:
        carpet_color = get_object_or_404(Color, uid=carpet_color_id)
    if border_color_id:
        border_color = get_object_or_404(Color, uid=border_color_id)

    # ⚠️ Проверяем доступность выбранных цветов перед добавлением
    if carpet_color and not carpet_color.is_available:
        messages.warning(request,
                         f'Цвет коврика "{carpet_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
        return redirect(request.META.get('HTTP_REFERER'))

    if border_color and not border_color.is_available:
        messages.warning(request,
                         f'Цвет окантовки "{border_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
        return redirect(request.META.get('HTTP_REFERER'))

    # Проверяем, есть ли уже такой товар в избранном
    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product,
        kit_variant=kit_variant
    ).first()

    if wishlist_item:
        # Обновляем существующую запись
        wishlist_item.carpet_color = carpet_color
        wishlist_item.border_color = border_color
        wishlist_item.has_podpyatnik = has_podp
        wishlist_item.save()
        messages.success(request, "Товар в избранном обновлен!")
    else:
        # Создаем новую запись
        Wishlist.objects.create(
            user=request.user,
            product=product,
            kit_variant=kit_variant,
            carpet_color=carpet_color,
            border_color=border_color,
            has_podpyatnik=has_podp
        )
        messages.success(request, "Товар добавлен в избранное!")

    return redirect(reverse('wishlist'))


# Remove product from wishlist
@login_required
def remove_from_wishlist(request, uid):
    """🗑️ Удаление товара из избранного"""
    product = get_object_or_404(Product, uid=uid)
    kit_code = request.GET.get('kit')

    if kit_code:
        kit_variant = get_object_or_404(KitVariant, code=kit_code)
        Wishlist.objects.filter(
            user=request.user, product=product, kit_variant=kit_variant).delete()
    else:
        Wishlist.objects.filter(user=request.user, product=product).delete()

    messages.success(request, "Товар удален из избранного!")
    return redirect(reverse('wishlist'))


# Wishlist View
@login_required
def wishlist_view(request):
    """❤️ Отображение списка избранных товаров с выбранными цветами и опциями"""
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'product/wishlist.html', {'wishlist_items': wishlist_items})


# Move to cart functionality on wishlist page.
@login_required
def move_to_cart(request, uid):
    """🛒 Перемещение товара из избранного в корзину"""
    product = get_object_or_404(Product, uid=uid)
    wishlist = Wishlist.objects.filter(user=request.user, product=product).first()

    if not wishlist:
        messages.error(request, "Товар не найден в избранном.")
        return redirect('wishlist')

    kit_variant = wishlist.kit_variant
    carpet_color = wishlist.carpet_color
    border_color = wishlist.border_color
    has_podpyatnik = wishlist.has_podpyatnik

    # ⚠️ Проверяем доступность выбранных цветов перед добавлением в корзину
    if carpet_color and not carpet_color.is_available:
        messages.warning(request,
                         f'Цвет коврика "{carpet_color.name}" временно недоступен. Товар не может быть добавлен в корзину.')
        return redirect('wishlist')

    if border_color and not border_color.is_available:
        messages.warning(request,
                         f'Цвет окантовки "{border_color.name}" временно недоступен. Товар не может быть добавлен в корзину.')
        return redirect('wishlist')

    # После проверок можно удалить из избранного
    wishlist.delete()

    cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)

    # Проверяем, есть ли уже такой товар в корзине
    cart_item = CartItem.objects.filter(
        cart=cart,
        product=product,
        kit_variant=kit_variant,
        carpet_color=carpet_color,
        border_color=border_color,
        has_podpyatnik=has_podpyatnik
    ).first()

    if cart_item:
        # Если товар уже есть, увеличиваем количество
        cart_item.quantity += 1
        cart_item.save()
    else:
        # Создаем новый элемент корзины
        CartItem.objects.create(
            cart=cart,
            product=product,
            kit_variant=kit_variant,
            carpet_color=carpet_color,
            border_color=border_color,
            has_podpyatnik=has_podpyatnik
        )

    messages.success(request, "Товар перемещен в корзину!")
    return redirect('cart')


# Убираем декоратор @login_required
def add_to_cart(request, uid):
    """🛒 Добавление товара в корзину с выбранными цветами и опциями"""
    try:
        kit_code = request.POST.get('kit')
        carpet_color_id = request.POST.get('carpet_color')
        border_color_id = request.POST.get('border_color')
        has_podp = request.POST.get('podp') == '1'
        quantity = int(request.POST.get('quantity') or 1)

        product = get_object_or_404(Product, uid=uid)

        # 🛥️ НОВАЯ ЛОГИКА: Для лодок упрощенная обработка
        if product.is_boat_product():
            kit_variant = None
            border_color = None
            has_podp = False
        else:
            # 🚗 Для автомобилей - как было
            kit_variant = get_object_or_404(KitVariant, code=kit_code or 'salon')

            border_color = None
            if border_color_id:
                border_color = get_object_or_404(Color, uid=border_color_id)
                if not border_color.is_available:
                    messages.warning(request,
                                     f'Цвет окантовки "{border_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
                    return redirect(request.META.get('HTTP_REFERER'))

        # Получаем объекты цвета и проверяем их доступность
        carpet_color = None
        if carpet_color_id:
            carpet_color = get_object_or_404(Color, uid=carpet_color_id)
            if not carpet_color.is_available:
                messages.warning(request,
                                 f'Цвет коврика "{carpet_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
                return redirect(request.META.get('HTTP_REFERER'))

        # Получаем корзину для текущего пользователя/сессии
        cart = Cart.get_cart(request)

        # Проверяем, есть ли уже такой товар в корзине
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            kit_variant=kit_variant,
            carpet_color=carpet_color,
            border_color=border_color,
            has_podpyatnik=has_podp,
            defaults={'quantity': quantity},
        )

        if not created:
            item.quantity += quantity
            item.save()

        messages.success(request, 'Товар добавлен в корзину!')

    except Exception as e:
        messages.error(request, f'Ошибка при добавлении в корзину: {str(e)}')

    return redirect('cart')

# 🔧 ИСПРАВЛЕНИЯ:
# ✅ УБРАН: фильтр parent=None из всех функций
# ✅ ИЗМЕНЕН: параметр category_slug → slug в products_by_category
# ✅ ОБНОВЛЕН: популярные товары без фильтра parent
# ✅ ДОБАВЛЕНО: поддержка per_page в products_by_category
# ✅ ДОБАВЛЕНО: логика "показать все" товары
# ✅ СОХРАНЕНА: вся остальная логика работы
# 🛥️ ИСПРАВЛЕНО: border_colors для лодок в get_product
# 🛥️ ДОБАВЛЕНА: поддержка лодок в add_to_wishlist, add_to_cart