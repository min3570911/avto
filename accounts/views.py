import os
import json
import uuid
import requests
import logging
from products.models import *
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from home.models import ShippingAddress
from django.contrib.auth.models import User
from django.template.loader import get_template, render_to_string
from accounts.models import Profile, Cart, CartItem, Order, OrderItem
from base.emails import send_account_activation_email
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect, render, get_object_or_404
from accounts.forms import UserUpdateForm, UserProfileForm, ShippingAddressForm, CustomPasswordChangeForm
from django.core.mail import send_mail
from django.utils.html import strip_tags

# Импорт для генерации PDF
try:
    from xhtml2pdf import pisa

    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

# Настройка логгера
logger = logging.getLogger(__name__)


# Создаем views

def login_page(request):
    next_url = request.GET.get('next')  # Get the next URL from the query parameter
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_obj = User.objects.filter(username=username)

        if not user_obj.exists():
            messages.warning(request, 'Аккаунт не найден!')
            return HttpResponseRedirect(request.path_info)

        if not user_obj[0].profile.is_email_verified:
            messages.error(request, 'Аккаунт не верифицирован!')
            return HttpResponseRedirect(request.path_info)

        user_obj = authenticate(username=username, password=password)
        if user_obj:
            login(request, user_obj)
            messages.success(request, 'Успешный вход.')

            # Check if the next URL is safe
            if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host()):
                return redirect(next_url)
            else:
                return redirect('index')

        messages.warning(request, 'Неверные учетные данные.')
        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/login.html')


def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username=username, email=email)

        if user_obj.exists():
            messages.info(request, 'Имя пользователя или email уже существуют!')
            return HttpResponseRedirect(request.path_info)

        user_obj = User.objects.create(
            username=username, first_name=first_name, last_name=last_name, email=email)
        user_obj.set_password(password)
        user_obj.save()

        profile = Profile.objects.get(user=user_obj)
        profile.email_token = str(uuid.uuid4())
        profile.save()

        send_account_activation_email(email, profile.email_token)
        messages.success(request, "На ваш email отправлено письмо для подтверждения.")
        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/register.html')


@login_required
def user_logout(request):
    logout(request)
    messages.warning(request, "Выход выполнен успешно!")
    return redirect('index')


def activate_email_account(request, email_token):
    try:
        user = Profile.objects.get(email_token=email_token)
        user.is_email_verified = True
        user.save()
        messages.success(request, 'Аккаунт успешно верифицирован.')
        return redirect('login')
    except Exception as e:
        return HttpResponse('Неверный токен email.')


def cart(request):
    """Отображение корзины с формой оформления заказа"""
    cart_obj = None

    try:
        # Получаем корзину для текущего пользователя/сессии
        cart_obj = Cart.get_cart(request)

    except Exception as e:
        messages.warning(request, "Ваша корзина пуста. Пожалуйста, добавьте товар в корзину.")
        return redirect(reverse('index'))

    if request.method == 'POST':
        coupon = request.POST.get('coupon')
        coupon_obj = Coupon.objects.filter(coupon_code__exact=coupon).first()

        if not coupon_obj:
            messages.warning(request, 'Неверный код купона.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if cart_obj and cart_obj.coupon:
            messages.warning(request, 'Купон уже применен.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if coupon_obj and coupon_obj.is_expired:
            messages.warning(request, 'Срок действия купона истек.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if cart_obj and coupon_obj and cart_obj.get_cart_total() < coupon_obj.minimum_amount:
            messages.warning(
                request, f'Сумма должна быть больше {coupon_obj.minimum_amount}')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if cart_obj and coupon_obj:
            cart_obj.coupon = coupon_obj
            cart_obj.save()
            messages.success(request, 'Купон успешно применен.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # Предзаполняем данные, если пользователь авторизован
    initial_data = {}
    if request.user.is_authenticated:
        initial_data = {
            'customer_name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'customer_email': request.user.email
        }

    context = {
        'cart': cart_obj,
        'quantity_range': range(1, 11),  # Для выбора количества товаров
        'initial_data': initial_data
    }
    return render(request, 'accounts/cart.html', context)


@require_POST
def update_cart_item(request):
    try:
        data = json.loads(request.body)
        cart_item_id = data.get("cart_item_id")
        quantity = int(data.get("quantity"))

        # Получаем корзину пользователя/сессии
        cart = Cart.get_cart(request)

        # Находим элемент корзины
        cart_item = CartItem.objects.get(uid=cart_item_id, cart=cart, cart__is_paid=False)
        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def remove_cart(request, uid):
    try:
        # Получаем корзину пользователя/сессии
        cart = Cart.get_cart(request)

        # Находим и удаляем элемент корзины
        cart_item = CartItem.objects.get(uid=uid, cart=cart)
        cart_item.delete()

        messages.success(request, 'Товар удален из корзины.')

    except Exception as e:
        print(e)
        messages.warning(request, 'Ошибка при удалении товара из корзины.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def remove_coupon(request, cart_id):
    # Проверяем, что корзина принадлежит текущему пользователю/сессии
    cart = Cart.get_cart(request)

    if str(cart.uid) != cart_id:
        messages.warning(request, 'Ошибка доступа к корзине.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    cart.coupon = None
    cart.save()

    messages.success(request, 'Купон удален.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def send_telegram_notification(order):
    """
    🤖 Отправляет уведомление о новом заказе в Telegram
    """
    try:
        # Конфигурация Telegram бота
        telegram_token = settings.TELEGRAM_BOT_TOKEN
        telegram_chat_id = settings.TELEGRAM_CHAT_ID

        # URL для отправки сообщения
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

        # Формируем текст сообщения
        items_text = ""
        for item in OrderItem.objects.filter(order=order):
            variant_info = f", {item.kit_variant.name}" if item.kit_variant else ""
            items_text += f"• {item.product.product_name}{variant_info} x {item.quantity} = {item.product_price} BYN\n"

        message = f"""
🛍️ *НОВЫЙ ЗАКАЗ #{order.order_id}*

👤 *Клиент:* {order.customer_name}
📱 *Телефон:* {order.customer_phone}
📧 *Email:* {order.customer_email}

🚚 *Способ доставки:* {order.get_delivery_method_display()}
📍 *Адрес:* {order.shipping_address}

📝 *Товары:*
{items_text}

💰 *Итого:* {order.grand_total} BYN

🗒️ *Примечание:* {order.order_notes or "Нет"}
        """

        # Параметры запроса
        params = {
            "chat_id": telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        # Отправляем запрос
        response = requests.post(url, params=params)

        # Проверяем результат
        if response.status_code != 200 or not response.json().get("ok"):
            logger.error(f"Ошибка при отправке уведомления в Telegram: {response.text}")

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в Telegram: {str(e)}")


def send_order_notification(order):
    """Отправляет уведомления о заказе на email и в Telegram"""
    try:
        # Подготовка данных для уведомления
        order_items = OrderItem.objects.filter(order=order)

        # Email уведомление клиенту
        subject = f'Ваш заказ #{order.order_id} успешно оформлен'
        message = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'order_items': order_items,
        })
        send_mail(
            subject,
            strip_tags(message),
            settings.DEFAULT_FROM_EMAIL,
            [order.customer_email],
            html_message=message,
            fail_silently=False,
        )

        # Отправка уведомления в Telegram
        send_telegram_notification(order)

    except Exception as e:
        # Логируем ошибку, но не прерываем процесс
        logger.error(f"Ошибка при отправке уведомления о заказе #{order.order_id}: {str(e)}")


def place_order(request):
    """Обработка оформления заказа без регистрации"""
    if request.method != 'POST':
        return redirect('cart')

    # Получаем корзину пользователя или сессии
    cart = Cart.get_cart(request)

    # Проверяем, есть ли товары в корзине
    if not cart.cart_items.exists():
        messages.warning(request, "Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
        return redirect('index')

    # Получаем данные формы
    customer_name = request.POST.get('customer_name')
    customer_phone = request.POST.get('customer_phone')
    customer_email = request.POST.get('customer_email')
    delivery_method = request.POST.get('delivery_method')
    shipping_address = request.POST.get('shipping_address')
    order_notes = request.POST.get('order_notes', '')

    # Проверяем обязательные поля
    if not all([customer_name, customer_phone, customer_email, delivery_method, shipping_address]):
        messages.error(request, "Пожалуйста, заполните все обязательные поля.")
        return redirect('cart')

    # Создаем уникальный ID заказа
    order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"

    # Создаем заказ
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        delivery_method=delivery_method,
        shipping_address=shipping_address,
        order_notes=order_notes,
        order_id=order_id,
        payment_status="Новый",
        order_total_price=cart.get_cart_total(),
        coupon=cart.coupon,
        grand_total=cart.get_cart_total_price_after_coupon()
    )

    # Создаем элементы заказа из корзины
    cart_items = cart.cart_items.all()
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            kit_variant=cart_item.kit_variant,
            color_variant=cart_item.color_variant,
            carpet_color=cart_item.carpet_color,
            border_color=cart_item.border_color,
            has_podpyatnik=cart_item.has_podpyatnik,
            quantity=cart_item.quantity,
            product_price=cart_item.get_product_price(),
        )

    # Отмечаем корзину как оплаченную
    cart.is_paid = True
    cart.save()

    # Отправляем уведомление на email и Telegram
    send_order_notification(order)

    # Перенаправляем на страницу успешного оформления
    return redirect('success', order_id=order_id)


def success(request, order_id=None):
    """📦 Страница успешного оформления заказа"""
    # Если order_id не передан, пытаемся получить последний заказ пользователя
    if not order_id:
        if request.user.is_authenticated:
            latest_order = Order.objects.filter(user=request.user).order_by('-created_at').first()
        else:
            # Для анонимных пользователей используем сессию для поиска заказа
            session_id = request.session.session_key
            cart = Cart.objects.filter(session_id=session_id, is_paid=True).order_by('-created_at').first()
            latest_order = Order.objects.filter(cart=cart).first() if cart else None

        if latest_order:
            order_id = latest_order.order_id
        else:
            messages.warning(request, "Заказ не найден.")
            return redirect('index')

    # Получаем заказ
    order = get_object_or_404(Order, order_id=order_id)

    context = {
        'order': order,
        'order_id': order_id
    }
    return render(request, 'payment_success/payment_success.html', context)


@login_required
def profile_view(request, username):
    user_name = get_object_or_404(User, username=username)
    user = request.user
    profile = user.profile

    user_form = UserUpdateForm(instance=user)
    profile_form = UserProfileForm(instance=profile)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    context = {
        'user_name': user_name,
        'user_form': user_form,
        'profile_form': profile_form
    }

    return render(request, 'accounts/profile.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Ваш пароль успешно обновлен!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.warning(request, 'Пожалуйста, исправьте ошибки ниже.')
    else:
        form = CustomPasswordChangeForm(request.user)
        return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def update_shipping_address(request):
    shipping_address = ShippingAddress.objects.filter(
        user=request.user, current_address=True).first()

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=shipping_address)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.current_address = True
            shipping_address.save()

            messages.success(request, "Адрес доставки успешно сохранен/обновлен!")

            form = ShippingAddressForm()
        else:
            form = ShippingAddressForm(request.POST, instance=shipping_address)
    else:
        form = ShippingAddressForm(instance=shipping_address)

    return render(request, 'accounts/shipping_address_form.html', {'form': form})


# Order history view
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'accounts/order_history.html', {'orders': orders})


# Order Details view
@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    context = {
        'order': order,
        'order_items': order_items,
        'order_total_price': order.order_total_price,
        'coupon_discount': order.coupon.discount_amount if order.coupon else 0,
        'grand_total': order.grand_total
    }
    return render(request, 'accounts/order_details.html', context)


# Функция для генерации PDF
def render_to_pdf(template_src, context_dict={}):
    """Генерирует PDF из HTML шаблона"""
    if not PDF_ENABLED:
        return HttpResponse("PDF генерация недоступна. Установите xhtml2pdf.", status=400)

    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = f'attachment; filename="invoice_{context_dict.get("order", {}).get("order_id", "order")}.pdf"'

    # Создаем PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    # В случае ошибки
    if pisa_status.err:
        return HttpResponse('Ошибка при создании PDF', status=400)
    return response


# Download invoice view
@login_required
def download_invoice(request, order_id):
    order = Order.objects.filter(order_id=order_id).first()

    # Проверяем доступ - только владелец заказа или админ
    if request.user.is_authenticated:
        if not (order.user == request.user or request.user.is_staff):
            messages.error(request, "У вас нет доступа к этому заказу.")
            return redirect('index')
    else:
        # Для неавторизованных нужен специальный токен/хэш (можно добавить позже)
        messages.error(request, "Для доступа к заказу необходимо авторизоваться.")
        return redirect('login')

    order_items = order.order_items.all()

    context = {
        'order': order,
        'order_items': order_items,
    }

    return render_to_pdf('accounts/order_pdf_generate.html', context)


# Delete account feature
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Ваш аккаунт успешно удален.")
        return redirect('index')


# Проверка наличия товара в корзине (AJAX)
def check_cart_item(request, product_id):
    if request.method == 'GET':
        try:
            cart = Cart.get_cart(request)
            product = get_object_or_404(Product, uid=product_id)
            in_cart = CartItem.objects.filter(cart=cart, product=product).exists()

            return JsonResponse({'in_cart': in_cart})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)