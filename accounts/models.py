# 📁 accounts/models.py - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ ColorVariant
# 🚨 УБРАН ИМПОРТ ColorVariant и все связанные поля

from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from products.models import Product, KitVariant, Coupon, Color
from django.conf import settings
import os
import uuid


class Profile(BaseModel):
    """👤 Профиль пользователя (только для админов)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def get_cart_count(self):
        """📊 Количество товаров в корзине (для админов)"""
        return CartItem.objects.filter(cart__is_paid=False, cart__user=self.user).count()

    def save(self, *args, **kwargs):
        """💾 Удаляем старое изображение при обновлении"""
        if self.pk:  # Только если профиль существует
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                if old_profile.profile_image and old_profile.profile_image != self.profile_image:
                    if old_profile.profile_image.path:
                        old_image_path = os.path.join(settings.MEDIA_ROOT, old_profile.profile_image.path)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
            except (Profile.DoesNotExist, ValueError, FileNotFoundError):
                pass

        super(Profile, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class Cart(BaseModel):
    """🛒 Корзина (поддерживает анонимных пользователей)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart", null=True, blank=True)
    session_id = models.CharField(max_length=50, null=True, blank=True)  # 🆕 Для анонимных пользователей
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def get_cart_total(self):
        """💰 Общая стоимость корзины"""
        cart_items = self.cart_items.all()
        total_price = 0

        for cart_item in cart_items:
            total_price += cart_item.get_product_price()

        return total_price

    def get_cart_total_price_after_coupon(self):
        """💳 Стоимость с учетом купона"""
        total = self.get_cart_total()

        if self.coupon and total >= self.coupon.minimum_amount:
            total -= self.coupon.discount_amount

        return total

    @classmethod
    def get_anonymous_cart(cls, request):
        """
        🛒 Получить или создать анонимную корзину

        🆕 ОБНОВЛЕННАЯ ВЕРСИЯ: работает только с сессиями (без пользователей)
        """
        # 🔑 Создаем сессию если её нет
        if not request.session.session_key:
            request.session.create()

        # 🔍 Ищем или создаем корзину по сессии
        cart, created = cls.objects.get_or_create(
            session_id=request.session.session_key,
            is_paid=False,
            defaults={'user': None}  # 🚫 Без пользователя
        )

        return cart

    # 🔄 LEGACY метод для совместимости
    @classmethod
    def get_cart(cls, request):
        """🔄 Устаревший метод, перенаправляет на get_anonymous_cart"""
        return cls.get_anonymous_cart(request)

    def __str__(self):
        if self.user:
            return f"Корзина {self.user.username}"
        return f"Анонимная корзина {self.session_id[:8]}..."

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"


class CartItem(BaseModel):
    """📦 Товар в корзине"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    # 🗑️ УДАЛЕНО: color_variant поле (ColorVariant больше не существует)
    kit_variant = models.ForeignKey(KitVariant, on_delete=models.SET_NULL, null=True, blank=True)
    carpet_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="cart_items_carpet")
    border_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="cart_items_border")
    quantity = models.IntegerField(default=1)
    has_podpyatnik = models.BooleanField(default=False)

    def get_product_price(self):
        """💰 Рассчитать стоимость товара с учетом всех опций"""
        # 🎯 Базовая цена за один товар
        base_price = self.product.price if self.product.price else 0

        # ➕ Добавляем стоимость комплектации
        if self.kit_variant:
            base_price += float(self.kit_variant.price_modifier)

        # 🦶 Добавляем стоимость подпятника если выбран
        if self.has_podpyatnik:
            podpyatnik_option = KitVariant.objects.filter(code='podpyatnik', is_option=True).first()
            if podpyatnik_option:
                base_price += float(podpyatnik_option.price_modifier)
            else:
                # 🔄 Запасной вариант
                base_price += 20

        # ✖️ Умножаем полную цену единицы товара на количество
        return base_price * self.quantity

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity}"

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"


class Order(BaseModel):
    """📦 Заказ (анонимный)"""
    # 🆕 Пользователь не обязателен (анонимные заказы)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)

    # 📝 Контактная информация клиента (ОБЯЗАТЕЛЬНАЯ)
    customer_name = models.CharField(max_length=100, verbose_name="Имя клиента")
    customer_phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    customer_email = models.EmailField(verbose_name="Email клиента")
    customer_city = models.CharField(max_length=100, verbose_name="Город клиента")

    # 🚚 Информация о доставке
    delivery_method = models.CharField(
        max_length=20,
        choices=[
            ('pickup', 'Самовывоз'),
            ('europochta', 'Европочта по Беларуси'),
            ('belpochta', 'Белпочта по Беларуси'),
            ('yandex', 'Яндекс курьер по Минску')
        ],
        default='pickup',
        verbose_name="Способ доставки"
    )
    shipping_address = models.TextField(verbose_name="Адрес доставки", blank=True, null=True)
    order_notes = models.TextField(blank=True, null=True, verbose_name="Примечание к заказу")

    # 📦 Основные поля заказа
    order_id = models.CharField(max_length=100, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=100, default="Новый")
    payment_mode = models.CharField(max_length=100, default="Оплата при получении")
    order_total_price = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    # 📍 Для отслеживания заказа
    tracking_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Код отслеживания")

    def __str__(self):
        return f"Заказ #{self.order_id} от {self.customer_name}"

    def get_delivery_method_display_custom(self):
        """🚚 Получить читаемое название способа доставки"""
        choices_dict = {
            'pickup': 'Самовывоз',
            'europochta': 'Европочта по Беларуси',
            'belpochta': 'Белпочта по Беларуси',
            'yandex': 'Яндекс курьер по Минску'
        }
        return choices_dict.get(self.delivery_method, self.delivery_method)

    def save(self, *args, **kwargs):
        """💾 Автозаполнение полей клиента от пользователя (если есть)"""
        if self.user and not self.customer_name:
            full_name = f"{self.user.first_name} {self.user.last_name}".strip()
            self.customer_name = full_name if full_name else self.user.username

        if self.user and not self.customer_email and self.user.email:
            self.customer_email = self.user.email

        if self.user and not self.customer_phone:
            # 📱 Попытка получить телефон из профиля пользователя
            try:
                profile = self.user.profile
                if hasattr(profile, 'phone') and profile.phone:
                    self.customer_phone = profile.phone
            except:
                pass

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-order_date']


class OrderItem(BaseModel):
    """📋 Товар в заказе"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    kit_variant = models.ForeignKey(KitVariant, on_delete=models.SET_NULL, null=True, blank=True)
    # 🗑️ УДАЛЕНО: color_variant поле (ColorVariant больше не существует)
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
        """💰 Общая стоимость позиции заказа"""
        # 🔄 Используем метод get_product_price из CartItem с учетом всех полей
        cart_item = CartItem(
            product=self.product,
            kit_variant=self.kit_variant,
            carpet_color=self.carpet_color,
            border_color=self.border_color,
            quantity=self.quantity,
            has_podpyatnik=self.has_podpyatnik
        )
        return cart_item.get_product_price()

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

# 🗑️ ИЗМЕНЕНИЯ:
# ✅ УБРАН импорт ColorVariant из products.models
# ✅ УДАЛЕНО поле color_variant из CartItem
# ✅ УДАЛЕНО поле color_variant из OrderItem
# ✅ ОБНОВЛЕН метод get_product_price() в CartItem (убрана проверка color_variant)