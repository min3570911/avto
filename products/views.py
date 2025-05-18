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
    product = get_object_or_404(Product, slug=slug)

    # варианты комплектов
    sorted_kit_variants = KitVariant.objects.filter(is_option=False).order_by('order')
    additional_options  = KitVariant.objects.filter(is_option=True ).order_by('order')

    # цвета
    colors = Color.objects.all().order_by('display_order')

    # похожие товары
    related_products = list(product.category.products.filter(parent=None).exclude(uid=product.uid))
    if len(related_products) >= 4:
        related_products = random.sample(related_products, 4)

    # рейтинг / отзыв текущего пользователя
    review = ProductReview.objects.filter(product=product, user=request.user).first() if request.user.is_authenticated else None
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
    kit_code    = request.GET.get('kit') or (default_kit.code if default_kit else None)

    if kit_code:
        selected_kit = kit_code
        updated_price = product.get_product_price_by_kit(kit_code)

    context = {
        'product'              : product,
        'sorted_kit_variants'  : sorted_kit_variants,
        'additional_options'   : additional_options,
        'related_products'     : related_products,
        'review_form'          : review_form,
        'rating_percentage'    : rating_percentage,
        'in_wishlist'          : Wishlist.objects.filter(user=request.user, product=product).exists() if request.user.is_authenticated else False,
        'colors'               : colors,
        'in_cart'              : in_cart,
        'selected_kit'         : selected_kit,
        'updated_price'        : updated_price,
    }

    return render(request, 'product/product.html', context)

# Product Review view
@login_required
def product_reviews(request):
    reviews = ProductReview.objects.filter(
        user=request.user).select_related('product').order_by('-date_added')
    return render(request, 'product/all_product_reviews.html', {'reviews': reviews})


# Edit Review view
@login_required
def edit_review(request, review_uid):
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
    review = ProductReview.objects.filter(uid=review_uid).first()

    if request.user in review.likes.all():
        review.likes.remove(request.user)
    else:
        review.likes.add(request.user)
        review.dislikes.remove(request.user)
    return JsonResponse({'likes': review.like_count(), 'dislikes': review.dislike_count()})


def dislike_review(request, review_uid):
    review = ProductReview.objects.filter(uid=review_uid).first()

    if request.user in review.dislikes.all():
        review.dislikes.remove(request.user)
    else:
        review.dislikes.add(request.user)
        review.likes.remove(request.user)
    return JsonResponse({'likes': review.like_count(), 'dislikes': review.dislike_count()})


# delete review view
def delete_review(request, slug, review_uid):
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
    kit_code = request.GET.get('kit')
    carpet_color_id = request.GET.get('carpet_color')
    border_color_id = request.GET.get('border_color')
    has_podp = request.GET.get('podp') == '1'

    if not kit_code:
        messages.warning(request, 'Пожалуйста, выберите комплектацию перед добавлением в избранное!')
        return redirect(request.META.get('HTTP_REFERER'))

    product = get_object_or_404(Product, uid=uid)
    kit_variant = get_object_or_404(KitVariant, code=kit_code)

    # Получаем цвета из базы данных, если они выбраны
    carpet_color = None
    border_color = None
    if carpet_color_id:
        carpet_color = get_object_or_404(Color, uid=carpet_color_id)
    if border_color_id:
        border_color = get_object_or_404(Color, uid=border_color_id)

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
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'product/wishlist.html', {'wishlist_items': wishlist_items})


# Move to cart functionality on wishlist page.
def move_to_cart(request, uid):
    product = get_object_or_404(Product, uid=uid)
    wishlist = Wishlist.objects.filter(user=request.user, product=product).first()

    if not wishlist:
        messages.error(request, "Товар не найден в избранном.")
        return redirect('wishlist')

    kit_variant = wishlist.kit_variant
    carpet_color = wishlist.carpet_color
    border_color = wishlist.border_color
    has_podpyatnik = wishlist.has_podpyatnik

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


@login_required
def add_to_cart(request, uid):
    # Получаем данные из POST-запроса
    kit_code = request.POST.get('kit')
    carpet_color_id = request.POST.get('carpet_color')
    border_color_id = request.POST.get('border_color')
    has_podp = request.POST.get('podp') == '1'
    quantity = int(request.POST.get('quantity', 1))  # Получаем количество из запроса

    # Получаем объекты из базы данных
    product = get_object_or_404(Product, uid=uid)

    # Если kit_code не передан, выбираем "Салон" по умолчанию
    if not kit_code:
        kit_variant = KitVariant.objects.filter(code='salon').first()
        if not kit_variant:  # Проверяем, существует ли комплектация "Салон"
            messages.error(request, "Комплектация 'Салон' не найдена.")
            return redirect('get_product', slug=product.slug)  # Редирект на страницу товара
    else:
        kit_variant = get_object_or_404(KitVariant, code=kit_code)

    carpet_color = get_object_or_404(Color, uid=carpet_color_id) if carpet_color_id else None
    border_color = get_object_or_404(Color, uid=border_color_id) if border_color_id else None

    # Получаем или создаем корзину пользователя
    cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)

    # Проверяем, есть ли уже такой товар в корзине
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        kit_variant=kit_variant,
        carpet_color=carpet_color,
        border_color=border_color,
        has_podpyatnik=has_podp,
        defaults={'quantity': quantity}  # Устанавливаем количество при создании
    )

    if not item_created:
        # Если товар уже есть, увеличиваем количество
        cart_item.quantity += quantity
        cart_item.save()

    messages.success(request, "Товар добавлен в корзину!")
    return redirect('cart')