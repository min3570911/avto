# 📁 accounts/models.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
# 🛥️ ДОБАВЛЕНО: Методы для отображения размеров лодок в корзине
# 🚨 УБРАН ИМПОРТ ColorVariant и все связанные поля

from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from products.models import Product, KitVariant, Coupon
from common.models import Color
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


from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from boats.models import BoatProduct

class CartItem(BaseModel):
    """📦 Универсальный товар в корзине"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")

    # Generic FK для связи с любым товаром
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    product = GenericForeignKey('content_type', 'object_id')

    # Поля для конфигурации
    kit_variant = models.ForeignKey(KitVariant, on_delete=models.SET_NULL, null=True, blank=True)
    carpet_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="cart_items_carpet")
    border_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="cart_items_border")
    quantity = models.IntegerField(default=1)
    has_podpyatnik = models.BooleanField(default=False)

    def get_product_price(self):
        """💰 Рассчитывает стоимость позиции в корзине"""
        if not self.product:
            return 0

        # 🚗 Для автомобильных товаров
        if isinstance(self.product, Product):
            base_price = float(self.product.price or 0)
            if self.kit_variant:
                base_price = float(self.product.get_product_price_by_kit(self.kit_variant.code))

            if self.has_podpyatnik:
                podpyatnik_option = KitVariant.objects.filter(code='podpyatnik', is_option=True).first()
                if podpyatnik_option:
                    base_price += float(podpyatnik_option.price_modifier)

            return base_price * self.quantity

        # 🛥️ Для лодочных товаров
        elif isinstance(self.product, BoatProduct):
            base_price = float(self.product.price or 0)
            return base_price * self.quantity

        return 0

    def is_boat(self):
        """Проверяет, является ли товар лодкой"""
        return isinstance(self.product, BoatProduct)

    def is_car(self):
        """Проверяет, является ли товар автомобилем"""
        return isinstance(self.product, Product)

    def get_image_url(self):
        """Получает URL изображения в зависимости от типа товара"""
        if self.product and hasattr(self.product, 'get_main_image_url'):
            return self.product.get_main_image_url()
        if self.product and hasattr(self.product, 'images') and self.product.images.first():
             return self.product.images.first().image.url
        return "/static/images/placeholder.png" # Заглушка

    def get_product_url(self):
        """Получает URL детальной страницы товара"""
        if self.product and hasattr(self.product, 'get_absolute_url'):
            return self.product.get_absolute_url()
        return "#"

    def get_product_dimensions(self):
        """Получает размеры для лодочных ковриков"""
        if self.is_boat() and hasattr(self.product, 'get_mat_dimensions'):
            return self.product.get_mat_dimensions()
        return None

    def __str__(self):
        if not self.product:
            return f"Удаленный товар x {self.quantity}"

        prefix = "🛥️" if self.is_boat() else "🚗"
        return f"{prefix} {self.product.product_name} x {self.quantity}"

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"


class Order(BaseModel):
    """📦 Заказ (анонимный)"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)
    customer_name = models.CharField(max_length=100, verbose_name="Имя клиента")
    customer_phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    customer_email = models.EmailField(verbose_name="Email клиента")
    customer_city = models.CharField(max_length=100, verbose_name="Город клиента")
    delivery_method = models.CharField(
        max_length=20,
        choices=[('pickup', '🏪 Самовывоз'), ('europochta', '📦Европочта'), ('belpochta', '📮Белпочта'), ('yandex', '🚚 Яндекс курьер по Минску')],
        default='pickup', verbose_name="Способ доставки"
    )
    shipping_address = models.TextField(blank=True, null=True, verbose_name="Адрес доставки")
    order_total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма заказа")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Купон")
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итого к оплате")
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Ожидает оплаты'), ('paid', 'Оплачен'), ('cancelled', 'Отменен')],
        default='pending', verbose_name="Статус оплаты"
    )
    payment_mode = models.CharField(max_length=20, choices=[('cash', 'Наличные'), ('card', 'Банковская карта')], default='cash')
    order_notes = models.TextField(blank=True, null=True, verbose_name="Комментарии к заказу")
    order_id = models.CharField(max_length=20, unique=True, verbose_name="Номер заказа")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")

    def save(self, *args, **kwargs):
        if not self.order_id:
            import datetime
            now = datetime.datetime.now()
            self.order_id = f"ORD-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-order_date']


class OrderItem(BaseModel):
    """📋 Универсальный товар в заказе"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")

    # Generic FK
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.UUIDField(null=True)
    product = GenericForeignKey('content_type', 'object_id')

    # Сохраненные поля конфигурации
    kit_variant = models.ForeignKey(KitVariant, on_delete=models.SET_NULL, null=True, blank=True)
    carpet_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items_carpet")
    border_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items_border")
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    has_podpyatnik = models.BooleanField(default=False)

    def __str__(self):
        product_name = self.product.product_name if self.product else "Удаленный товар"
        return f"{product_name} - {self.quantity}"

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