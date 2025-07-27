# 📁 boats/admin.py - ПОЛНАЯ АДМИНКА С EXCEL ИМПОРТОМ ДЛЯ ЛОДОК
# 🛥️ Админка с Excel импортом по образу и подобию products
# ✅ АДАПТИРОВАНО: Импорт размеров boat_mat_length, boat_mat_width

import os
import logging
from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from django.urls import path
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import BoatCategory, BoatProduct, BoatProductImage

logger = logging.getLogger(__name__)


class BoatExcelImportForm(forms.Form):
    """
    📊 Форма импорта Excel для лодок (по образу products)

    ФОРМАТ ДЛЯ ЛОДОК (адаптированный):
    A - Категория (1.Yamaha) или SKU товара (BOAT001)
    B - Название товара/категории
    C - Длина коврика (см) - ТОЛЬКО ДЛЯ ЛОДОК
    D - Ширина коврика (см) - ТОЛЬКО ДЛЯ ЛОДОК
    E - Цена
    F - Описание
    G - Meta-описание
    H - Изображение
    """

    excel_file = forms.FileField(
        label="📊 Excel файл с данными лодок",
        help_text="Формат: .xlsx, .xls. По образу импорта products, но для лодок с размерами",
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control-file'
        })
    )

    images_zip = forms.FileField(
        label="🖼️ ZIP архив с изображениями",
        required=False,
        help_text="Необязательно. ZIP файл с изображениями лодок (PNG, JPG, WEBP)",
        widget=forms.FileInput(attrs={
            'accept': '.zip',
            'class': 'form-control-file'
        })
    )


class BoatProductImageInline(admin.TabularInline):
    """🖼️ Inline для управления изображениями лодочных товаров"""
    model = BoatProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_main', 'display_order']
    readonly_fields = ['created_at']

    def get_extra(self, request, obj=None, **kwargs):
        """Показывать пустую форму только для новых товаров"""
        return 1 if obj is None else 0


@admin.register(BoatCategory)
class BoatCategoryAdmin(admin.ModelAdmin):
    """🛥️ Админка категорий лодок"""

    list_display = [
        'category_name',
        'get_products_count',
        'is_active',
        'display_order',
        'created_at'
    ]

    list_filter = [
        'is_active',
        'created_at'
    ]

    search_fields = [
        'category_name',
        'description',
        'meta_title'
    ]

    prepopulated_fields = {
        'slug': ('category_name',)
    }

    fieldsets = (
        ('🏷️ Основная информация', {
            'fields': ('category_name', 'slug', 'category_image')
        }),
        ('📝 Описания (заполняется через редактор)', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('🔍 SEO настройки', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('⚙️ Управление', {
            'fields': ('is_active', 'display_order'),
            'classes': ('collapse',)
        })
    )

    # 🎨 Кастомные методы для отображения
    def get_products_count(self, obj):
        """📊 Количество товаров в категории"""
        count = obj.get_products_count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">📦 {}</span>',
                count
            )
        return format_html('<span style="color: gray;">пусто</span>')

    get_products_count.short_description = "Товаров"


@admin.register(BoatProduct)
class BoatProductAdmin(admin.ModelAdmin):
    """🛥️ Админка товаров лодок с Excel импортом (по образу products)"""

    # 🔗 Подключаем изображения
    inlines = [BoatProductImageInline]

    # 📊 Шаблон с кнопкой импорта
    change_list_template = "admin/boats/import_boats.html"

    list_display = [
        'product_name',
        'category',
        'get_dimensions_badge',
        'get_price_display',
        'is_active',
        'newest_product',
        'stock_quantity',
        'created_at'
    ]

    list_filter = [
        'category',
        'is_active',
        'newest_product',
        'is_featured',
        'created_at'
    ]

    search_fields = [
        'product_name',
        'sku',
        'description',
        'short_description'
    ]

    prepopulated_fields = {
        'slug': ('product_name',)
    }

    readonly_fields = [
        'sku',  # Автогенерируется
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('🏷️ Основная информация', {
            'fields': (
                'product_name',
                'slug',
                'category',
                'sku',
                'price'
            )
        }),
        ('📐 Размеры лодочного коврика', {
            'fields': ('boat_mat_length', 'boat_mat_width'),
            'description': '🛥️ УНИКАЛЬНЫЕ ПОЛЯ ДЛЯ ЛОДОК: Укажите размеры коврика в сантиметрах'
        }),
        ('📝 Описания (заполняется через редактор)', {
            'fields': ('short_description', 'description'),
            'classes': ('wide',)
        }),
        ('🔍 SEO настройки', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('📦 Складские данные', {
            'fields': ('stock_quantity', 'weight'),
            'classes': ('collapse',)
        }),
        ('⚙️ Управление товаром', {
            'fields': (
                'is_active',
                'is_featured',
                'newest_product'
            ),
            'classes': ('collapse',)
        })
    )

    # 🎨 Кастомные методы для отображения
    def get_dimensions_badge(self, obj):
        """📐 Красивый значок с размерами"""
        dimensions = obj.get_mat_dimensions()
        if 'Размеры уточняйте' in dimensions:
            return format_html(
                '<span style="color: orange;">⚠️ Не указаны</span>'
            )
        return format_html(
            '<span style="background: #e3f2fd; padding: 2px 6px; border-radius: 3px; font-weight: bold;">📏 {}</span>',
            dimensions
        )

    get_dimensions_badge.short_description = "Размеры коврика"

    def get_price_display(self, obj):
        """💰 Отформатированная цена"""
        if obj.price > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">💰 {} руб.</span>',
                obj.get_display_price()
            )
        return format_html('<span style="color: gray;">Не указана</span>')

    get_price_display.short_description = "Цена"

    # 📊 Дополнительные URL для импорта
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-boats/',
                self.admin_site.admin_view(self.import_boats_view),
                name='boats_boatproduct_import'
            ),
        ]
        return custom_urls + urls

    def import_boats_view(self, request):
        """📊 Обработка импорта Excel для лодок (по образу products)"""
        if request.method == 'POST':
            form = BoatExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                return self._process_boats_import(request, form)
        else:
            form = BoatExcelImportForm()

        context = {
            'form': form,
            'title': '📊 Импорт лодок из Excel',
            'subtitle': 'Загрузка категорий и товаров лодок по образу products',
            'import_help': self._get_boats_import_help(),
            'opts': self.model._meta,  # Для breadcrumbs
        }

        return render(request, 'admin/boats/import_boats.html', context)

    def _process_boats_import(self, request, form):
        """🔄 Обработка загруженного Excel файла с лодками"""
        try:
            excel_file = request.FILES['excel_file']
            images_zip = request.FILES.get('images_zip')

            # 📊 Процессинг Excel файла для лодок
            result = self._process_boats_excel(excel_file)

            if result['success']:
                success_msg = f"✅ Импорт лодок завершен! Создано: {result['categories']} категорий, {result['products']} товаров"
                messages.success(request, success_msg)

                if result['errors']:
                    error_msg = f"⚠️ Предупреждения: {len(result['errors'])} строк с ошибками"
                    messages.warning(request, error_msg)
            else:
                messages.error(request, f"❌ Ошибка импорта: {result['error']}")

            # 🖼️ Обработка изображений (если загружены)
            if images_zip:
                img_result = self._process_boats_images(images_zip)
                if img_result['success']:
                    messages.info(request, f"📷 Обработано изображений: {img_result['processed']}")
                else:
                    messages.warning(request, f"⚠️ Ошибка изображений: {img_result['error']}")

        except Exception as e:
            logger.error(f"Ошибка импорта лодок: {e}")
            messages.error(request, f"❌ Критическая ошибка импорта: {str(e)}")

        return HttpResponseRedirect('../')

    def _process_boats_excel(self, excel_file):
        """📊 Обработка Excel файла для лодок (адаптировано с products)"""
        import openpyxl

        result = {
            'success': False,
            'categories': 0,
            'products': 0,
            'errors': []
        }

        try:
            # 📖 Читаем Excel файл
            workbook = openpyxl.load_workbook(excel_file)
            worksheet = workbook.active

            current_category = None
            row_num = 1

            for row in worksheet.iter_rows(min_row=2, values_only=True):  # Пропускаем заголовок
                row_num += 1

                if not any(row):  # Пропускаем пустые строки
                    continue

                try:
                    identifier = str(row[0]).strip() if row[0] else ""
                    name = str(row[1]).strip() if row[1] else ""
                    length = row[2] if row[2] else None  # Длина коврика
                    width = row[3] if row[3] else None  # Ширина коврика
                    price = row[4] if row[4] else 0
                    description = str(row[5]).strip() if row[5] else ""
                    meta_description = str(row[6]).strip() if row[6] else ""
                    image_name = str(row[7]).strip() if row[7] else ""

                    # 📂 Определяем тип строки (категория или товар)
                    if '.' in identifier and not identifier.replace('.', '').isdigit():
                        # КАТЕГОРИЯ: формат "1.Yamaha"
                        category_name = name

                        category, created = BoatCategory.objects.get_or_create(
                            category_name=category_name,
                            defaults={
                                'description': description,
                                'meta_title': name,
                                'meta_description': meta_description,
                                'is_active': True,
                                'display_order': 0
                            }
                        )

                        current_category = category
                        if created:
                            result['categories'] += 1
                            logger.info(f"Создана категория лодок: {category_name}")

                    else:
                        # ТОВАР ЛОДКИ
                        if not current_category:
                            result['errors'].append(f"Строка {row_num}: Товар без категории")
                            continue

                        # 🛥️ Создаем товар лодки с размерами
                        product, created = BoatProduct.objects.get_or_create(
                            product_name=name,
                            category=current_category,
                            defaults={
                                'price': float(price) if price else 0,
                                'boat_mat_length': int(length) if length else None,  # 🆕 Длина
                                'boat_mat_width': int(width) if width else None,  # 🆕 Ширина
                                'description': description,
                                'meta_title': name,
                                'meta_description': meta_description,
                                'is_active': True,
                                'newest_product': False
                            }
                        )

                        if created:
                            result['products'] += 1
                            dimensions = product.get_mat_dimensions()
                            logger.info(f"Создан товар лодки: {name} ({dimensions})")

                except Exception as e:
                    error_msg = f"Строка {row_num}: {str(e)}"
                    result['errors'].append(error_msg)
                    logger.error(error_msg)

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Ошибка обработки Excel для лодок: {e}")

        return result

    def _process_boats_images(self, images_zip):
        """🖼️ Обработка ZIP архива с изображениями лодок"""
        import zipfile
        import os
        from django.conf import settings

        result = {'success': False, 'processed': 0, 'error': ''}

        try:
            with zipfile.ZipFile(images_zip, 'r') as zip_ref:
                for filename in zip_ref.namelist():
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        # Сохраняем изображение в папку boat_products
                        target_path = os.path.join(settings.MEDIA_ROOT, 'boat_products', os.path.basename(filename))

                        os.makedirs(os.path.dirname(target_path), exist_ok=True)

                        with zip_ref.open(filename) as source, open(target_path, 'wb') as target:
                            target.write(source.read())

                        result['processed'] += 1

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Ошибка обработки изображений лодок: {e}")

        return result

    def _get_boats_import_help(self):
        """📋 Справка по формату импорта лодок"""
        return {
            'columns': [
                ('A', 'Категория/SKU', '1.Yamaha или BOAT001'),
                ('B', 'Название', 'Коврик EVA Yamaha F150'),
                ('C', 'Длина (см)', '120'),
                ('D', 'Ширина (см)', '80'),
                ('E', 'Цена', '4500.00'),
                ('F', 'Описание', 'Подробное описание товара'),
                ('G', 'Meta-описание', 'SEO описание'),
                ('H', 'Изображение', 'yamaha_f150.jpg')
            ],
            'examples': [
                ('1.Yamaha', 'Лодочные моторы Yamaha', '', '', '', 'Описание категории', 'SEO категории', 'yamaha.jpg'),
                ('BOAT001', 'Коврик EVA Yamaha F150', '120', '80', '4500', 'Качественный коврик...', 'SEO товара',
                 'yamaha_f150.jpg')
            ]
        }


@admin.register(BoatProductImage)
class BoatProductImageAdmin(admin.ModelAdmin):
    """🖼️ Админка изображений лодочных товаров"""

    list_display = [
        'get_image_preview',
        'product',
        'alt_text',
        'is_main',
        'display_order',
        'created_at'
    ]

    list_filter = [
        'is_main',
        'product__category',
        'created_at'
    ]

    search_fields = [
        'product__product_name',
        'alt_text'
    ]

    list_editable = [
        'is_main',
        'display_order'
    ]

    def get_image_preview(self, obj):
        """🖼️ Превью изображения в списке"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "Нет изображения"

    get_image_preview.short_description = "Превью"


# 🔧 НАСТРОЙКИ АДМИНКИ
admin.site.site_header = "🛥️ Админ-панель лодочных ковриков"
admin.site.site_title = "Boats Admin"
admin.site.index_title = "Управление лодочными товарами"

# 📝 КОММЕНТАРИИ:
#
# ✅ СОЗДАНА ПОЛНАЯ АДМИНКА ПО ОБРАЗУ PRODUCTS:
# 1. BoatCategoryAdmin - управление категориями лодок
# 2. BoatProductAdmin - управление товарами лодок + Excel импорт
# 3. BoatProductImageAdmin - управление изображениями
#
# 🛥️ АДАПТИРОВАНО ДЛЯ ЛОДОК:
# • Поддержка размеров boat_mat_length, boat_mat_width
# • Специальный формат Excel импорта с размерами
# • Красивые значки и отображение размеров
# • Интеграция с CKEditor5 для описаний
# • Обработка ZIP архивов с изображениями
#
# 📊 ФОРМАТ EXCEL ДЛЯ ЛОДОК:
# A - Категория (1.Yamaha) или SKU (BOAT001)
# B - Название товара/категории
# C - Длина коврика (см) - НОВОЕ ПОЛЕ
# D - Ширина коврика (см) - НОВОЕ ПОЛЕ
# E - Цена
# F - Описание
# G - Meta-описание
# H - Изображение
#
# 🎯 СЛЕДУЮЩИЕ ШАГИ:
# 1. Создать шаблон admin/boats/import_boats.html
# 2. Создать миграции boats
# 3. Обновить boats/views.py под отдельные модели
# 4. Протестировать Excel импорт