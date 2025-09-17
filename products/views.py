# 📁 products/views.py
# 🔒 ОБНОВЛЕННАЯ версия с полной системой модерации отзывов
# ⭐ ДОБАВЛЕНО: Функции модерации для администраторов + интерактивные звездочки

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
import json

# 🛍️ Модели товаров
from products.models import (
    Product,
    KitVariant,
    Color,
    Category,
)

# 🤝 Импорт универсальных моделей из common
from common.models import ProductReview, Wishlist

# 👤 Модели пользователей и корзины
from accounts.models import Cart, CartItem

# 📝 Формы
from .forms import ReviewForm


def products_catalog(request):
    """🛍️ Главная страница каталога товаров"""
    search_query = request.GET.get("search", "")
    sort_by = request.GET.get("sort", "-created_at")
    category_filter = request.GET.get("category", "")
    per_page = request.GET.get("per_page", "12")

    products = Product.objects.all().select_related("category").prefetch_related("product_images")

    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query)
            | Q(product_desription__icontains=search_query)
        )

    if category_filter:
        products = products.filter(category__slug=category_filter)

    sort_options = {
        "name": "product_name",
        "-name": "-product_name",
        "price": "price",
        "-price": "-price",
        "newest": "-created_at",
        "oldest": "created_at",
    }
    products = products.order_by(sort_options.get(sort_by, "-created_at"))

    if per_page == "all":
        total_products = products.count()
        if total_products > 500:
            messages.warning(request, f"Показано первые 500 из {total_products} товаров.")
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

    # Пагинация
    paginator = Paginator(products, per_page_num)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Активные категории
    categories = (
        Category.objects.filter(is_active=True)
        .order_by("display_order", "category_name")
    )

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

    sort_by = request.GET.get("sort", "-created_at")
    search_query = request.GET.get("search", "")
    per_page = request.GET.get("per_page", "12")

    products = (
        Product.objects.filter(category=category)
        .select_related("category")
        .prefetch_related("product_images")
    )

    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query)
            | Q(product_desription__icontains=search_query)
        )

    sort_options = {
        "name": "product_name",
        "-name": "-product_name",
        "price": "price",
        "-price": "-price",
        "newest": "-created_at",
        "oldest": "created_at",
    }
    products = products.order_by(sort_options.get(sort_by, "-created_at"))

    if per_page == "all":
        total_products = products.count()
        if total_products > 500:
            messages.warning(request, f"Показано первые 500 из {total_products} товаров.")
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

    paginator = Paginator(products, per_page_num)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = (
        Category.objects.filter(is_active=True)
        .order_by("display_order", "category_name")
    )

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
    🛍️ ОБНОВЛЕННАЯ страница товара с полной модерацией отзывов

    ⭐ Поддерживает интерактивные звездочки
    🔒 Полная система модерации отзывов
    👁️ Показ только одобренных отзывов обычным пользователям
    """

    product = get_object_or_404(Product, slug=slug)

    # 🔍 Проверяем тип товара
    if product.is_boat_product():
        # ================== ЛОГИКА ДЛЯ ЛОДОК ==================
        carpet_colors = Color.objects.filter(
            color_type='carpet',
            is_available=True
        ).order_by('display_order')

        border_colors = Color.objects.filter(
            color_type='border',
            is_available=True
        ).order_by('display_order')

        initial_carpet_color = carpet_colors.first()
        initial_border_color = border_colors.first()

        sorted_kit_variants = []
        additional_options = []
        podpyatnik_option = None

        selected_kit = None
        updated_price = product.price or 0

        in_cart = False
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user, is_paid=False).first()
            if cart:
                product_content_type = ContentType.objects.get_for_model(Product)
                in_cart = CartItem.objects.filter(
                    cart=cart,
                    content_type=product_content_type,
                    object_id=product.uid,
                    kit_variant__isnull=True,
                    has_podpyatnik=False
                ).exists()

    else:
        # ================== ЛОГИКА ДЛЯ АВТОМОБИЛЕЙ ==================
        sorted_kit_variants = KitVariant.objects.filter(is_option=False).order_by('order')
        additional_options = KitVariant.objects.filter(is_option=True).order_by('order')

        podpyatnik_option = KitVariant.objects.filter(code='podpyatnik', is_option=True).first()
        if not podpyatnik_option:
            podpyatnik_option = type('obj', (object,), {
                'name': 'Подпятник',
                'price_modifier': 15.00,
                'code': 'podpyatnik'
            })

        carpet_colors = Color.objects.filter(color_type='carpet').order_by('display_order')
        border_colors = Color.objects.filter(color_type='border').order_by('display_order')

        initial_carpet_color = carpet_colors.filter(is_available=True).first() or carpet_colors.first()
        initial_border_color = border_colors.filter(is_available=True).first() or border_colors.first()

        in_cart = False
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user, is_paid=False).first()
            if cart:
                product_content_type = ContentType.objects.get_for_model(Product)
                in_cart = CartItem.objects.filter(
                    cart=cart,
                    content_type=product_content_type,
                    object_id=product.uid
                ).exists()

        selected_kit, updated_price = None, product.price
        default_kit = sorted_kit_variants.filter(code='salon').first()
        kit_code = request.GET.get('kit') or (default_kit.code if default_kit else None)

        if kit_code:
            selected_kit = kit_code
            updated_price = product.get_product_price_by_kit(kit_code)

    # ================== 🔒 ОБНОВЛЕННАЯ ЛОГИКА ОТЗЫВОВ С МОДЕРАЦИЕЙ ==================

    # 👁️ Получаем ТОЛЬКО одобренные отзывы для обычного отображения
    try:
        reviews = product.reviews.filter(is_approved=True).order_by('-date_added')
        has_reviews = product.reviews.filter(is_approved=True).exists()
    except AttributeError:
        product_content_type = ContentType.objects.get_for_model(Product)
        reviews = ProductReview.objects.filter(
            content_type=product_content_type,
            object_id=product.uid,
            is_approved=True
        ).order_by('-date_added')
        has_reviews = reviews.exists()

    # 📝 Получаем отзыв текущего пользователя (может быть на модерации)
    user_existing_review = None
    if request.user.is_authenticated:
        try:
            product_content_type = ContentType.objects.get_for_model(Product)
            user_existing_review = ProductReview.objects.filter(
                content_type=product_content_type,
                object_id=product.uid,
                user=request.user
            ).first()
        except:
            user_existing_review = None

    rating_percentage = (product.get_rating() / 5) * 100 if has_reviews else 0
    review_form = ReviewForm(request.POST or None, instance=user_existing_review)

    # 🔒 ОБРАБОТКА POST-запроса с модерацией
    if request.method == 'POST' and request.user.is_authenticated:
        if review_form.is_valid():
            try:
                if user_existing_review:
                    # ✏️ Обновляем существующий отзыв
                    user_existing_review.stars = review_form.cleaned_data['stars']
                    user_existing_review.content = review_form.cleaned_data['content']
                    user_existing_review.is_approved = False  # Повторная модерация
                    user_existing_review.save()
                    messages.info(request,
                                  "✅ Ваш отзыв обновлен и отправлен на модерацию. "
                                  "После проверки он появится на сайте.")
                else:
                    # ➕ Создаем новый отзыв
                    review = review_form.save(commit=False)
                    review.user = request.user

                    # 🔗 Устанавливаем связь через Generic FK
                    product_content_type = ContentType.objects.get_for_model(Product)
                    review.content_type = product_content_type
                    review.object_id = product.uid

                    # 🔒 Новый отзыв требует модерации
                    review.is_approved = False
                    review.save()

                    messages.success(request,
                                     "✅ Спасибо за отзыв! Он отправлен на модерацию и скоро появится на сайте.")

                return redirect('get_product', slug=slug)

            except Exception as e:
                messages.error(request, f"❌ Ошибка при сохранении отзыва: {str(e)}")
        else:
            messages.error(request, "❌ Пожалуйста, исправьте ошибки в форме.")

    # 🔍 Похожие товары
    similar_products = Product.objects.filter(
        category=product.category
    ).exclude(uid=product.uid).select_related('category').prefetch_related('product_images')[:4]

    # ❤️ Проверяем наличие в избранном
    in_wishlist = False
    if request.user.is_authenticated:
        try:
            product_content_type = ContentType.objects.get_for_model(Product)
            in_wishlist = Wishlist.objects.filter(
                user=request.user,
                content_type=product_content_type,
                object_id=product.uid
            ).exists()
        except:
            in_wishlist = False

    # 📋 Контекст для шаблона
    context = {
        'product': product,
        'reviews': reviews,
        'similar_products': similar_products,

        # 🔍 Типы товаров
        'is_boat_product': product.is_boat_product(),
        'is_car_product': product.is_car_product(),

        # 🛠️ Комплектации
        'sorted_kit_variants': sorted_kit_variants,
        'additional_options': additional_options,
        'podpyatnik_option': podpyatnik_option,

        # 🎨 Цвета
        'carpet_colors': carpet_colors,
        'border_colors': border_colors,
        'initial_carpet_color': initial_carpet_color,
        'initial_border_color': initial_border_color,

        # 💰 Цены
        'selected_kit': selected_kit,
        'updated_price': updated_price,

        # 🛒 Состояния
        'in_cart': in_cart,
        'in_wishlist': in_wishlist,

        # 📝 Отзывы и формы
        'review_form': review_form,
        'rating_percentage': rating_percentage,
        'user_existing_review': user_existing_review,
        'user_review_pending': user_existing_review and not user_existing_review.is_approved if user_existing_review else False,
    }

    return render(request, 'product/product.html', context)


def add_to_cart(request, uid):
    """🛒 Добавление товара в корзину с Generic FK"""
    try:
        kit_code = request.POST.get('kit')
        carpet_color_id = request.POST.get('carpet_color')
        border_color_id = request.POST.get('border_color')
        has_podp = request.POST.get('podp') == '1'
        quantity = int(request.POST.get('quantity') or 1)

        product = get_object_or_404(Product, uid=uid)

        if product.is_boat_product():
            kit_variant = None
            has_podp = False
        else:
            if not kit_code:
                messages.warning(request, 'Пожалуйста, выберите комплектацию!')
                return redirect(request.META.get('HTTP_REFERER'))
            kit_variant = get_object_or_404(KitVariant, code=kit_code)

        carpet_color = None
        if carpet_color_id:
            carpet_color = get_object_or_404(Color, uid=carpet_color_id)
            if not carpet_color.is_available:
                messages.warning(request, f'Цвет коврика "{carpet_color.name}" временно недоступен.')
                return redirect(request.META.get('HTTP_REFERER'))

        border_color = None
        if border_color_id:
            border_color = get_object_or_404(Color, uid=border_color_id)
            if not border_color.is_available:
                messages.warning(request, f'Цвет окантовки "{border_color.name}" временно недоступен.')
                return redirect(request.META.get('HTTP_REFERER'))

        # 🛒 Получаем или создаем корзину
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                is_paid=False,
                defaults={'session_id': None}
            )
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            cart, created = Cart.objects.get_or_create(
                session_id=session_key,
                user=None,
                is_paid=False
            )

        product_content_type = ContentType.objects.get_for_model(Product)

        existing_item = CartItem.objects.filter(
            cart=cart,
            content_type=product_content_type,
            object_id=product.uid,
            kit_variant=kit_variant,
            carpet_color=carpet_color,
            border_color=border_color,
            has_podpyatnik=has_podp
        ).first()

        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            messages.success(request, f'Количество товара увеличено! Всего в корзине: {existing_item.quantity}')
        else:
            CartItem.objects.create(
                cart=cart,
                content_type=product_content_type,
                object_id=product.uid,
                kit_variant=kit_variant,
                carpet_color=carpet_color,
                border_color=border_color,
                has_podpyatnik=has_podp,
                quantity=quantity
            )
            messages.success(request, '✅ Товар добавлен в корзину!')

    except Exception as e:
        messages.error(request, f'❌ Ошибка при добавлении в корзину: {str(e)}')

    return redirect('cart')


@login_required
def product_reviews(request):
    """📝 Отображение всех отзывов пользователя (включая на модерации)"""
    reviews = ProductReview.objects.filter(
        user=request.user
    ).order_by('-date_added')

    for review in reviews:
        try:
            if review.content_type.model == 'product':
                product = Product.objects.get(uid=review.object_id)
            elif review.content_type.model == 'boatproduct':
                from boats.models import BoatProduct
                product = BoatProduct.objects.get(uid=review.object_id)
            else:
                product = None
            review._cached_product = product
        except:
            review._cached_product = None

    return render(request, 'product/all_product_reviews.html', {'reviews': reviews})


def delete_review(request, slug, review_uid):
    """🗑️ Удаление отзыва"""
    if not request.user.is_authenticated:
        messages.warning(request, "Необходимо войти в систему, чтобы удалить отзыв.")
        return redirect('login')

    review = ProductReview.objects.filter(
        uid=review_uid,
        user=request.user
    ).first()

    if not review:
        messages.error(request, "Отзыв не найден.")
        return redirect('get_product', slug=slug)

    try:
        if review.content_type.model == 'product':
            product = Product.objects.get(uid=review.object_id)
            if hasattr(product, 'slug') and product.slug != slug:
                messages.error(request, "Отзыв не принадлежит этому товару.")
                return redirect('get_product', slug=slug)
    except:
        pass

    review.delete()
    messages.success(request, "✅ Ваш отзыв был удален.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', f'/products/{slug}/'))


@login_required
def edit_review(request, review_uid):
    """✏️ Редактирование отзыва пользователя"""
    review = ProductReview.objects.filter(uid=review_uid, user=request.user).first()

    if not review:
        return JsonResponse({"detail": "Отзыв не найден"}, status=404)

    if request.method == "POST":
        try:
            stars = request.POST.get("stars")
            content = request.POST.get("content")

            if stars and content:
                review.stars = int(stars)
                review.content = content
                review.is_approved = False  # Повторная модерация
                review.save()
                messages.success(request, "✅ Ваш отзыв обновлен и отправлен на модерацию.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                return JsonResponse({"detail": "Заполните все поля"}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({"detail": "Некорректные данные"}, status=400)

    return JsonResponse({"detail": "Некорректный запрос"}, status=400)


def like_review(request, review_uid):
    """👍 Обработка лайка отзыва"""
    review = ProductReview.objects.filter(uid=review_uid).first()

    if not review:
        return JsonResponse({'error': 'Отзыв не найден'}, status=404)

    if request.user in review.likes.all():
        review.likes.remove(request.user)
    else:
        review.likes.add(request.user)
        review.dislikes.remove(request.user)

    return JsonResponse({
        'likes': review.like_count(),
        'dislikes': review.dislike_count()
    })


def dislike_review(request, review_uid):
    """👎 Обработка дизлайка отзыва"""
    review = ProductReview.objects.filter(uid=review_uid).first()

    if not review:
        return JsonResponse({'error': 'Отзыв не найден'}, status=404)

    if request.user in review.dislikes.all():
        review.dislikes.remove(request.user)
    else:
        review.dislikes.add(request.user)
        review.likes.remove(request.user)

    return JsonResponse({
        'likes': review.like_count(),
        'dislikes': review.dislike_count()
    })


@login_required
def add_to_wishlist(request, uid):
    """❤️ Добавление товара в избранное"""
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

    if product.is_boat_product():
        kit_variant = None
        has_podp = False
    else:
        kit_variant = get_object_or_404(KitVariant, code=kit_code)

    carpet_color = None
    border_color = None
    if carpet_color_id:
        carpet_color = get_object_or_404(Color, uid=carpet_color_id)
    if border_color_id:
        border_color = get_object_or_404(Color, uid=border_color_id)

    if carpet_color and not carpet_color.is_available:
        messages.warning(request, f'Цвет коврика "{carpet_color.name}" временно недоступен.')
        return redirect(request.META.get('HTTP_REFERER'))

    if border_color and not border_color.is_available:
        messages.warning(request, f'Цвет окантовки "{border_color.name}" временно недоступен.')
        return redirect(request.META.get('HTTP_REFERER'))

    product_content_type = ContentType.objects.get_for_model(Product)
    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        content_type=product_content_type,
        object_id=product.uid,
        kit_variant=kit_variant
    ).first()

    if wishlist_item:
        wishlist_item.carpet_color = carpet_color
        wishlist_item.border_color = border_color
        wishlist_item.has_podpyatnik = has_podp
        wishlist_item.save()
        messages.success(request, "✅ Товар в избранном обновлен!")
    else:
        Wishlist.objects.create(
            user=request.user,
            content_type=product_content_type,
            object_id=product.uid,
            kit_variant=kit_variant,
            carpet_color=carpet_color,
            border_color=border_color,
            has_podpyatnik=has_podp
        )
        messages.success(request, "✅ Товар добавлен в избранное!")

    return redirect(reverse('wishlist'))


@login_required
def remove_from_wishlist(request, uid):
    """🗑️ Удаление товара из избранного"""
    product = get_object_or_404(Product, uid=uid)
    kit_code = request.GET.get('kit')

    product_content_type = ContentType.objects.get_for_model(Product)

    if kit_code:
        kit_variant = get_object_or_404(KitVariant, code=kit_code)
        Wishlist.objects.filter(
            user=request.user,
            content_type=product_content_type,
            object_id=product.uid,
            kit_variant=kit_variant
        ).delete()
    else:
        Wishlist.objects.filter(
            user=request.user,
            content_type=product_content_type,
            object_id=product.uid
        ).delete()

    messages.success(request, "✅ Товар удален из избранного!")
    return redirect(reverse('wishlist'))


@login_required
def wishlist_view(request):
    """❤️ Отображение списка избранных товаров"""
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'product/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def move_to_cart(request, uid):
    """🔄 Перемещение товара из избранного в корзину"""
    product = get_object_or_404(Product, uid=uid)
    product_content_type = ContentType.objects.get_for_model(Product)

    wishlist = Wishlist.objects.filter(
        user=request.user,
        content_type=product_content_type,
        object_id=product.uid
    ).first()

    if not wishlist:
        messages.error(request, "❌ Товар не найден в избранном.")
        return redirect('wishlist')

    kit_variant = wishlist.kit_variant
    carpet_color = wishlist.carpet_color
    border_color = wishlist.border_color
    has_podpyatnik = wishlist.has_podpyatnik

    if carpet_color and not carpet_color.is_available:
        messages.warning(request, f'Цвет коврика "{carpet_color.name}" временно недоступен.')
        return redirect('wishlist')

    if border_color and not border_color.is_available:
        messages.warning(request, f'Цвет окантовки "{border_color.name}" временно недоступен.')
        return redirect('wishlist')

    wishlist.delete()

    cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)

    cart_item = CartItem.objects.filter(
        cart=cart,
        content_type=product_content_type,
        object_id=product.uid,
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
            content_type=product_content_type,
            object_id=product.uid,
            kit_variant=kit_variant,
            carpet_color=carpet_color,
            border_color=border_color,
            has_podpyatnik=has_podpyatnik
        )

    messages.success(request, "✅ Товар перемещен в корзину!")
    return redirect('cart')


# ==================== 🔒 НОВЫЕ ФУНКЦИИ МОДЕРАЦИИ ДЛЯ АДМИНИСТРАТОРОВ ====================

@staff_member_required
@require_POST
def moderate_review(request, review_uid, action):
    """
    👨‍💼 Модерация отзывов администраторами

    Позволяет администраторам одобрять или отклонять отзывы
    через AJAX-запросы с страницы товара
    """
    try:
        review = ProductReview.objects.filter(uid=review_uid).first()

        if not review:
            return JsonResponse({
                'success': False,
                'error': 'Отзыв не найден'
            }, status=404)

        if action == 'approve':
            review.is_approved = True
            review.save()

            return JsonResponse({
                'success': True,
                'message': f'Отзыв от {review.user.get_full_name()} одобрен',
                'new_status': 'approved'
            })

        elif action == 'reject':
            # 🗑️ Отклоняем отзыв (удаляем)
            user_name = review.user.get_full_name()
            review.delete()

            return JsonResponse({
                'success': True,
                'message': f'Отзыв от {user_name} отклонен и удален',
                'new_status': 'rejected'
            })

        else:
            return JsonResponse({
                'success': False,
                'error': f'Неизвестное действие: {action}'
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при модерации: {str(e)}'
        }, status=500)


@staff_member_required
def pending_reviews(request):
    """
    👨‍💼 Страница с отзывами, ожидающими модерации

    Административная страница для просмотра и модерации
    всех отзывов, ожидающих одобрения
    """
    # 📋 Получаем все неодобренные отзывы
    pending_reviews = ProductReview.objects.filter(
        is_approved=False
    ).order_by('-date_added').select_related('user', 'content_type')

    # 🔍 Добавляем информацию о товарах к отзывам
    for review in pending_reviews:
        try:
            if review.content_type.model == 'product':
                product = Product.objects.get(uid=review.object_id)
            elif review.content_type.model == 'boatproduct':
                from boats.models import BoatProduct
                product = BoatProduct.objects.get(uid=review.object_id)
            else:
                product = None
            review._cached_product = product
        except:
            review._cached_product = None

    # 📊 Статистика
    stats = {
        'total_pending': pending_reviews.count(),
        'today_pending': pending_reviews.filter(
            date_added__date=timezone.now().date()
        ).count() if 'timezone' in globals() else 0,
        'total_approved': ProductReview.objects.filter(is_approved=True).count(),
    }

    context = {
        'pending_reviews': pending_reviews,
        'stats': stats,
    }

    return render(request, 'admin/moderate_reviews.html', context)


@staff_member_required
@require_POST
def bulk_moderate_reviews(request):
    """
    👨‍💼 Массовая модерация отзывов

    Позволяет администраторам одобрить или отклонить
    несколько отзывов одновременно
    """
    try:
        data = json.loads(request.body)
        review_uids = data.get('review_uids', [])
        action = data.get('action')  # 'approve' or 'reject'

        if not review_uids or not action:
            return JsonResponse({
                'success': False,
                'error': 'Не указаны отзывы или действие'
            }, status=400)

        reviews = ProductReview.objects.filter(uid__in=review_uids)

        if not reviews.exists():
            return JsonResponse({
                'success': False,
                'error': 'Отзывы не найдены'
            }, status=404)

        processed_count = 0

        if action == 'approve':
            # ✅ Одобряем отзывы
            updated = reviews.update(is_approved=True)
            processed_count = updated
            message = f'Одобрено отзывов: {processed_count}'

        elif action == 'reject':
            # 🗑️ Удаляем отклоненные отзывы
            processed_count = reviews.count()
            reviews.delete()
            message = f'Отклонено отзывов: {processed_count}'

        else:
            return JsonResponse({
                'success': False,
                'error': f'Неизвестное действие: {action}'
            }, status=400)

        return JsonResponse({
            'success': True,
            'message': message,
            'processed_count': processed_count
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Некорректные JSON данные'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при обработке: {str(e)}'
        }, status=500)


# 🔧 ДОПОЛНИТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ УЛУЧШЕННОЙ НАВИГАЦИИ
def toggle_like(request, review_uid):
    """👍 Универсальная функция для лайков (AJAX)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Необходима авторизация'}, status=401)

    review = get_object_or_404(ProductReview, uid=review_uid)

    if request.user in review.likes.all():
        review.likes.remove(request.user)
        action = 'removed'
    else:
        review.likes.add(request.user)
        review.dislikes.remove(request.user)  # Убираем дизлайк если был
        action = 'added'

    return JsonResponse({
        'success': True,
        'action': action,
        'likes': review.like_count(),
        'dislikes': review.dislike_count()
    })


def toggle_dislike(request, review_uid):
    """👎 Универсальная функция для дизлайков (AJAX)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Необходима авторизация'}, status=401)

    review = get_object_or_404(ProductReview, uid=review_uid)

    if request.user in review.dislikes.all():
        review.dislikes.remove(request.user)
        action = 'removed'
    else:
        review.dislikes.add(request.user)
        review.likes.remove(request.user)  # Убираем лайк если был
        action = 'added'

    return JsonResponse({
        'success': True,
        'action': action,
        'likes': review.like_count(),
        'dislikes': review.dislike_count()
    })

# 🔧 ОСНОВНЫЕ ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ⭐ ДОБАВЛЕНО: Полная поддержка интерактивных звездочек в формах
# 🔒 ДОБАВЛЕНО: Система модерации с функциями для администраторов
# 👨‍💼 ДОБАВЛЕНО: moderate_review, pending_reviews, bulk_moderate_reviews
# 🎯 УЛУЧШЕНО: Обработка отзывов с автоматической отправкой на модерацию
# 📝 СОХРАНЕНО: Вся существующая логика товаров, корзины, избранного
# 🔗 ИСПРАВЛЕНО: Правильная работа с Generic FK для отзывов
#
# 🎯 РЕЗУЛЬТАТ:
# - Полная система модерации отзывов
# - Интерактивные звездочки готовы к использованию
# - Функции для администраторов через AJAX
# - Массовая модерация отзывов
# - Совместимость с существующим кодом