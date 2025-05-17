import random
from .forms import ReviewForm
from django.urls import reverse
from django.contrib import messages
from accounts.models import Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product, KitVariant, ProductReview, Wishlist, Color


# Create your views here.

def get_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    # Берем все комплектации из справочника, отсортированные по порядку
    # Фильтруем только обычные комплектации (не дополнительные опции)
    sorted_kit_variants = KitVariant.objects.filter(is_option=False).order_by('order')

    # Получаем дополнительные опции (подпятник)
    additional_options = KitVariant.objects.filter(is_option=True).order_by('order')

    # Получаем связанные товары из той же категории
    related_products = list(product.category.products.filter(parent=None).exclude(uid=product.uid))

    # Получаем все доступные цвета для выбора
    colors = Color.objects.all().order_by('display_order')

    # Review product view
    review = None
    if request.user.is_authenticated:
        try:
            review = ProductReview.objects.filter(product=product, user=request.user).first()
        except Exception as e:
            print("Отзывы для этого товара не найдены", str(e))
            messages.warning(request, "Отзывы для этого товара не найдены")

    rating_percentage = 0
    if product.reviews.exists():
        rating_percentage = (product.get_rating() / 5) * 100

    if request.method == 'POST' and request.user.is_authenticated:
        if review:
            # Если отзыв существует, обновляем его
            review_form = ReviewForm(request.POST, instance=review)
        else:
            # Иначе создаем новый отзыв
            review_form = ReviewForm(request.POST)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Отзыв успешно добавлен!")
            return redirect('get_product', slug=slug)
    else:
        review_form = ReviewForm()

    # Ограничиваем количество связанных товаров
    if len(related_products) >= 4:
        related_products = random.sample(related_products, 4)

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    context = {
        'product': product,
        'sorted_kit_variants': sorted_kit_variants,
        'additional_options': additional_options,
        'related_products': related_products,
        'review_form': review_form,
        'rating_percentage': rating_percentage,
        'in_wishlist': in_wishlist,
        'colors': colors,
    }

    # По умолчанию выбираем "Салон"
    default_kit = sorted_kit_variants.filter(code='salon').first()
    if default_kit and not request.GET.get('kit'):
        context['selected_kit'] = default_kit.code
        context['updated_price'] = product.get_product_price_by_kit(default_kit.code)

    # Если указан kit в URL, используем его
    if request.GET.get('kit'):
        kit_code = request.GET.get('kit')
        try:
            price = product.get_product_price_by_kit(kit_code)
            context['selected_kit'] = kit_code
            context['updated_price'] = price
        except Exception as e:
            print(f"Ошибка расчета цены: {e}")
            messages.warning(request, "Ошибка расчета цены для выбранной комплектации")

    return render(request, 'product/product.html', context=context)


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