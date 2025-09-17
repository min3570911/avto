# accounts/management/commands/fix_cart.py
# 🔧 Упрощенная команда для быстрого исправления корзины
# ✅ Исправляет Generic FK и пустые slug

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from products.models import Product
from boats.models import BoatProduct
from accounts.models import CartItem, OrderItem


class Command(BaseCommand):
    help = 'Исправление проблем корзины и товаров'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Исправить проблемы')

    def handle(self, *args, **options):
        self.stdout.write('🔧 Исправление корзины...\n')

        # Получаем правильные ContentType
        try:
            product_ct = ContentType.objects.get_for_model(Product)
            boat_ct = ContentType.objects.get_for_model(BoatProduct)
            self.stdout.write(f'✅ Product ContentType: {product_ct.id}')
            self.stdout.write(f'✅ BoatProduct ContentType: {boat_ct.id}')
        except Exception as e:
            self.stderr.write(f'❌ Ошибка ContentType: {e}')
            return

        # Диагностика CartItem
        broken_cart_items = []
        for item in CartItem.objects.all():
            try:
                product = item.product
                if not product or not hasattr(product, 'product_name'):
                    broken_cart_items.append(item)
            except Exception:
                broken_cart_items.append(item)

        # Диагностика OrderItem
        broken_order_items = []
        for item in OrderItem.objects.all():
            try:
                product = item.product
                if not product or not hasattr(product, 'product_name'):
                    broken_order_items.append(item)
            except Exception:
                broken_order_items.append(item)

        self.stdout.write(f'❌ Битых элементов корзины: {len(broken_cart_items)}')
        self.stdout.write(f'❌ Битых элементов заказов: {len(broken_order_items)}')

        # Проверяем пустые slug
        empty_products = Product.objects.filter(Q(slug__isnull=True) | Q(slug=''))
        empty_boats = BoatProduct.objects.filter(Q(slug__isnull=True) | Q(slug=''))

        self.stdout.write(f'❌ Товаров без slug: {empty_products.count()}')
        self.stdout.write(f'❌ Лодок без slug: {empty_boats.count()}')

        if not options['fix']:
            self.stdout.write('\n💡 Для исправления добавьте --fix')
            return

        # Исправляем
        with transaction.atomic():
            cart_fixed = 0
            cart_deleted = 0
            order_fixed = 0
            order_deleted = 0

            # Исправляем CartItem
            for item in broken_cart_items:
                try:
                    # Пробуем найти товар
                    if Product.objects.filter(uid=item.object_id).exists():
                        item.content_type = product_ct
                        item.save()
                        cart_fixed += 1
                    elif BoatProduct.objects.filter(uid=item.object_id).exists():
                        item.content_type = boat_ct
                        item.save()
                        cart_fixed += 1
                    else:
                        item.delete()
                        cart_deleted += 1
                except Exception:
                    item.delete()
                    cart_deleted += 1

            # Исправляем OrderItem
            for item in broken_order_items:
                try:
                    # Пробуем найти товар
                    if Product.objects.filter(uid=item.object_id).exists():
                        item.content_type = product_ct
                        item.save()
                        order_fixed += 1
                    elif BoatProduct.objects.filter(uid=item.object_id).exists():
                        item.content_type = boat_ct
                        item.save()
                        order_fixed += 1
                    else:
                        item.delete()
                        order_deleted += 1
                except Exception:
                    item.delete()
                    order_deleted += 1

            # Исправляем slug
            slugs_fixed = 0
            for product in empty_products:
                slug = slugify(product.product_name) or f'product-{product.uid}'
                counter = 1
                original_slug = slug
                while Product.objects.filter(slug=slug).exclude(uid=product.uid).exists():
                    slug = f'{original_slug}-{counter}'
                    counter += 1
                product.slug = slug
                product.save()
                slugs_fixed += 1

            for boat in empty_boats:
                slug = slugify(boat.product_name) or f'boat-{boat.uid}'
                counter = 1
                original_slug = slug
                while BoatProduct.objects.filter(slug=slug).exclude(uid=boat.uid).exists():
                    slug = f'{original_slug}-{counter}'
                    counter += 1
                boat.slug = slug
                boat.save()
                slugs_fixed += 1

            self.stdout.write(f'\n✅ Корзина - исправлено: {cart_fixed}, удалено: {cart_deleted}')
            self.stdout.write(f'✅ Заказы - исправлено: {order_fixed}, удалено: {order_deleted}')
            self.stdout.write(f'🔗 Slug создано: {slugs_fixed}')

        self.stdout.write(self.style.SUCCESS('\n🎉 Готово! Проверьте корзину и админку.'))