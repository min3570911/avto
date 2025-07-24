# 📁 accounts/models.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
# 🛥️ ДОБАВЛЕНО: Методы для отображения размеров лодок в корзине
# 🔧 ИСПРАВЛЕНО: Импорт products.models → references.models

from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from references.models import Product, KitVariant, Coupon, Color  # ✅ ИСПРАВЛЕНО: products → references
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
    """📦 Товар в корзине с поддержкой размеров лодок"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    kit_variant = models.ForeignKey(KitVariant, on_delete=models.SET_NULL, null=True, blank=True)
    carpet_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="cart_items_carpet")
    border_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="cart_items_border")
    quantity = models.IntegerField(default=1)
    has_podpyatnik = models.BooleanField(default=False)

    def get_product_price(self):
        """💰 ФИНАЛЬНЫЙ: Правильный расчет стоимости БЕЗ подпятника для лодок"""

        if not self.product:
            return 0

        # 🛥️ ЛОГИКА ДЛЯ ЛОДОК (упрощенная)
        if self.product.is_boat_product():
            # ✅ Для лодок ТОЛЬКО базовая цена, БЕЗ комплектаций и подпятника
            base_price = self.product.price or 0
            return float(base_price * self.quantity)

        # 🚗 ЛОГИКА ДЛЯ АВТОМОБИЛЕЙ (сложная)
        base_price = self.product.price or 0
        kit_price = 0
        podpyatnik_price = 0

        # 📦 Добавляем стоимость комплектации
        if self.kit_variant:
            kit_price = float(self.kit_variant.price_modifier)

        # 🦶 Добавляем стоимость подпятника
        if self.has_podpyatnik:
            podpyatnik_option = KitVariant.objects.filter(
                code='podpyatnik', is_option=True
            ).first()
            if podpyatnik_option:
                podpyatnik_price = float(podpyatnik_option.price_modifier)

        # 💰 Итоговая цена за единицу × количество
        unit_price = base_price + kit_price + podpyatnik_price
        return float(unit_price * self.quantity)

    def get_product_dimensions(self):
        """📐 Получение размеров лодки для отображения в корзине"""
        if self.product and self.product.is_boat_product():
            return self.product.get_boat_dimensions()
        return None

    def get_product_description_info(self):
        """📝 Полное описание товара в корзине для шаблона"""
        info_parts = []

        # 🛥️ Размеры для лодок
        dimensions = self.get_product_dimensions()
        if dimensions:
            info_parts.append(f"📏 Размер: {dimensions}")

        # 📦 Комплектация для автомобилей
        if self.kit_variant:
            info_parts.append(f"Комплектация: {self.kit_variant.name}")

        # 🎨 Цвета
        if self.carpet_color:
            info_parts.append(f"Цвет коврика: {self.carpet_color.name}")

        if self.border_color:
            info_parts.append(f"Цвет окантовки: {self.border_color.name}")

        # 🦶 Подпятник для автомобилей
        if self.has_podpyatnik:
            info_parts.append("🦶 С подпятником")

        return info_parts

    def get_short_description(self):
        """📝 Краткое описание для админки"""
        if not self.product:
            return "Удаленный товар"

        parts = [self.product.product_name]

        # 🛥️ Размеры для лодок
        if self.product.is_boat_product():
            dimensions = self.get_product_dimensions()
            if dimensions:
                parts.append(f"({dimensions})")
        else:
            # 🚗 Комплектация для автомобилей
            if self.kit_variant:
                parts.append(f"({self.kit_variant.name})")

        return " ".join(parts)

    def __str__(self):
        """Строковое представление товара в корзине"""
        if not self.product:
            return f"Удаленный товар - {self.quantity} шт."

        # 🛥️ Для лодок показываем размеры
        if self.product.is_boat_product():
            dimensions = self.get_product_dimensions()
            size_info = f" ({dimensions})" if dimensions else ""
            return f"{self.product.product_name}{size_info} - {self.quantity} шт."

        # 🚗 Для автомобилей показываем комплектацию
        kit_info = f" ({self.kit_variant.name})" if self.kit_variant else ""
        return f"{self.product.product_name}{kit_info} - {self.quantity} шт."

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"


class Order(BaseModel):
    """📦 Модель заказов"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=50, null=True, blank=True)  # Для анонимных заказов
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, blank=True)

    # 📝 Контактная информация
    customer_name = models.CharField(max_length=100, verbose_name="Имя клиента")
    customer_phone = models.CharField(max_length=20, verbose_name="Телефон клиента")
    customer_email = models.EmailField(blank=True, null=True, verbose_name="Email клиента")

    # 📍 Адрес доставки
    delivery_address = models.TextField(verbose_name="Адрес доставки")
    delivery_notes = models.TextField(blank=True, null=True, verbose_name="Примечания к доставке")

    # 💰 Финансовая информация
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    # 📊 Статус заказа
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")

    # 🕐 Временные метки
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    delivery_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата доставки")

    def get_total_items(self):
        """📊 Общее количество товаров в заказе"""
        return sum([item.quantity for item in self.order_items.all()])

    def get_order_summary(self):
        """📝 Краткое описание заказа"""
        items_count = self.get_total_items()
        return f"Заказ #{self.pk} от {self.order_date.strftime('%d.%m.%Y')} - {items_count} товаров на {self.total_amount} BYN"

    def __str__(self):
        customer_info = self.customer_name if self.customer_name else f"Анонимный ({self.session_id[:8]}...)"
        return f"Заказ #{self.pk} - {customer_info} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-order_date']


class OrderItem(BaseModel):
    """📦 Товар в заказе"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    kit_variant = models.ForeignKey(KitVariant, on_delete=models.SET_NULL, null=True, blank=True)
    carpet_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="order_items_carpet")
    border_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="order_items_border")
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    has_podpyatnik = models.BooleanField(default=False)

    def __str__(self):
        """Строковое представление товара в заказе"""
        product_name = self.product.product_name if self.product else "Удаленный товар"
        return f"{product_name} - {self.quantity}"

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

# 🔧 КЛЮЧЕВЫЕ ДОБАВЛЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# 🛥️ НОВЫЕ МЕТОДЫ В CartItem:
# ✅ get_product_dimensions() - получение размеров лодки (150×200 см)
# ✅ get_product_description_info() - полное описание товара в корзине
# ✅ get_short_description() - краткое описание для админки
# ✅ Обновленный __str__() с размерами лодок
#
# 📝 РЕЗУЛЬТАТ:
# - В корзине для лодок будет показываться: "📏 Размер: 150×200 см"
# - В корзине для автомобилей: комплектация, цвета, подпятник
# - В админке: улучшенное отображение товаров с размерами
# - Полная обратная совместимость с автомобильными товарами
#
# 🎯 ИСПОЛЬЗОВАНИЕ В ШАБЛОНЕ:
# {{ cart_item.get_product_dimensions }} - размеры лодки
# {% for info in cart_item.get_product_description_info %} - полная информация
#
# ⚠️ ВАЖНО:
# После замены этого файла нужно обновить шаблон корзины
# для отображения размеров лодок!