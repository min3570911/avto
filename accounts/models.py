# 📁 accounts/models.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с Generic FK
# 🛒 Универсальная корзина для автомобилей И лодок
# ✅ ФИКС: Правильные типы полей и ссылки на модели

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
from base.models import BaseModel
import os
import uuid


class Profile(BaseModel):
    """👤 Профиль пользователя"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    is_email_verified = models.BooleanField(
        default=False,
        verbose_name="Email подтвержден"
    )

    email_token = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Токен подтверждения"
    )

    profile_image = models.ImageField(
        upload_to='profile',
        null=True,
        blank=True,
        verbose_name="Фото профиля"
    )

    bio = models.TextField(
        null=True,
        blank=True,
        verbose_name="О себе"
    )

    def __str__(self):
        return self.user.username

    def get_cart_count(self):
        """📊 Количество товаров в корзине"""
        return CartItem.objects.filter(
            cart__is_paid=False,
            cart__user=self.user
        ).count()

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class Cart(BaseModel):
    """🛒 Корзина (поддерживает анонимных пользователей)"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cart",
        null=True,
        blank=True,
        verbose_name="Пользователь"
    )

    session_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="ID сессии",
        help_text="Для анонимных пользователей"
    )

    # ✅ ИСПРАВЛЕНО: Правильная ссылка на Coupon
    coupon = models.ForeignKey(
        'products.Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Купон"
    )

    is_paid = models.BooleanField(
        default=False,
        verbose_name="Оплачен"
    )

    def get_cart_total(self):
        """💰 Общая стоимость корзины"""
        total_price = 0
        for cart_item in self.cart_items.all():
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
        """🛒 Получить или создать анонимную корзину"""
        if not request.session.session_key:
            request.session.create()

        cart, created = cls.objects.get_or_create(
            session_id=request.session.session_key,
            is_paid=False,
            defaults={'user': None}
        )

        return cart

    def __str__(self):
        if self.user:
            return f"Корзина {self.user.username}"
        return f"Анонимная корзина {self.session_id[:8]}..."

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"


class CartItem(BaseModel):
    """
    📦 Универсальный товар в корзине через Generic FK

    Может содержать products.Product ИЛИ boats.BoatProduct
    ИЛИ любые будущие типы товаров
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="Корзина"
    )

    # 🔗 Generic FK - может ссылаться на ЛЮБУЮ модель товара
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Тип товара",
        help_text="Автоматически определяется (автомобиль/лодка)"
    )

    # ✅ ИСПРАВЛЕНО: UUIDField для совместимости с UUID primary keys
    object_id = models.UUIDField(
        verbose_name="ID товара",
        help_text="Автоматически определяется"
    )

    # 🎯 Главное поле - ссылка на товар любого типа
    product = GenericForeignKey('content_type', 'object_id')

    # 📊 Количество
    quantity = models.IntegerField(
        default=1,
        verbose_name="Количество"
    )

    # 🎨 Конфигурация товара
    # ✅ ИСПРАВЛЕНО: Правильная ссылка на модель Color
    carpet_color = models.ForeignKey(
        'products.Color',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cart_items_carpet",
        verbose_name="Цвет коврика",
        limit_choices_to={'color_type': 'carpet'}
    )

    border_color = models.ForeignKey(
        'products.Color',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cart_items_border",
        verbose_name="Цвет окантовки",
        limit_choices_to={'color_type': 'border'}
    )

    # 📦 Комплектация (только для автомобилей)
    kit_variant = models.ForeignKey(
        'products.KitVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Комплектация",
        help_text="Применимо только к автомобильным коврикам"
    )

    # 🦶 Подпятник (только для автомобилей)
    has_podpyatnik = models.BooleanField(
        default=False,
        verbose_name="С подпятником",
        help_text="Применимо только к автомобильным коврикам"
    )

    def get_product_name(self):
        """🏷️ Название товара любого типа"""
        if self.product:
            return self.product.product_name
        return "Удаленный товар"

    def get_product_type(self):
        """🔍 Тип товара"""
        if self.content_type:
            app_label = self.content_type.app_label
            if app_label == 'products':
                return '🚗 Автомобиль'
            elif app_label == 'boats':
                return '🛥️ Лодка'
        return '❓ Неизвестно'

    def is_car_product(self):
        """🚗 Проверка что это автомобильный товар"""
        return self.content_type and self.content_type.app_label == 'products'

    def is_boat_product(self):
        """🛥️ Проверка что это лодочный товар"""
        return self.content_type and self.content_type.app_label == 'boats'

    def get_product_dimensions(self):
        """📏 Размеры товара (для лодок)"""
        if self.is_boat_product() and self.product:
            if hasattr(self.product, 'boat_mat_length') and hasattr(self.product, 'boat_mat_width'):
                if self.product.boat_mat_length and self.product.boat_mat_width:
                    return f"{self.product.boat_mat_length}×{self.product.boat_mat_width} см"
        return None

    def get_product_image(self):
        """🖼️ Получение изображения товара любого типа"""
        if not self.product:
            return None

        if self.is_boat_product():
            # 🛥️ Для лодочных товаров используем images
            if hasattr(self.product, 'images') and self.product.images.exists():
                return self.product.images.first()
            return None
        else:
            # 🚗 Для автомобильных товаров используем product_images
            if hasattr(self.product, 'product_images') and self.product.product_images.exists():
                return self.product.product_images.first()
            return None

    def get_product_image_url(self):
        """🖼️ URL изображения товара"""
        image = self.get_product_image()
        if image and hasattr(image, 'image') and image.image:
            return image.image.url
        return None

    def get_product_url(self):
        """🔗 URL страницы товара"""
        if not self.product or not hasattr(self.product, 'slug'):
            return "#"

        if self.is_boat_product():
            # 🛥️ URL лодочного товара
            return f"/boats/product/{self.product.slug}/"
        else:
            # 🚗 URL автомобильного товара
            return f"/products/{self.product.slug}/"

    def get_product_price(self):
        """💰 Расчет стоимости товара с учетом типа и конфигурации"""
        if not self.product:
            return 0

        base_price = float(self.product.price or 0)
        total_price = base_price * self.quantity

        # 🚗 Логика для автомобилей
        if self.is_car_product():
            # Добавляем стоимость комплектации
            if self.kit_variant and hasattr(self.kit_variant, 'price_modifier'):
                kit_price = float(self.kit_variant.price_modifier or 0)
                total_price += kit_price * self.quantity

            # Добавляем стоимость подпятника
            if self.has_podpyatnik:
                # 🔍 Ищем подпятник в KitVariant как опцию
                try:
                    from products.models import KitVariant
                    podpyatnik_option = KitVariant.objects.filter(
                        code='podpyatnik', is_option=True
                    ).first()
                    if podpyatnik_option:
                        podpyatnik_price = float(podpyatnik_option.price_modifier or 0)
                        total_price += podpyatnik_price * self.quantity
                except:
                    # Fallback цена подпятника
                    total_price += 500 * self.quantity

        # 🛥️ Логика для лодок (только базовая цена)
        elif self.is_boat_product():
            # Для лодок только базовая цена * количество
            pass

        return total_price

    def get_configuration_summary(self):
        """📋 Описание конфигурации товара"""
        parts = []

        # Цвета (для всех типов)
        if self.carpet_color:
            parts.append(f"Коврик: {self.carpet_color.name}")

        if self.border_color:
            parts.append(f"Окантовка: {self.border_color.name}")

        # Специфичные поля для автомобилей
        if self.is_car_product():
            if self.kit_variant:
                parts.append(f"Комплект: {self.kit_variant.name}")

            if self.has_podpyatnik:
                parts.append("С подпятником")

        # Специфичные поля для лодок
        elif self.is_boat_product():
            dimensions = self.get_product_dimensions()
            if dimensions:
                parts.append(f"Размер: {dimensions}")

        return " | ".join(parts) if parts else "Базовая конфигурация"

    def __str__(self):
        product_name = self.get_product_name()
        product_type = self.get_product_type()
        config = self.get_configuration_summary()
        return f"🛒 {product_type} {product_name} - {config} (×{self.quantity})"

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        # ⚠️ УБРАНО: unique_together может вызвать проблемы с миграциями
        # При необходимости добавим индексы отдельно


class Order(BaseModel):
    """📋 Заказ - ПОЛНАЯ версия со всеми полями"""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Пользователь"
    )

    # 📞 Контактные данные клиента
    customer_name = models.CharField(
        max_length=100,
        verbose_name="Имя клиента"
    )
    customer_phone = models.CharField(
        max_length=20,
        verbose_name="Контактный телефон"
    )
    customer_email = models.EmailField(
        verbose_name="Email клиента"
    )
    customer_city = models.CharField(
        max_length=100,
        verbose_name="Город клиента"
    )

    # 🚚 Доставка
    delivery_method = models.CharField(
        max_length=20,
        choices=[
            ('pickup', 'Самовывоз'),
            ('europochta', 'Европочта по Беларуси'),
            ('belpochta', 'Белпочта по Беларуси'),
            ('yandex', 'Яндекс курьер по Минску'),
        ],
        default='pickup',
        verbose_name="Способ доставки"
    )

    shipping_address = models.TextField(
        blank=True,
        null=True,
        verbose_name="Адрес доставки"
    )

    tracking_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Код отслеживания"
    )

    # 💰 Стоимость
    order_total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Стоимость товаров"
    )

    coupon = models.ForeignKey(
        'products.Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Купон"
    )

    grand_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Итого к оплате"
    )

    # 🔄 Статусы
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидает оплаты'),
            ('paid', 'Оплачен'),
            ('cancelled', 'Отменен'),
        ],
        default='pending',
        verbose_name="Статус оплаты"
    )

    payment_mode = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Наличные'),
            ('card', 'Банковская карта')
        ],
        default='cash',
        verbose_name="Способ оплаты"
    )

    # 📝 Дополнительная информация
    order_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Комментарии к заказу"
    )

    order_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Номер заказа"
    )

    order_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата заказа"
    )

    def save(self, *args, **kwargs):
        """💾 Автоматическая генерация номера заказа"""
        if not self.order_id:
            import datetime
            now = datetime.datetime.now()
            self.order_id = f"ORD-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"📋 Заказ {self.order_id} - {self.customer_name}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-order_date']


class OrderItem(BaseModel):
    """📦 Товар в заказе с Generic FK"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="Заказ"
    )

    # 🔗 Generic FK - может ссылаться на ЛЮБУЮ модель товара
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Тип товара"
    )

    # ✅ ИСПРАВЛЕНО: UUIDField для совместимости
    object_id = models.UUIDField(
        verbose_name="ID товара"
    )

    # 🎯 Главное поле - ссылка на товар любого типа
    product = GenericForeignKey('content_type', 'object_id')

    # 📊 Данные на момент заказа
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )

    product_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        verbose_name="Цена товара",
        help_text="Цена на момент заказа"
    )

    # Конфигурация (копируется из CartItem)
    # ✅ ИСПРАВЛЕНО: Правильные ссылки на модели
    carpet_color = models.ForeignKey(
        'products.Color',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items_carpet",
        verbose_name="Цвет коврика"
    )

    border_color = models.ForeignKey(
        'products.Color',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items_border",
        verbose_name="Цвет окантовки"
    )

    kit_variant = models.ForeignKey(
        'products.KitVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Комплектация"
    )

    has_podpyatnik = models.BooleanField(
        default=False,
        verbose_name="С подпятником"
    )

    def get_product_name(self):
        """🏷️ Название товара"""
        if self.product:
            return self.product.product_name
        return "Удаленный товар"

    def get_total_price(self):
        """💰 Общая стоимость позиции"""
        if self.product_price:
            return float(self.product_price) * self.quantity
        return 0

    def __str__(self):
        product_name = self.get_product_name()
        return f"📦 {product_name} - {self.quantity} шт."

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"