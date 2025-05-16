from django.db import models
from base.models import BaseModel
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.contrib.auth.models import User


# Create your models here.

class Category(BaseModel):
    category_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    category_image = models.ImageField(upload_to="catgories")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.category_name


class ColorVariant(BaseModel):
    color_name = models.CharField(max_length=100)
    price = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.color_name


class KitVariant(BaseModel):
    name = models.CharField(max_length=100, verbose_name="Название комплектации")
    code = models.CharField(max_length=50, unique=True, verbose_name="Символьный код")
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Модификатор цены")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    image = models.ImageField(upload_to='configurations', null=True, blank=True, verbose_name="Изображение схемы")

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Тип комплектации"
        verbose_name_plural = "Типы комплектаций"


class Product(BaseModel):
    parent = models.ForeignKey(
        'self', related_name='variants', on_delete=models.CASCADE, blank=True, null=True)
    product_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    price = models.IntegerField()
    product_desription = models.TextField()
    color_variant = models.ManyToManyField(ColorVariant, blank=True)
    # Убираем связь с kit_variant
    newest_product = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.product_name

    def get_product_price_by_kit(self, kit_code):
        # Получаем комплектацию из справочника
        kit = KitVariant.objects.filter(code=kit_code).first()
        if kit:
            return self.price + float(kit.price_modifier)
        return self.price

    def get_rating(self):
        total = sum(int(review['stars']) for review in self.reviews.values())

        if self.reviews.count() > 0:
            return total / self.reviews.count()
        else:
            return 0


class ProductImage(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to='product')

    def img_preview(self):
        return mark_safe(f'<img src="{self.image.url}" width="500"/>')


class Coupon(BaseModel):
    coupon_code = models.CharField(max_length=10)
    is_expired = models.BooleanField(default=False)
    discount_amount = models.IntegerField(default=100)
    minimum_amount = models.IntegerField(default=500)


class ProductReview(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    stars = models.IntegerField(default=3, choices=[(i, i) for i in range(1, 6)])
    content = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="liked_reviews", blank=True)
    dislikes = models.ManyToManyField(User, related_name="disliked_reviews", blank=True)

    def like_count(self):
        return self.likes.count()

    def dislike_count(self):
        return self.dislikes.count()


class Color(BaseModel):
    """Модель для хранения доступных цветов ковриков и окантовки"""
    name = models.CharField(max_length=50, verbose_name="Название цвета")
    hex_code = models.CharField(max_length=7, verbose_name="HEX-код")
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок отображения")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Цвет"
        verbose_name_plural = "Цвета"


class Wishlist(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    kit_variant = models.ForeignKey(KitVariant, on_delete=models.SET_NULL, null=True,
                                    blank=True, related_name="wishlist_items")
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'kit_variant')

    def __str__(self) -> str:
        return f'{self.user.username} - {self.product.product_name} - {self.kit_variant.name if self.kit_variant else "No Kit"}'