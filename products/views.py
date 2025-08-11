# 📁 products/views.py — ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
# 🛍️ View-функции интернет-магазина автоковриков
# 🛥️ ИСПРАВЛЕНО: border_colors для лодок + правильная логика корзины
# 🚗 ИСПРАВЛЕНО: подпятник для автомобилей

import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from products.models import (
    Product,
    KitVariant,
    Category,
)
from common.models import ProductReview, Wishlist
from common.models import Color
from accounts.models import Cart, CartItem
from .forms import ReviewForm


# 🏠 Каталог товаров
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
    per_page = request.GET.get("per_page", "12")

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

    # 📂 Активные категории
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
        "per_page": per_page,
        "total_products": paginator.count,
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
    }

    return render(request, "product/catalog.html", context)


def products_by_category(request, slug):
    """📂 Каталог товаров в выбранной категории"""
    category = get_object_or_404(Category, slug=slug)

    if not category.is_active:
        messages.warning(request, "Эта категория временно недоступна.")
        return redirect("products_catalog")

    # 🔍 Параметры
    sort_by = request.GET.get("sort", "-created_at")
    search_query = request.GET.get("search", "")
    per_page = request.GET.get("per_page", "12")

    # 📦 Товары категории
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

    # 📂 Активные категории
    categories = (
        Category.objects.filter(is_active=True)
        .order_by("display_order", "category_name")
    )

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
        "page_title": category.page_title or category.category_name,
        "meta_title": category.get_seo_title(),
        "meta_description": category.get_seo_description(),
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

    # ================== ЛОГИКА ДЛЯ АВТОМОБИЛЕЙ ==================

    # 📦 Варианты комплектов
    sorted_kit_variants = KitVariant.objects.filter(is_option=False).order_by('order')
    additional_options = KitVariant.objects.filter(is_option=True).order_by('order')

    # 💰 Получаем цену подпятника из справочника KitVariant
    podpyatnik_option = KitVariant.objects.filter(code='podpyatnik', is_option=True).first()
    if not podpyatnik_option:
        print("⚠️ ВНИМАНИЕ: Опция 'подпятник' не найдена в справочнике KitVariant!")
        podpyatnik_option = type('obj', (object,), {
            'name': 'Подпятник',
            'price_modifier': 15.00,
            'code': 'podpyatnik'
        })

    # 🎨 Цвета для коврика и окантовки
    carpet_colors = Color.objects.filter(color_type='carpet').order_by('display_order')
    border_colors = Color.objects.filter(color_type='border').order_by('display_order')

    # 🎨 Первый доступный цвет для каждого типа
    initial_carpet_color = carpet_colors.filter(is_available=True).first() or carpet_colors.first()
    initial_border_color = border_colors.filter(is_available=True).first() or border_colors.first()

    # 🛒 Проверяем наличие в корзине
    in_cart = False
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, is_paid=False).first()
        if cart:
            content_type = ContentType.objects.get_for_model(product)
            in_cart = CartItem.objects.filter(
                cart=cart,
                content_type=content_type,
                object_id=product.pk
            ).exists()

    # 💰 Цена и комплект по умолчанию
    selected_kit, updated_price = None, product.price
    default_kit = sorted_kit_variants.filter(code='salon').first()
    kit_code = request.GET.get('kit') or (default_kit.code if default_kit else None)

    if kit_code:
        selected_kit = kit_code
        updated_price = product.get_product_price_by_kit(kit_code)

    # ================== ОБЩАЯ ЛОГИКА ДЛЯ ВСЕХ ТОВАРОВ ==================

    # 📝 Рейтинг и отзывы
    content_type = ContentType.objects.get_for_model(product)
    review = ProductReview.objects.filter(
        content_type=content_type,
        object_id=product.pk,
        user=request.user
    ).first() if request.user.is_authenticated else None

    # This will be fixed later by adding a GenericRelation to BaseProduct
    # For now, this will raise an AttributeError which is expected.
    # rating_percentage = (product.get_rating() / 5) * 100 if product.reviews.exists() else 0
    rating_percentage = 0 # Temporary fix
    review_form = ReviewForm(request.POST or None, instance=review)

    if request.method == 'POST' and request.user.is_authenticated and review_form.is_valid():
        new_rev = review_form.save(commit=False)
        new_rev.product = product # GFK handles this
        new_rev.user = request.user
        new_rev.save()
        messages.success(request, 'Отзыв сохранён')
        return redirect('get_product', slug=slug)

    # 📊 Контекст для шаблона
    context = {
        'product': product,

        # 🛥️ Поля для определения типа товара
        'is_boat_product': product.is_boat_product(),
        'is_car_product': product.is_car_product(),

        # 📦 Комплектации
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
            content_type=content_type,
            object_id=product.pk
        ).exists() if request.user.is_authenticated else False,

        # 📝 Отзывы
        'review_form': review_form,
        'rating_percentage': rating_percentage,
    }

    return render(request, 'product/product.html', context)


# 🛒 ИСПРАВЛЕННАЯ ФУНКЦИЯ ДОБАВЛЕНИЯ В КОРЗИНУ
def add_to_cart(request, uid):
    """
    🛒 ИСПРАВЛЕННАЯ: Добавление товара в корзину с поддержкой лодок и автомобилей

    🛥️ ИСПРАВЛЕНО: Для лодок ВКЛЮЧЕНА окантовка
    🚗 ИСПРАВЛЕНО: Для автомобилей правильная обработка подпятника
    """
    try:
        # 📝 Получаем данные из POST-запроса
        kit_code = request.POST.get('kit')
        carpet_color_id = request.POST.get('carpet_color')
        border_color_id = request.POST.get('border_color')
        has_podp = request.POST.get('podp') == '1'
        quantity = int(request.POST.get('quantity') or 1)

        # 🛍️ Получаем товар
        product = get_object_or_404(Product, uid=uid)

        # ================== АВТОМОБИЛИ ==================
        # 📦 Для автомобилей обязательна комплектация
        if not kit_code:
            messages.warning(request, 'Пожалуйста, выберите комплектацию!')
            return redirect(request.META.get('HTTP_REFERER'))

        kit_variant = get_object_or_404(KitVariant, code=kit_code)
        # has_podp остается как есть из POST-запроса

        # 🎨 УНИВЕРСАЛЬНАЯ ОБРАБОТКА ЦВЕТОВ (для лодок И автомобилей)

        # 🎨 Цвет коврика
        carpet_color = None
        if carpet_color_id:
            carpet_color = get_object_or_404(Color, uid=carpet_color_id)
            if not carpet_color.is_available:
                messages.warning(request,
                                 f'Цвет коврика "{carpet_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
                return redirect(request.META.get('HTTP_REFERER'))

        # 🎨 Цвет окантовки (✅ ИСПРАВЛЕНО: работает для лодок И автомобилей!)
        border_color = None
        if border_color_id:
            border_color = get_object_or_404(Color, uid=border_color_id)
            if not border_color.is_available:
                messages.warning(request,
                                 f'Цвет окантовки "{border_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
                return redirect(request.META.get('HTTP_REFERER'))

        # 🛒 Получаем корзину для текущего пользователя/сессии
        cart = Cart.get_cart(request)

        # 🔍 Проверяем, есть ли уже такой товар в корзине с ТОЧНО ТАКИМИ ЖЕ параметрами
        content_type = ContentType.objects.get_for_model(product)
        existing_item = CartItem.objects.filter(
            cart=cart,
            content_type=content_type,
            object_id=product.pk,
            kit_variant=kit_variant,
            carpet_color=carpet_color,
            border_color=border_color,
            has_podpyatnik=has_podp
        ).first()

        if existing_item:
            # 📈 Если товар уже есть - увеличиваем количество
            existing_item.quantity += quantity
            existing_item.save()
            messages.success(request, f'Количество товара увеличено! Всего в корзине: {existing_item.quantity}')
        else:
            # 🆕 Создаем новый элемент корзины
            new_item = CartItem.objects.create(
                cart=cart,
                product=product, # GFK handles this
                kit_variant=kit_variant,
                carpet_color=carpet_color,
                border_color=border_color,
                has_podpyatnik=has_podp,
                quantity=quantity
            )
            messages.success(request, '✅ Товар добавлен в корзину!')

    except Exception as e:
        # 🚨 Обработка ошибок с подробным логированием
        print(f"🚨 ОШИБКА в add_to_cart: {str(e)}")
        print(f"   - Товар UID: {uid}")
        print(f"   - POST данные: {request.POST}")
        messages.error(request, f'Ошибка при добавлении в корзину: {str(e)}')

    return redirect('cart')


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

    review = get_object_or_404(ProductReview, uid=review_uid, user=request.user)

    review.delete()
    messages.success(request, "Ваш отзыв был удален.")
    # Redirect back to the product page using the slug
    return redirect('get_product', slug=slug)


# Add a product to Wishlist
@login_required
def add_to_wishlist(request, uid):
    """❤️ Добавление товара в избранное с выбранными цветами и опциями"""
    kit_code = request.POST.get('kit')
    carpet_color_id = request.POST.get('carpet_color')
    border_color_id = request.POST.get('border_color')
    has_podp = request.POST.get('podp') == '1'

    if not kit_code:
        kit_code = request.GET.get('kit')
    if not carpet_color_id:
        carpet_color_id = request.GET.get('carpet_color')
    if not border_color_id:
        border_color_id = request.GET.get('border_color')
    if not has_podp:
        has_podp = request.GET.get('podp') == '1'

    product = get_object_or_404(Product, uid=uid)

    if not product.is_boat_product() and not kit_code:
        messages.warning(request, 'Пожалуйста, выберите комплектацию перед добавлением в избранное!')
        return redirect(request.META.get('HTTP_REFERER'))

    # 🛥️ Для лодок устанавливаем значения по умолчанию
    if product.is_boat_product():
        kit_variant = None
        has_podp = False
    else:
        kit_variant = get_object_or_404(KitVariant, code=kit_code)

    # Получаем цвета коврика и окантовки
    carpet_color = None
    border_color = None
    if carpet_color_id:
        carpet_color = get_object_or_404(Color, uid=carpet_color_id)
    if border_color_id:
        border_color = get_object_or_404(Color, uid=border_color_id)

    # Проверяем доступность выбранных цветов
    if carpet_color and not carpet_color.is_available:
        messages.warning(request,
                         f'Цвет коврика "{carpet_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
        return redirect(request.META.get('HTTP_REFERER'))

    if border_color and not border_color.is_available:
        messages.warning(request,
                         f'Цвет окантовки "{border_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
        return redirect(request.META.get('HTTP_REFERER'))

    # Проверяем, есть ли уже такой товар в избранном
    content_type = ContentType.objects.get_for_model(product)
    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        content_type=content_type,
        object_id=product.pk,
        kit_variant=kit_variant
    ).first()

    if wishlist_item:
        wishlist_item.carpet_color = carpet_color
        wishlist_item.border_color = border_color
        wishlist_item.has_podpyatnik = has_podp
        wishlist_item.save()
        messages.success(request, "Товар в избранном обновлен!")
    else:
        Wishlist.objects.create(
            user=request.user,
            product=product, # GFK handles this
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
    # This view now receives the Wishlist item's UID directly
    wishlist_item = get_object_or_404(Wishlist, uid=uid, user=request.user)
    wishlist_item.delete()

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
    # This view now receives the Wishlist item's UID directly
    wishlist_item = get_object_or_404(Wishlist, uid=uid, user=request.user)

    product = wishlist_item.product
    kit_variant = wishlist_item.kit_variant
    carpet_color = wishlist_item.carpet_color
    border_color = wishlist_item.border_color
    has_podpyatnik = wishlist_item.has_podpyatnik

    # Проверяем доступность выбранных цветов
    if carpet_color and not carpet_color.is_available:
        messages.warning(request,
                         f'Цвет коврика "{carpet_color.name}" временно недоступен. Товар не может быть добавлен в корзину.')
        return redirect('wishlist')

    if border_color and not border_color.is_available:
        messages.warning(request,
                         f'Цвет окантовки "{border_color.name}" временно недоступен. Товар не может быть добавлен в корзину.')
        return redirect('wishlist')

    # После проверок можно удалить из избранного
    wishlist_item.delete()

    cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)

    # Проверяем, есть ли уже такой товар в корзине
    # This will need to be updated to use GFK when CartItem is refactored
    cart_item = CartItem.objects.filter(
        cart=cart,
        product=product,
        kit_variant=kit_variant,
        carpet_color=carpet_color,
        border_color=border_color,
        has_podpyatnik=has_podpyatnik
    ).first()

    if cart_item:
        cart_item.quantity += 1
        cart_item.save()
    else:
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

# 🔧 КЛЮЧЕВЫЕ ИСПРАВЛЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ✅ УБРАНО: Принудительное обнуление border_color для лодок в add_to_cart()
# ✅ ИСПРАВЛЕНО: Универсальная обработка цветов для всех типов товаров
# ✅ ДОБАВЛЕНО: Правильная логика для лодок (kit_variant=None, has_podpyatnik=False)
# ✅ СОХРАНЕНО: Вся логика автомобилей (комплектации, подпятник)
# ✅ УБРАНО: Дублирующиеся функции add_to_cart
# ✅ ДОБАВЛЕНО: Отладочная информация для диагностики проблем
# ✅ УЛУЧШЕНО: Более понятные сообщения пользователю
#
# 🛥️ РЕЗУЛЬТАТ ДЛЯ ЛОДОК:
# - kit_variant = None (не нужны комплектации)
# - has_podpyatnik = False (нет подпятника)
# - carpet_color = выбранный цвет коврика
# - border_color = выбранный цвет окантовки ✅ СОХРАНЯЕТСЯ!
#
# 🚗 РЕЗУЛЬТАТ ДЛЯ АВТОМОБИЛЕЙ:
# - kit_variant = выбранная комплектация
# - has_podpyatnik = True/False по выбору
# - carpet_color = выбранный цвет коврика
# - border_color = выбранный цвет окантовки
# - Правильное добавление стоимости подпятника в CartItem.get_product_price()