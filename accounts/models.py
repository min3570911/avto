# 📁 accounts/models.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
# 🛥️ ДОБАВЛЕНО: Методы для отображения размеров лодок в корзине
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
        """💰 ИСПРАВЛЕННЫЙ: Рассчитать стоимость товара БЕЗ хардкода цен"""

        if not self.product:
            return 0

        # 🛥️ ЛОГИКА ДЛЯ ЛОДОК
        if self.product.is_boat_product():
            # Для лодок используем цену напрямую (без комплектаций и подпятника)
            base_price = float(self.product.price or 0)

        # 🚗 ЛОГИКА ДЛЯ АВТОМОБИЛЕЙ
        else:
            # ✅ Получаем ИТОГОВУЮ цену комплектации
            if self.kit_variant:
                base_price = float(self.product.get_product_price_by_kit(self.kit_variant.code))
            else:
                # Если комплектация не выбрана, используем цену салона по умолчанию
                base_price = float(self.product.get_product_price_by_kit('salon'))

            # 🦶 ПРАВИЛЬНАЯ обработка подпятника БЕЗ хардкода
            if self.has_podpyatnik:
                # Импортируем здесь чтобы избежать циклических импортов
                from products.models import KitVariant

                podpyatnik_option = KitVariant.objects.filter(
                    code='podpyatnik',
                    is_option=True
                ).first()

                if podpyatnik_option:
                    # ✅ Цена из админки
                    base_price += float(podpyatnik_option.price_modifier)
                    print(f"✅ Подпятник: {podpyatnik_option.price_modifier} руб (из админки)")
                else:
                    # 🚨 КРИТИЧЕСКАЯ ОШИБКА: подпятник не настроен в админке!
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(
                        "🚨 ОШИБКА: Опция 'подпятник' не найдена в админке! Создайте KitVariant с code='podpyatnik' и is_option=True")

                    print("❌ ВНИМАНИЕ: Подпятник не добавлен к цене - не настроен в админке!")

                    # 📧 Можно добавить уведомление администратору
                    # send_admin_notification("Подпятник не настроен в админке!")

        # ✖️ Умножаем цену единицы товара на количество
        total_price = base_price * self.quantity

        # 🔍 Отладочная информация
        print(f"🧮 Расчет цены товара '{self.product.product_name}':")
        print(f"   - Базовая цена: {base_price} руб")
        print(f"   - Количество: {self.quantity}")
        print(f"   - Итого: {total_price} руб")

        return total_price

    # 🛥️ НОВЫЕ МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ РАЗМЕРОВ ЛОДОК
    def get_product_dimensions(self):
        """
        📏 Получить размеры коврика для лодок

        Возвращает строку с размерами для лодочных товаров
        или None для автомобильных товаров
        """
        if self.product and self.product.is_boat_product():
            return self.product.get_mat_dimensions()
        return None

    def get_product_description_info(self):
        """
        📝 Полное описание товара в корзине с размерами и опциями

        Возвращает список строк для отображения под названием товара в корзине
        """
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

        # 🦶 Подпятник
        if self.has_podpyatnik:
            info_parts.append("🦶 С подпятником")

        return info_parts

    def get_short_description(self):
        """📝 Краткое описание конфигурации товара (для админки)"""
        parts = []

        # 🛥️ Размеры для лодок
        dimensions = self.get_product_dimensions()
        if dimensions:
            parts.append(f"Размер: {dimensions}")

        # 📦 Комплектация
        if self.kit_variant:
            parts.append(f"Комплект: {self.kit_variant.name}")

        # 🎨 Цвета
        if self.carpet_color:
            parts.append(f"Коврик: {self.carpet_color.name}")
        if self.border_color:
            parts.append(f"Окантовка: {self.border_color.name}")

        # 🦶 Подпятник
        if self.has_podpyatnik:
            parts.append("С подпятником")

        return " | ".join(parts) if parts else "Стандартная конфигурация"

    def __str__(self):
        # 🛥️ УЛУЧШЕННОЕ отображение с размерами для лодок
        product_name = self.product.product_name if self.product else "Удаленный товар"
        dimensions = self.get_product_dimensions()

        if dimensions:
            # Для лодок показываем размеры
            return f"🛥️ {product_name} ({dimensions}) x {self.quantity}"
        else:
            # Для автомобилей обычное отображение
            return f"🚗 {product_name} x {self.quantity}"

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
            ('europochta', 'Европочта'),
            ('belpost', 'Белпочта'),
        ],
        default='pickup',
        verbose_name="Способ доставки"
    )
    shipping_address = models.TextField(
        blank=True,
        null=True,
        verbose_name="Адрес доставки"
    )

    # 💰 Финансовая информация
    order_total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма заказа")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Купон")
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итого к оплате")

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

    # 📝 Дополнительная информация
    order_notes = models.TextField(blank=True, null=True, verbose_name="Комментарии к заказу")
    order_id = models.CharField(max_length=20, unique=True, verbose_name="Номер заказа")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")

    def save(self, *args, **kwargs):
        """💾 Автоматическая генерация номера заказа и заполнение данных"""
        if not self.order_id:
            import datetime
            now = datetime.datetime.now()
            self.order_id = f"ORD-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"

        # 📞 Пытаемся заполнить контактные данные из профиля пользователя
        if self.user and not self.customer_phone:
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