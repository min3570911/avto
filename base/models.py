from django.db import models
import uuid


from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django_ckeditor_5.fields import CKEditor5Field


class BaseModel(models.Model):
    uid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class BaseProduct(BaseModel):
    """🔧 Абстрактная модель товара - общие поля"""
    product_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    price = models.IntegerField()
    product_desription = CKEditor5Field()
    newest_product = models.BooleanField(default=False)
    product_sku = models.CharField(max_length=50, unique=True)
    page_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        abstract = True  # ✅ Не создает таблицу!
