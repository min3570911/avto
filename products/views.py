import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from products.models import Product, KitVariant, ProductReview, Wishlist, Color
from accounts.models import Cart, CartItem
from .forms import ReviewForm


# -----------------------------  карточка товара  ----------------------------- #
def get_product(request, slug):
    """
    🛍️ Отображение страницы товара с возможностью выбора цветов, комплектации и опций

    Получает товар по слагу и подготавливает все необходимые данные:
    - варианты комплектации, цветов, опций
    - цены и описания
    - системы отзывов
    - связанные товары

    🔍 Разделяет цвета на типы (для коврика и окантовки)
    """
    product = get_object_or_404(Product, slug=slug)

    # варианты комплектов
    sorted_kit_variants = KitVariant.objects.filter(is_option=False).order_by('order')
    additional_options = KitVariant.objects.filter(is_option=True).order_by('order')

    # 🎨 разделяем цвета на типы для коврика и окантовки
    carpet_colors = Color.objects.filter(color_type='carpet').order_by('display_order')
    border_colors = Color.objects.filter(color_type='border').order_by('display_order')

    # Определяем первый доступный цвет для каждого типа (для начального выбора)
    initial_carpet_color = carpet_colors.filter(is_available=True).first() or carpet_colors.first()
    initial_border_color = border_colors.filter(is_available=True).first() or border_colors.first()

    # похожие товары
    related_products = list(product.category.products.filter(parent=None).exclude(uid=product.uid))
    if len(related_products) >= 4:
        related_products = random.sample(related_products, 4)

    # рейтинг / отзыв текущего пользователя
    review = ProductReview.objects.filter(product=product,
                                          user=request.user).first() if request.user.is_authenticated else None
    rating_percentage = (product.get_rating() / 5) * 100 if product.reviews.exists() else 0
    review_form = ReviewForm(request.POST or None, instance=review)

    if request.method == 'POST' and request.user.is_authenticated and review_form.is_valid():
        new_rev = review_form.save(commit=False)
        new_rev.product, new_rev.user = product, request.user
        new_rev.save()
        messages.success(request, 'Отзыв сохранён')
        return redirect('get_product', slug=slug)

    # ----------  определяем, лежит ли товар уже в корзине пользователя  ----------
    in_cart = False
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, is_paid=False).first()
        if cart:
            in_cart = CartItem.objects.filter(cart=cart, product=product).exists()

    # ----------  цена и комплект по умолчанию  ----------
    selected_kit, updated_price = None, product.price
    default_kit = sorted_kit_variants.filter(code='salon').first()
    kit_code = request.GET.get('kit') or (default_kit.code if default_kit else None)

    if kit_code:
        selected_kit = kit_code
        updated_price = product.get_product_price_by_kit(kit_code)

    context = {
        'product': product,
        'sorted_kit_variants': sorted_kit_variants,
        'additional_options': additional_options,
        'related_products': related_products,
        'review_form': review_form,
        'rating_percentage': rating_percentage,
        'in_wishlist': Wishlist.objects.filter(user=request.user,
                                               product=product).exists() if request.user.is_authenticated else False,
        'carpet_colors': carpet_colors,  # 🎨 Добавляем цвета ковриков
        'border_colors': border_colors,  # 🎨 Добавляем цвета окантовки
        'initial_carpet_color': initial_carpet_color,  # 🎨 Начальный цвет коврика
        'initial_border_color': initial_border_color,  # 🎨 Начальный цвет окантовки
        'in_cart': in_cart,
        'selected_kit': selected_kit,
        'updated_price': updated_price,
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

    if not kit_code:
        messages.warning(request, 'Пожалуйста, выберите комплектацию перед добавлением в избранное!')
        return redirect(request.META.get('HTTP_REFERER'))

    # Получаем объекты из БД
    product = get_object_or_404(Product, uid=uid)
    kit_variant = get_object_or_404(KitVariant, code=kit_code)

    # Получаем цвета из базы данных, если они выбраны
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
        kit_variant = get_object_or_404(KitVariant, code=kit_code or 'salon')

        # Получаем объекты цвета и проверяем их доступность
        carpet_color = None
        if carpet_color_id:
            carpet_color = get_object_or_404(Color, uid=carpet_color_id)
            if not carpet_color.is_available:
                messages.warning(request,
                                f'Цвет коврика "{carpet_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
                return redirect(request.META.get('HTTP_REFERER'))

        border_color = None
        if border_color_id:
            border_color = get_object_or_404(Color, uid=border_color_id)
            if not border_color.is_available:
                messages.warning(request,
                                f'Цвет окантовки "{border_color.name}" временно недоступен. Пожалуйста, выберите другой цвет.')
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