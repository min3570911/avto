# accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from products.models import Product, ColorVariant, KitVariant, Coupon, Color
from home.models import ShippingAddress
from django.conf import settings
import os
import uuid


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL,
                                         related_name="shipping_address", null=True, blank=True)

    def __str__(self):
        return self.user.username

    def get_cart_count(self):
        return CartItem.objects.filter(cart__is_paid=False, cart__user=self.user).count()

    def save(self, *args, **kwargs):
        # Check if the profile image is being updated and profile exists
        if self.pk:  # Only if profile exists
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                if old_profile.profile_image and old_profile.profile_image != self.profile_image:
                    if old_profile.profile_image.path:
                        old_image_path = os.path.join(settings.MEDIA_ROOT, old_profile.profile_image.path)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
            except (Profile.DoesNotExist, ValueError, FileNotFoundError):
                # Обрабатываем различные возможные ошибки
                pass

        super(Profile, self).save(*args, **kwargs)


class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart", null=True, blank=True)
    session_id = models.CharField(max_length=50, null=True, blank=True)  # Для анонимных пользователей
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    # Поля Razorpay (оставляем для обратной совместимости)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_signature = models.CharField(max_length=100, null=True, blank=True)

    def get_cart_total(self):
        cart_items = self.cart_items.all()
        total_price = 0

        for cart_item in cart_items:
            total_price += cart_item.get_product_price()

        return total_price

    def get_cart_total_price_after_coupon(self):
        total = self.get_cart_total()

        if self.coupon and total >= self.coupon.minimum_amount:
            total -= self.coupon.discount_amount

        return total

    @classmethod
    def get_cart(cls, request):
        """Получить или создать корзину для пользователя/сессии"""
        if request.user.is_authenticated:
            cart, created = cls.objects.get_or_create(
                user=request.user,
                is_paid=False
            )
        else:
            if not request.session.session_key:
                request.session.create()

            cart, created = cls.objects.get_or_create(
                session_id=request.session.session_key,
                is_paid=False
            )
        return cart


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)
    kit_variant = models.ForeignKey(KitVariant, on_delete=models.SET_NULL, null=True, blank=True)
    carpet_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="cart_items_carpet")
    border_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="cart_items_border")
    quantity = models.IntegerField(default=1)
    has_podpyatnik = models.BooleanField(default=False)

    def get_product_price(self):
        price = self.product.price * self.quantity

        if self.color_variant:
            price += self.color_variant.price

        if self.kit_variant:
            price += float(self.kit_variant.price_modifier)

        # Добавляем стоимость подпятника если выбран
        if self.has_podpyatnik:
            # Ищем опцию подпятник в справочнике комплектаций
            podpyatnik_option = KitVariant.objects.filter(code='podpyatnik', is_option=True).first()
            if podpyatnik_option:
                price += float(podpyatnik_option.price_modifier)
            else:
                # Если записи нет, используем значение по умолчанию
                price += 15

        return price


class Order(BaseModel):
    # Убираем обязательную связь с пользователем
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)

    # Добавляем поля для контактной информации (делаем их необязательными для миграции)
    customer_name = models.CharField(max_length=100, verbose_name="Имя клиента", null=True, blank=True)
    customer_phone = models.CharField(max_length=20, verbose_name="Контактный телефон", null=True, blank=True)
    customer_email = models.EmailField(verbose_name="Email клиента", null=True, blank=True)

    # Информация о доставке
    delivery_method = models.CharField(
        max_length=20,
        choices=[
            ('europochta', 'Европочта по Беларуси'),
            ('belpochta', 'Белпочта по Беларуси'),
            ('yandex', 'Яндекс курьер по Минску')
        ],
        verbose_name="Способ доставки",
        null=True,  # Разрешаем null для миграции
        blank=True
    )
    shipping_address = models.TextField(verbose_name="Адрес доставки", blank=True, null=True)
    order_notes = models.TextField(blank=True, null=True, verbose_name="Примечание к заказу")

    # Основные поля заказа (оставляем как есть)
    order_id = models.CharField(max_length=100, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=100)
    payment_mode = models.CharField(max_length=100, default="Оплата при получении")
    order_total_price = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    # Для отслеживания заказа
    tracking_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Код отслеживания")

    def __str__(self):
        if self.customer_name:
            return f"Заказ #{self.order_id} от {self.customer_name}"
        return f"Заказ #{self.order_id}"

    def get_delivery_method_display(self):
        """Возвращает читаемое название способа доставки"""
        method_dict = dict(self._meta.get_field('delivery_method').choices)
        return method_dict.get(self.delivery_method, self.delivery_method)

    def save(self, *args, **kwargs):
        """Автоматически заполняем поля клиента на основе данных пользователя"""
        if self.user and not self.customer_name:
            full_name = f"{self.user.first_name} {self.user.last_name}".strip()
            self.customer_name = full_name if full_name else self.user.username

        if self.user and not self.customer_email and self.user.email:
            self.customer_email = self.user.email

        if self.user and not self.customer_phone:
            # Попытка получить телефон из профиля пользователя, если есть
            profile = Profile.objects.filter(user=self.user).first()
            if profile and hasattr(profile, 'phone') and profile.phone:
                self.customer_phone = profile.phone

        super().save(*args, **kwargs)


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    kit_variant = models.ForeignKey(KitVariant, on_delete=models.SET_NULL, null=True, blank=True)
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)
    carpet_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="order_items_carpet")
    border_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="order_items_border")
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    has_podpyatnik = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity}"

    def get_total_price(self):
        # Используем метод get_product_price из CartItem с учетом всех полей
        cart_item = CartItem(
            product=self.product,
            kit_variant=self.kit_variant,
            color_variant=self.color_variant,
            carpet_color=self.carpet_color,  # Добавляем цвет коврика
            border_color=self.border_color,  # Добавляем цвет окантовки
            quantity=self.quantity,
            has_podpyatnik=self.has_podpyatnik
        )
        return cart_item.get_product_price()