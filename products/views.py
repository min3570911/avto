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
    # Берем все комплектации из справочника, не привязываясь к продукту
    sorted_kit_variants = KitVariant.objects.all().order_by('order')
    related_products = list(product.category.products.filter(parent=None).exclude(uid=product.uid))

    # Получаем все доступные цвета для выбора
    colors = Color.objects.all().order_by('display_order')

    # Review product view
    review = None
    if request.user.is_authenticated:
        try:
            review = ProductReview.objects.filter(product=product, user=request.user).first()
        except Exception as e:
            print("No reviews found for this product", str(e))
            messages.warning(request, "No reviews found for this product")

    rating_percentage = 0
    if product.reviews.exists():
        rating_percentage = (product.get_rating() / 5) * 100

    if request.method == 'POST' and request.user.is_authenticated:
        if review:
            # If review exists, update it
            review_form = ReviewForm(request.POST, instance=review)
        else:
            # Otherwise, create a new review
            review_form = ReviewForm(request.POST)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Review added successfully!")
            return redirect('get_product', slug=slug)
    else:
        review_form = ReviewForm()

    # Related product view
    if len(related_products) >= 4:
        related_products = random.sample(related_products, 4)

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    context = {
        'product': product,
        'sorted_kit_variants': sorted_kit_variants,
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
        return JsonResponse({"detail": "Review not found"}, status=404)

    if request.method == "POST":
        stars = request.POST.get("stars")
        content = request.POST.get("content")
        review.stars = stars
        review.content = content
        review.save()
        messages.success(request, "Your review has been updated successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return JsonResponse({"detail": "Invalid request"}, status=400)


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
        messages.warning(request, "You need to be logged in to delete a review.")
        return redirect('login')

    review = ProductReview.objects.filter(uid=review_uid, product__slug=slug, user=request.user).first()

    if not review:
        messages.error(request, "Review not found.")
        return redirect('get_product', slug=slug)

    review.delete()
    messages.success(request, "Your review has been deleted.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Add a product to Wishlist
@login_required
def add_to_wishlist(request, uid):
    kit_code = request.GET.get('kit')
    if not kit_code:
        messages.warning(request, 'Пожалуйста, выберите комплектацию перед добавлением в избранное!')
        return redirect(request.META.get('HTTP_REFERER'))

    product = get_object_or_404(Product, uid=uid)
    kit_variant = get_object_or_404(KitVariant, code=kit_code)
    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user, product=product, kit_variant=kit_variant)

    if created:
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
    wishlist.delete()

    cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, kit_variant=kit_variant)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Товар перемещен в корзину!")
    return redirect('cart')