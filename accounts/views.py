# accounts/views.py
# 🛒 Django views для e-commerce с Telegram уведомлениями (УПРОЩЕННАЯ ВЕРСИЯ)
# 📝 Только корзина и оформление заказов для анонимных пользователей

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
from django.contrib.auth.models import User
from accounts.models import Cart, CartItem, Order, OrderItem
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404

# Настройка логгера
logger = logging.getLogger(__name__)


def cart(request):
    """🛒 Отображение корзины с формой оформления заказа для анонимных пользователей"""
    cart_obj = None

    try:
        # Получаем корзину для текущего пользователя/сессии
        cart_obj = Cart.get_cart(request)

    except Exception as e:
        messages.warning(request, "Ваша корзина пуста. Пожалуйста, добавьте товар в корзину.")
        return redirect('/')  # 🔄 Перенаправляем на главную вместо 'index'

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

    # ✅ Убираем предзаполнение данных пользователя (анонимные заказы)
    initial_data = {}

    context = {
        'cart': cart_obj,
        'quantity_range': range(1, 11),  # Для выбора количества товаров
        'initial_data': initial_data
    }
    return render(request, 'accounts/cart.html', context)


@require_POST
def update_cart_item(request):
    """🔄 Обновление количества товаров в корзине с возвратом всех необходимых данных"""
    try:
        # 📥 Получаем данные из запроса
        data = json.loads(request.body)
        cart_item_id = data.get("cart_item_id")
        quantity = int(data.get("quantity"))

        # ✅ Валидация количества
        if quantity <= 0:
            return JsonResponse({
                "success": False,
                "error": "Количество должно быть больше 0"
            }, status=400)

        if quantity > 99:  # 🚧 Максимальное количество
            return JsonResponse({
                "success": False,
                "error": "Максимальное количество - 99 штук"
            }, status=400)

        # 🛒 Получаем корзину пользователя/сессии
        cart = Cart.get_cart(request)

        # 🔍 Находим элемент корзины (убрали избыточное условие cart__is_paid=False)
        try:
            cart_item = CartItem.objects.get(uid=cart_item_id, cart=cart)
        except CartItem.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Товар не найден в корзине"
            }, status=404)

        # 💾 Обновляем количество
        cart_item.quantity = quantity
        cart_item.save()

        # 💰 Рассчитываем новую цену товара
        item_total_price = cart_item.get_product_price()

        # 💳 Рассчитываем общую стоимость корзины
        cart_total = cart.get_cart_total()
        cart_total_after_coupon = cart.get_cart_total_price_after_coupon()

        # ✅ Возвращаем ПОЛНЫЙ ответ для обновления интерфейса
        return JsonResponse({
            "success": True,
            "cart_item_id": str(cart_item_id),  # 🆔 ID товара для обновления цены
            "item_price": float(item_total_price),  # 💰 Новая цена товара
            "cart_total": float(cart_total),  # 🛒 Общая сумма корзины
            "cart_total_after_coupon": float(cart_total_after_coupon),  # 💳 Сумма с купоном
            "quantity": quantity  # 🔢 Подтверждение количества
        })

    except ValueError:
        # 🚨 Ошибка преобразования количества в число
        return JsonResponse({
            "success": False,
            "error": "Неверное значение количества"
        }, status=400)

    except json.JSONDecodeError:
        # 🚨 Ошибка парсинга JSON
        return JsonResponse({
            "success": False,
            "error": "Неверный формат данных"
        }, status=400)

    except Exception as e:
        # 🚨 Общая обработка ошибок
        logger.error(f"Ошибка обновления корзины: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Произошла ошибка при обновлении корзины"
        }, status=500)


def remove_cart(request, uid):
    """🗑️ Удаление товара из корзины"""
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
    """🎫 Удаление купона из корзины"""
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
    """🤖 Отправляет красивое уведомление о новом заказе в Telegram"""
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

        # 📝 Собираем информацию о товарах с красивым форматированием
        items_text = ""
        total_items = 0

        for item in OrderItem.objects.filter(order=order):
            total_items += item.quantity

            # 🏷️ Наименование товара с эмодзи
            product_name = item.product.product_name
            items_text += f"🚘 <b>{product_name}</b>\n"

            # 📋 Информация о комплектации
            if item.kit_variant:
                items_text += f"   📦 Комплектация: {item.kit_variant.name}\n"

            # 🎨 Информация о цветах
            if item.carpet_color:
                carpet_emoji = getattr(item.carpet_color, 'emoji', '🎨')
                items_text += f"   {carpet_emoji} Коврик: {item.carpet_color.name}\n"

            if item.border_color:
                border_emoji = getattr(item.border_color, 'emoji', '🎨')
                items_text += f"   {border_emoji} Окантовка: {item.border_color.name}\n"

            if item.has_podpyatnik:
                items_text += f"   👞 С подпятником\n"

            # 🔢 ИСПРАВЛЕННЫЙ расчет цены за единицу и общей суммы
            total_item_price = float(item.product_price)  # Общая цена позиции
            unit_price = total_item_price / item.quantity  # Цена за единицу

            items_text += f"   🔢 Количество: <b>{item.quantity} шт. × {unit_price:.2f} BYN</b>\n"
            items_text += f"   💵 Сумма: <b>{total_item_price:.2f} BYN</b>\n\n"

        # 🚚 Информация о доставке
        delivery_info = ""
        if hasattr(order, 'delivery_method') and order.delivery_method:
            delivery_methods = {
                'europochta': '📦 Европочта по Беларуси',
                'belpochta': '📮 Белпочта по Беларуси',
                'yandex': ' 🚕 Яндекс курьер по Минску',
                'pickup': '🏪 Самовывоз'
            }
            delivery_info = delivery_methods.get(order.delivery_method, order.delivery_method)
        # 📍 Адрес доставки
        address_info = "🏪 Самовывоз"
        if order.shipping_address:
            address_info = f"📍 {order.shipping_address}"

        # 🔄 Формируем красивое сообщение
        html_message = f"""<b>🛍️ НОВЫЙ ЗАКАЗ #{order.order_id}</b>

<b>👤 Клиент:</b> {order.customer_name}
<b>📱 Телефон:</b> {order.customer_phone}

{f"<b>🚚 Доставка:</b> {delivery_info}" if delivery_info else ""}
<b>{address_info}</b>

<b>📦 ТОВАРЫ ({total_items} шт.):</b>
{items_text}<b>💰 ИТОГО: {order.grand_total} BYN</b>

{f"<b>💬 Примечание:</b> {order.order_notes}" if order.order_notes else ""}

<b>⏰ Заказ оформлен:</b> {order.order_date.strftime('%d.%m.%Y в %H:%M')}
"""

        # Параметры для отправки
        params = {
            "chat_id": telegram_chat_id,
            "text": html_message,
            "parse_mode": "HTML"
        }

        # 📡 Отправляем
        response = requests.post(url, params=params, timeout=15)

        logger.info(f"📡 Telegram API ответ: статус {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("ok"):
                message_id = response_data.get("result", {}).get("message_id")
                logger.info(f"✅ Telegram уведомление отправлено (ID сообщения: {message_id})")
            else:
                error_desc = response_data.get("description", "Неизвестная ошибка API")
                logger.error(f"❌ Ошибка Telegram API: {error_desc}")
                raise Exception(f"Telegram API: {error_desc}")
        else:
            logger.error(f"❌ HTTP ошибка: {response.status_code} - {response.text}")
            raise Exception(f"HTTP {response.status_code}: {response.text}")

    except Exception as e:
        logger.error(f"💥 Ошибка при отправке уведомления в Telegram: {str(e)}")
        # Не прерываем создание заказа из-за ошибок уведомлений


def send_order_notification(order):
    """🤖 Отправляет уведомление о заказе ТОЛЬКО в Telegram"""
    try:
        send_telegram_notification(order)
        logger.info(f"✅ Уведомление о заказе #{order.order_id} отправлено в Telegram")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления о заказе #{order.order_id}: {str(e)}")


def place_order(request):
    """🛒 Обработка оформления заказа для анонимных пользователей"""

    print("🔍 Начинаем обработку заказа...")

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
            return redirect('/')

        # 📝 Получаем данные формы
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_city = request.POST.get('customer_city', '').strip()
        need_delivery = request.POST.get('need_delivery') == 'on'
        terms_agree = request.POST.get('terms_agree') == 'on'
        order_notes = request.POST.get('order_notes', '').strip()

        # 🚚 Поля доставки
        delivery_method = 'pickup'
        shipping_address = ''

        if need_delivery:
            delivery_method = request.POST.get('delivery_method', 'europochta')
            shipping_address = request.POST.get('shipping_address', '').strip()

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

        # 🆔 ИСПРАВЛЕННЫЙ БЛОК: Генерация красивого номера заказа
        from datetime import datetime

        # 📊 ИСПРАВЛЕНО: Используем count() вместо Max('id')
        existing_orders_count = Order.objects.count()
        next_number = existing_orders_count + 1

        # 📅 Дата ДДММ
        today = datetime.now()
        date_part = today.strftime("%d%m%y")

        # 🏙️ Город (всегда из поля)
        city_part = customer_city.strip().title() if customer_city else "Город"

        # 🔢 Собираем номер: 001-2007-Минск
        order_id = f"{next_number:03d}-{date_part}-{city_part}"

        print(f"🆔 Сгенерирован номер заказа: {order_id}")

        # 📦 Создаем заказ (остальной код без изменений)
        order = Order.objects.create(
            user=None,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email="",
            customer_city=customer_city,
            delivery_method=delivery_method,
            shipping_address=shipping_address,
            order_notes=order_notes,
            order_id=order_id,  # ✅ Используем новый формат
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
                carpet_color=cart_item.carpet_color,
                border_color=cart_item.border_color,
                has_podpyatnik=cart_item.has_podpyatnik,
                quantity=cart_item.quantity,
                product_price=cart_item.get_product_price(),
            )
            created_items += 1

        print(f"✅ Создано элементов заказа: {created_items}")

        # 🔒 Отмечаем корзину как оплаченную
        cart.is_paid = True
        cart.save()

        # 📧 Отправляем уведомления
        try:
            send_order_notification(order)
        except Exception as e:
            print(f"⚠️ Ошибка отправки уведомлений: {e}")

        # ✅ Показываем сообщение об успехе
        delivery_text = "с доставкой" if need_delivery else "самовывоз"
        success_msg = f"🎉 Заказ #{order_id} успешно оформлен ({delivery_text})! Наш менеджер свяжется с вами в ближайшее время."
        messages.success(request, success_msg)

        # 🔄 Перенаправляем на страницу успешного оформления
        return redirect('success', order_id=order_id)

    except Exception as e:
        # 🚨 Обработка ошибок
        error_msg = f"Произошла ошибка при оформлении заказа: {str(e)}"
        print(f"❌ ОШИБКА: {error_msg}")
        messages.error(request,
                       "Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз или свяжитесь с поддержкой.")
        return redirect('cart')


def success(request, order_id=None):
    """📦 Страница успешного оформления заказа"""
    # Если order_id не передан, показываем общее сообщение
    if not order_id:
        context = {
            'order': None,
            'order_id': None
        }
        return render(request, 'payment_success/payment_success.html', context)

    # Получаем заказ (может быть анонимным)
    order = get_object_or_404(Order, order_id=order_id)

    context = {
        'order': order,
        'order_id': order_id
    }
    return render(request, 'payment_success/payment_success.html', context)


def check_cart_item(request, product_id):
    """✅ Проверка наличия товара в корзине (AJAX)"""
    if request.method == 'GET':
        try:
            cart = Cart.get_cart(request)
            product = get_object_or_404(Product, uid=product_id)
            in_cart = CartItem.objects.filter(cart=cart, product=product).exists()

            return JsonResponse({'in_cart': in_cart})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)