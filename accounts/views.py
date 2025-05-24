# accounts/views.py
# 🛒 Django views для e-commerce с Telegram уведомлениями (БЕЗ EMAIL)

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
from django.template.loader import get_template
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

# Импорт для генерации PDF
try:
    from xhtml2pdf import pisa

    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

# Настройка логгера
logger = logging.getLogger(__name__)


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
    🤖 Отправляет красивое уведомление о новом заказе в Telegram
    """
    try:
        # Получаем настройки из Django settings
        telegram_token = settings.TELEGRAM_BOT_TOKEN
        telegram_chat_id = settings.TELEGRAM_CHAT_ID

        # ⚠️ Проверяем наличие настроек
        if not telegram_token or not telegram_chat_id:
            logger.warning("⚠️ Telegram настройки отсутствуют. Добавьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env")
            return

        # URL для отправки сообщения
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

        # 📝 Собираем информацию о товарах
        items_text = ""
        total_items = 0

        for item in OrderItem.objects.filter(order=order):
            total_items += item.quantity

            # Информация о комплектации с экранированием специальных символов
            kit_info = f" ({item.kit_variant.name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')})" if item.kit_variant else ""

            # Информация о цветах с экранированием специальных символов
            color_info = ""
            if item.carpet_color:
                carpet_name = item.carpet_color.name.replace('_', '\\_').replace('*', '\\*').replace('[',
                                                                                                     '\\[').replace('`',
                                                                                                                    '\\`')
                color_info += f", коврик: {carpet_name}"
            if item.border_color:
                border_name = item.border_color.name.replace('_', '\\_').replace('*', '\\*').replace('[',
                                                                                                     '\\[').replace('`',
                                                                                                                    '\\`')
                color_info += f", окантовка: {border_name}"
            if item.has_podpyatnik:
                color_info += ", с подпятником"

            # Экранирование названия продукта
            product_name = item.product.product_name.replace('_', '\\_').replace('*', '\\*').replace('[',
                                                                                                     '\\[').replace('`',
                                                                                                                    '\\`')

            items_text += f"• {product_name}{kit_info}{color_info}\n"
            items_text += f"  Количество: {item.quantity} шт. × {item.product_price} BYN\n\n"

        # 🚚 Информация о доставке
        delivery_info = ""
        if hasattr(order, 'delivery_method') and order.delivery_method:
            delivery_methods = {
                'europochta': '📦 Европочта по Беларуси',
                'belpochta': '📮 Белпочта по Беларуси',
                'yandex': '🚚 Яндекс курьер по Минску',
                'pickup': '🏪 Самовывоз'
            }
            delivery_info = delivery_methods.get(order.delivery_method, order.delivery_method)

        # 📍 Адрес доставки (с экранированием)
        address_info = "Самовывоз"
        if order.shipping_address:
            address_info = order.shipping_address.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(
                '`', '\\`')

        # 📝 Формируем красивое сообщение
        # Экранирование имени и примечаний
        customer_name = order.customer_name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`',
                                                                                                                '\\`') if order.customer_name else ""
        customer_email = order.customer_email.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`',
                                                                                                                  '\\`') if order.customer_email else ""
        customer_phone = order.customer_phone.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`',
                                                                                                                  '\\`') if order.customer_phone else ""
        order_notes = order.order_notes.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`',
                                                                                                            '\\`') if order.order_notes else ""

        # 🔄 Используем HTML-форматирование вместо Markdown
        # Это поможет избежать проблем с экранированием в Markdown
        html_message = f"""<b>🛍️ НОВЫЙ ЗАКАЗ #{order.order_id}</b>

<b>👤 Клиент:</b> {order.customer_name}
<b>📱 Телефон:</b> {order.customer_phone}
<b>📧 Email:</b> {order.customer_email}

{f"<b>🚚 Доставка:</b> {delivery_info}" if delivery_info else ""}
<b>📍 Адрес:</b> {address_info}

<b>📦 Товары ({total_items} шт.):</b>
{items_text}<b>💰 ИТОГО:</b> {order.grand_total} BYN

{f"<b>💬 Примечание:</b> {order.order_notes}" if order.order_notes else ""}

<b>⏰ Заказ оформлен:</b> {order.order_date.strftime('%d.%m.%Y в %H:%M')}
"""

        # Параметры для отправки (используем HTML вместо Markdown)
        params = {
            "chat_id": telegram_chat_id,
            "text": html_message,
            "parse_mode": "HTML"  # Меняем режим форматирования на HTML
        }

        # 📡 Отправляем
        response = requests.post(url, params=params, timeout=15)

        logger.info(f"📡 Telegram API ответ: статус {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("ok"):
                message_id = response_data.get("result", {}).get("message_id")
                logger.info(f"✅ Telegram уведомление отправлено (ID сообщения: {message_id})")

                # 🎉 Отправляем дополнительное сообщение с кнопками
                send_telegram_buttons(order, telegram_token, telegram_chat_id)

            else:
                error_desc = response_data.get("description", "Неизвестная ошибка API")
                logger.error(f"❌ Ошибка Telegram API: {error_desc}")
                raise Exception(f"Telegram API: {error_desc}")
        else:
            logger.error(f"❌ HTTP ошибка: {response.status_code} - {response.text}")
            raise Exception(f"HTTP {response.status_code}: {response.text}")

    except requests.exceptions.Timeout:
        logger.error("⏱️ Таймаут при отправке уведомления в Telegram")
        raise Exception("Таймаут подключения к Telegram")

    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Ошибка сети при отправке уведомления в Telegram: {str(e)}")
        raise Exception(f"Ошибка сети: {str(e)}")

    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка при отправке уведомления в Telegram: {str(e)}")
        raise


def send_telegram_buttons(order, bot_token, chat_id):
    """
    🔘 Отправляет сообщение с кнопками для быстрых действий
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # Создаем inline кнопки
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Принять заказ", "callback_data": f"accept_{order.order_id}"},
                    {"text": "❌ Отклонить", "callback_data": f"decline_{order.order_id}"}
                ],
                [
                    {"text": "📞 Позвонить", "url": f"tel:{order.customer_phone.replace('+', '').replace(' ', '')}"},
                    {"text": "💬 WhatsApp",
                     "url": f"https://wa.me/{order.customer_phone.replace('+', '').replace(' ', '')}"}
                ]
            ]
        }

        # Используем HTML вместо Markdown для согласованности с основным сообщением
        params = {
            "chat_id": chat_id,
            "text": f"<b>🎯 Действия для заказа #{order.order_id}:</b>",
            "parse_mode": "HTML",  # Используем HTML вместо Markdown
            "reply_markup": json.dumps(keyboard)
        }

        response = requests.post(url, params=params, timeout=10)

        if response.status_code == 200 and response.json().get("ok"):
            logger.info(f"✅ Кнопки для заказа #{order.order_id} отправлены")
        else:
            logger.warning(f"⚠️ Не удалось отправить кнопки: {response.text}")

    except Exception as e:
        # Ошибка кнопок не критична
        logger.warning(f"⚠️ Не удалось отправить кнопки для заказа {order.order_id}: {e}")


def send_order_notification(order):
    """🤖 Отправляет уведомление о заказе ТОЛЬКО в Telegram"""
    try:
        send_telegram_notification(order)
        logger.info(f"✅ Уведомление о заказе #{order.order_id} отправлено в Telegram")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления о заказе #{order.order_id}: {str(e)}")


def place_order(request):
    """🛒 Обработка оформления заказа - ИСПРАВЛЕНО под текущую форму"""

    print("🔍 Начинаем обработку заказа...")  # Отладочная информация

    if request.method != 'POST':
        print("❌ Неверный метод запроса")
        return redirect('cart')

    try:
        # Получаем корзину пользователя или сессии
        cart = Cart.get_cart(request)
        print(f"🛒 Корзина получена: {cart.uid}")

        # Проверяем, есть ли товары в корзине
        if not cart.cart_items.exists():
            print("❌ Корзина пуста")
            messages.warning(request, "Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
            return redirect('index')

        # 📝 Получаем данные формы (ИСПРАВЛЕНО под текущую структуру)
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_city = request.POST.get('customer_city', '').strip()  # 🆕 НОВОЕ ПОЛЕ
        need_delivery = request.POST.get('need_delivery') == 'on'  # 🆕 ЧЕКБОКС
        terms_agree = request.POST.get('terms_agree') == 'on'  # 🆕 ЧЕКБОКС
        order_notes = request.POST.get('order_notes', '').strip()

        print(f"📝 Данные формы:")
        print(f"  - customer_name: '{customer_name}'")
        print(f"  - customer_phone: '{customer_phone}'")
        print(f"  - customer_city: '{customer_city}'")
        print(f"  - need_delivery: {need_delivery}")
        print(f"  - terms_agree: {terms_agree}")

        # 🚚 Поля доставки (только если нужна доставка)
        delivery_method = 'pickup'  # По умолчанию самовывоз
        shipping_address = ''

        if need_delivery:
            delivery_method = request.POST.get('delivery_method', 'europochta')
            shipping_address = request.POST.get('shipping_address', '').strip()
            print(f"  - delivery_method: '{delivery_method}'")
            print(f"  - shipping_address: '{shipping_address}'")

        # 📧 Генерируем email (так как в форме его нет)
        if request.user.is_authenticated and request.user.email:
            customer_email = request.user.email
        else:
            # Создаем временный email из телефона
            phone_clean = customer_phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(
                ')', '')
            customer_email = f"order_{phone_clean}@temp.local"

        print(f"  - customer_email (сгенерирован): '{customer_email}'")

        # ✅ Проверяем обязательные поля
        missing_fields = []
        if not customer_name:
            missing_fields.append('Имя')
        if not customer_phone:
            missing_fields.append('Телефон')
        if not customer_city:
            missing_fields.append('Город')
        if not terms_agree:
            missing_fields.append('Согласие с условиями')

        # Проверяем поля доставки только если доставка нужна
        if need_delivery and not shipping_address:
            missing_fields.append('Адрес доставки')

        if missing_fields:
            error_msg = f"Не заполнены обязательные поля: {', '.join(missing_fields)}"
            print(f"❌ {error_msg}")
            messages.error(request, error_msg)
            return redirect('cart')

        # 💰 Рассчитываем стоимость
        order_total = cart.get_cart_total()
        grand_total = cart.get_cart_total_price_after_coupon()
        print(f"💰 Стоимость: {order_total}, итого: {grand_total}")

        # 🆔 Создаем уникальный ID заказа
        order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        print(f"🆔 ID заказа: {order_id}")

        # 📦 Создаем заказ
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
            order_total_price=order_total,
            coupon=cart.coupon,
            grand_total=grand_total
        )

        print(f"✅ Заказ создан в БД: {order.pk}")

        # 📋 Создаем элементы заказа из корзины
        cart_items = cart.cart_items.all()
        created_items = 0

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
            created_items += 1
            print(f"📦 Создан элемент заказа: {cart_item.product.product_name}")

        print(f"✅ Создано элементов заказа: {created_items}")

        # 🔒 Отмечаем корзину как оплаченную
        cart.is_paid = True
        cart.save()
        print(f"🔒 Корзина отмечена как оплаченная")

        # 📧 Отправляем уведомления (если настроены)
        try:
            send_order_notification(order)
            print(f"📧 Уведомления отправлены")
        except Exception as e:
            print(f"⚠️ Ошибка отправки уведомлений: {e}")
            # Не блокируем создание заказа из-за ошибок уведомлений

        # ✅ Показываем сообщение об успехе
        delivery_text = "с доставкой" if need_delivery else "самовывоз"
        success_msg = f"🎉 Заказ #{order_id} успешно оформлен ({delivery_text})! Наш менеджер свяжется с вами в ближайшее время."
        messages.success(request, success_msg)
        print(f"🎉 {success_msg}")

        # 🔄 Перенаправляем на страницу успешного оформления
        return redirect('success', order_id=order_id)

    except Exception as e:
        # 🚨 Обработка ошибок
        error_msg = f"Произошла ошибка при оформлении заказа: {str(e)}"
        print(f"❌ ОШИБКА: {error_msg}")
        print(f"❌ Трейсбек: {e}")
        messages.error(request,
                       "Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз или свяжитесь с поддержкой.")
        return redirect('cart')


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