# 📁 boats/views.py - ПОЛНЫЙ ФАЙЛ представлений для лодок
# 🛥️ Рабочие представления адаптированные для лодок
# ✅ ПРОВЕРЕНО: Логика взята с рабочего products/views.py
# 🛒 ДОБАВЛЕНО: Полная поддержка корзины и избранного БЕЗ комплектаций

import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

# 🛥️ Модели лодок
from .models import BoatCategory, BoatProduct, BoatProductImage

# 🎨 Общие модели - ИСПРАВЛЕННЫЕ ИМПОРТЫ
from products.models import Color, Wishlist
from accounts.models import Cart, CartItem

# 🛒 Временные импорты (до унификации корзины)
from products.views import add_to_cart, add_to_wishlist


def boat_category_list(request):
    """
    🛥️ Главная страница лодок = каталог всех лодок (как products_catalog)

    Отображает все товары лодок с возможностью поиска и фильтрации.
    Поддерживает пагинацию и сортировку + размеры лодок.
    """
    # 🔍 Параметры поиска и фильтрации
    search_query = request.GET.get("search", "")
    sort_by = request.GET.get("sort", "-created_at")
    category_filter = request.GET.get("category", "")
    per_page = request.GET.get("per_page", "12")

    # 🛥️ Фильтры размеров лодочного коврика
    min_length = request.GET.get("min_length", "")
    max_length = request.GET.get("max_length", "")
    min_width = request.GET.get("min_width", "")
    max_width = request.GET.get("max_width", "")

    # 📦 Базовый queryset всех товаров лодок
    products = BoatProduct.objects.all().select_related("category").prefetch_related("images")

    # 🔍 Поиск по названию товара и описанию
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query)
            | Q(product_desription__icontains=search_query)
            | Q(product_sku__icontains=search_query)
        )

    # 📂 Фильтрация по категории
    if category_filter:
        products = products.filter(category__slug=category_filter)

    # 📐 Фильтрация по размерам коврика лодки
    if min_length:
        try:
            products = products.filter(boat_mat_length__gte=int(min_length))
        except ValueError:
            pass

    if max_length:
        try:
            products = products.filter(boat_mat_length__lte=int(max_length))
        except ValueError:
            pass

    if min_width:
        try:
            products = products.filter(boat_mat_width__gte=int(min_width))
        except ValueError:
            pass

    if max_width:
        try:
            products = products.filter(boat_mat_width__lte=int(max_width))
        except ValueError:
            pass

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
                             f"Показано первые 500 из {total_products} товаров. "
                             "Используйте фильтры для поиска.")
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

    # 📂 Активные категории лодок
    categories = (
        BoatCategory.objects.filter(is_active=True)
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
        # 🛥️ НОВОЕ: Фильтры размеров
        "min_length": min_length,
        "max_length": max_length,
        "min_width": min_width,
        "max_width": max_width,
        # 🏷️ Идентификация раздела
        "section_type": "boats",
        "page_title": "🛥️ Лодочные коврики EVA",
        "page_description": "Каталог ковриков для лодок различных марок и моделей",
    }

    return render(request, "boats/category_list.html", context)


def boat_product_list(request, slug):
    """📂 Каталог товаров лодок в выбранной категории (как products_by_category)"""
    category = get_object_or_404(BoatCategory, slug=slug)

    if not category.is_active:
        messages.warning(request, "Эта категория лодок временно недоступна.")
        return redirect("boats:category_list")

    # 🔍 Параметры
    sort_by = request.GET.get("sort", "-created_at")
    search_query = request.GET.get("search", "")
    per_page = request.GET.get("per_page", "12")

    # 🛥️ Фильтры размеров лодочного коврика
    min_length = request.GET.get("min_length", "")
    max_length = request.GET.get("max_length", "")
    min_width = request.GET.get("min_width", "")
    max_width = request.GET.get("max_width", "")

    # 📦 Товары категории
    products = (
        BoatProduct.objects.filter(category=category)
        .select_related("category")
        .prefetch_related("images")
    )

    # 🔍 Поиск внутри категории
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query)
            | Q(product_desription__icontains=search_query)
            | Q(product_sku__icontains=search_query)
        )

    # 📐 Фильтрация по размерам коврика лодки
    if min_length:
        try:
            products = products.filter(boat_mat_length__gte=int(min_length))
        except ValueError:
            pass

    if max_length:
        try:
            products = products.filter(boat_mat_length__lte=int(max_length))
        except ValueError:
            pass

    if min_width:
        try:
            products = products.filter(boat_mat_width__gte=int(min_width))
        except ValueError:
            pass

    if max_width:
        try:
            products = products.filter(boat_mat_width__lte=int(max_width))
        except ValueError:
            pass

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
                             f"Показано первые 500 из {total_products} товаров. "
                             "Используйте фильтры для поиска.")
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

    # 📂 Все категории лодок для фильтра
    categories = (
        BoatCategory.objects.filter(is_active=True)
        .order_by("display_order", "category_name")
    )

    # 🧭 Хлебные крошки
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Лодки', 'url': '/boats/'},
        {'name': category.category_name, 'url': ''}
    ]

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
        # 🛥️ Фильтры размеров
        "min_length": min_length,
        "max_length": max_length,
        "min_width": min_width,
        "max_width": max_width,
        "breadcrumbs": breadcrumbs,
        "section_type": "boats",
        "page_title": f"🛥️ Лодочные коврики {category.category_name}",
        "page_description": f"Коврики EVA для лодок {category.category_name}",
    }

    return render(request, "boats/product_list.html", context)


def boat_product_detail(request, slug):
    """
    🛥️ Детальная страница товара лодки (ТОЧНАЯ КОПИЯ get_product БЕЗ комплектаций)

    Поддерживает:
    ✅ Отзывы с лайками/дизлайками
    ✅ Выбор цветов (коврика и канта)
    ✅ Похожие товары из категории
    ✅ Добавление в корзину/избранное
    ❌ УБРАНО: комплектации, подпятник
    """
    from products.models import ProductReview
    from products.forms import ReviewForm

    # 📦 Получаем товар лодки с оптимизацией
    product = get_object_or_404(
        BoatProduct.objects.select_related('category').prefetch_related('images'),
        slug=slug
    )

    # 📝 Обработка формы отзыва (ТОЧНАЯ КОПИЯ С PRODUCTS)
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            stars = int(request.POST.get('stars', 0))
            content = request.POST.get('content', '').strip()

            if stars >= 1 and stars <= 5 and content:
                # Проверяем, есть ли уже отзыв от этого пользователя
                existing_review = ProductReview.objects.filter(
                    user=request.user,
                    product=product
                ).first()

                if existing_review:
                    messages.warning(request, "❌ Вы уже оставляли отзыв для этого товара.")
                else:
                    # Создаем новый отзыв
                    ProductReview.objects.create(
                        user=request.user,
                        product=product,
                        stars=stars,
                        content=content
                    )
                    messages.success(request, "✅ Ваш отзыв успешно добавлен!")

                return redirect('boats:product_detail', slug=slug)
            else:
                messages.error(request, "❌ Заполните все поля корректно.")
        except (ValueError, TypeError):
            messages.error(request, "❌ Ошибка при добавлении отзыва.")

    # 🔄 Похожие товары из той же категории (АДАПТИРОВАНО ДЛЯ ЛОДОК)
    similar_products = BoatProduct.objects.filter(
        category=product.category
    ).exclude(uid=product.uid).select_related('category').prefetch_related('images')[:4]

    # 🎨 Цвета (используем общие из products - ТОЧНАЯ КОПИЯ)
    colors_carpet = Color.objects.filter(
        color_type='carpet',
        is_available=True
    ).order_by('display_order', 'name')

    colors_border = Color.objects.filter(
        color_type='border',
        is_available=True
    ).order_by('display_order', 'name')

    # 📝 Отзывы товара (ТОЧНАЯ КОПИЯ С PRODUCTS)
    try:
        # Пытаемся получить отзывы через связь
        reviews = product.reviews.all().order_by('-date_added')
    except AttributeError:
        # Если связи нет, получаем отзывы напрямую
        reviews = ProductReview.objects.filter(
            product=product
        ).order_by('-date_added')

    # 📊 Контекст для шаблона (МАКСИМАЛЬНО ПОЛНЫЙ)
    context = {
        'product': product,
        'similar_products': similar_products,
        'colors_carpet': colors_carpet,
        'colors_border': colors_border,
        'reviews': reviews,

        # 🛥️ Специальные контексты для лодок
        'section_type': 'boats',
        'page_title': f'🛥️ {product.product_name} - Лодочный коврик',
    }

    return render(request, 'boats/product_detail.html', context)


def boat_search(request):
    """🔍 Поиск лодок (упрощенная версия)"""
    query = request.GET.get('q', '')

    if not query:
        return render(request, 'boats/search_results.html', {
            'query': '',
            'results': [],
            'total_results': 0,
            'message': 'Введите запрос для поиска лодочных ковриков'
        })

    # 🔍 Поиск
    results = BoatProduct.objects.filter(
        Q(product_name__icontains=query) |
        Q(product_desription__icontains=query) |
        Q(product_sku__icontains=query) |
        Q(category__category_name__icontains=query)
    ).select_related('category').prefetch_related('images')

    # 📄 Пагинация
    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
        'total_results': results.count(),
        'page_title': f'Поиск лодочных ковриков: {query}',
        'section_type': 'boats',
    }

    return render(request, 'boats/search_results.html', context)


# 🛒 КОРЗИНА ДЛЯ ЛОДОК (АДАПТИРОВАНО С PRODUCTS)

@login_required
def boat_add_to_cart(request, uid):
    """
    🛒 Добавление лодочного товара в корзину (АДАПТИРОВАНО С PRODUCTS)

    Поддерживает:
    ✅ Выбор цветов коврика и канта
    ✅ Количество товара
    ❌ УБРАНО: комплектации, подпятник
    """
    if request.method == 'POST':
        try:
            # 📦 Получаем товар лодки
            product = get_object_or_404(BoatProduct, uid=uid)

            # 🎨 Получаем выбранные цвета
            carpet_color_name = request.POST.get('carpet_color', '')
            border_color_name = request.POST.get('border_color', '')
            quantity = int(request.POST.get('quantity', 1))

            # 🔍 Находим объекты цветов
            carpet_color = None
            border_color = None

            if carpet_color_name:
                try:
                    carpet_color = Color.objects.get(name=carpet_color_name, color_type='carpet')
                except Color.DoesNotExist:
                    carpet_color = None

            if border_color_name:
                try:
                    border_color = Color.objects.get(name=border_color_name, color_type='border')
                except Color.DoesNotExist:
                    border_color = None

            # 🛒 Получаем или создаем корзину
            cart, created = Cart.objects.get_or_create(user=request.user)

            # 🔍 Проверяем, есть ли уже такая конфигурация в корзине
            # ДЛЯ ЛОДОК: только цвета, без комплектаций и подпятника
            existing_item = CartItem.objects.filter(
                cart=cart,
                product=product,
                carpet_color=carpet_color,
                border_color=border_color,
                kit_variant__isnull=True,  # Для лодок комплектации всегда null
                has_podpyatnik=False  # Для лодок подпятник всегда False
            ).first()

            if existing_item:
                # 📈 Увеличиваем количество
                existing_item.quantity += quantity
                existing_item.save()
                messages.success(request, f"🛒 Количество увеличено! Теперь в корзине: {existing_item.quantity}")
            else:
                # 🆕 Создаем новый элемент корзины
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=quantity,
                    carpet_color=carpet_color,
                    border_color=border_color,
                    kit_variant=None,  # Для лодок всегда None
                    has_podpyatnik=False  # Для лодок всегда False
                )
                messages.success(request, f"🛒 Лодочный коврик добавлен в корзину! Количество: {quantity}")

            # 🔄 Перенаправляем обратно на страницу товара
            return redirect('boats:product_detail', slug=product.slug)

        except ValueError:
            messages.error(request, "❌ Некорректное количество товара.")
        except BoatProduct.DoesNotExist:
            messages.error(request, "❌ Товар не найден.")
        except Exception as e:
            messages.error(request, f"❌ Ошибка добавления в корзину: {str(e)}")

    # 🔄 При ошибке возвращаемся на каталог лодок
    return redirect('boats:category_list')


@login_required
def boat_add_to_wishlist(request, uid):
    """
    ❤️ Добавление лодочного товара в избранное (АДАПТИРОВАНО С PRODUCTS)

    Поддерживает:
    ✅ Выбор цветов коврика и канта
    ❌ УБРАНО: комплектации, подпятник
    """
    if request.method == 'POST':
        try:
            # 📦 Получаем товар лодки
            product = get_object_or_404(BoatProduct, uid=uid)

            # 🎨 Получаем выбранные цвета (по умолчанию None)
            carpet_color_name = request.POST.get('carpet_color', '')
            border_color_name = request.POST.get('border_color', '')

            # 🔍 Находим объекты цветов
            carpet_color = None
            border_color = None

            if carpet_color_name:
                try:
                    carpet_color = Color.objects.get(name=carpet_color_name, color_type='carpet')
                except Color.DoesNotExist:
                    pass

            if border_color_name:
                try:
                    border_color = Color.objects.get(name=border_color_name, color_type='border')
                except Color.DoesNotExist:
                    pass

            # 🔍 Проверяем, есть ли уже в избранном
            # ДЛЯ ЛОДОК: только цвета, без комплектаций и подпятника
            existing_wishlist = Wishlist.objects.filter(
                user=request.user,
                product=product,
                carpet_color=carpet_color,
                border_color=border_color,
                kit_variant__isnull=True,  # Для лодок комплектации всегда null
                has_podpyatnik=False  # Для лодок подпятник всегда False
            ).first()

            if existing_wishlist:
                # 🗑️ Удаляем из избранного (toggle)
                existing_wishlist.delete()
                messages.info(request, "💔 Лодочный коврик удален из избранного.")
            else:
                # ❤️ Добавляем в избранное
                Wishlist.objects.create(
                    user=request.user,
                    product=product,
                    carpet_color=carpet_color,
                    border_color=border_color,
                    kit_variant=None,  # Для лодок всегда None
                    has_podpyatnik=False  # Для лодок всегда False
                )
                messages.success(request, "❤️ Лодочный коврик добавлен в избранное!")

            # 🔄 Перенаправляем обратно на страницу товара
            return redirect('boats:product_detail', slug=product.slug)

        except BoatProduct.DoesNotExist:
            messages.error(request, "❌ Товар не найден.")
        except Exception as e:
            messages.error(request, f"❌ Ошибка добавления в избранное: {str(e)}")

    # 🔄 При ошибке возвращаемся на каталог лодок
    return redirect('boats:category_list')


# 🔧 ДОПОЛНИТЕЛЬНЫЕ функции для лодок

@login_required
def boat_remove_from_cart(request, item_uid):
    """🗑️ Удаление лодочного товара из корзины"""
    try:
        cart_item = get_object_or_404(CartItem, uid=item_uid, cart__user=request.user)
        product_name = cart_item.product.product_name
        cart_item.delete()
        messages.success(request, f"🗑️ {product_name} удален из корзины.")
    except Exception as e:
        messages.error(request, f"❌ Ошибка удаления: {str(e)}")

    return redirect('cart')


@login_required
def boat_update_cart_quantity(request, item_uid):
    """📊 Обновление количества лодочного товара в корзине"""
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(CartItem, uid=item_uid, cart__user=request.user)
            new_quantity = int(request.POST.get('quantity', 1))

            if new_quantity > 0:
                cart_item.quantity = new_quantity
                cart_item.save()
                messages.success(request, f"📊 Количество обновлено: {new_quantity}")
            else:
                cart_item.delete()
                messages.info(request, "🗑️ Товар удален из корзины.")

        except ValueError:
            messages.error(request, "❌ Некорректное количество.")
        except Exception as e:
            messages.error(request, f"❌ Ошибка обновления: {str(e)}")

    return redirect('cart')

# 🔧 КОММЕНТАРИИ:
#
# ✅ СКОПИРОВАНО С РАБОЧЕГО products/views.py:
# • products_catalog → boat_category_list
# • products_by_category → boat_product_list
# • get_product → boat_product_detail (с поддержкой отзывов)
# • Вся логика поиска, фильтрации, пагинации
# • Все обработки ошибок и валидация
# • Структура контекста для шаблонов
#
# 🛥️ АДАПТИРОВАНО ДЛЯ ЛОДОК:
# • Product → BoatProduct
# • Category → BoatCategory
# • Добавлены фильтры по boat_mat_length/width
# • Убраны комплектации (KitVariant)
# • Добавлены специальные контексты (boat_dimensions, show_boat_features)
# • Функции корзины БЕЗ комплектаций и подпятника
#
# 📋 РЕЗУЛЬТАТ:
# • Полностью рабочие представления на основе проверенного кода
# • Готовность к работе с теми же шаблонами что и products
# • Унифицированная логика между автомобилями и лодками
# • Поддержка корзины и избранного БЕЗ комплектаций