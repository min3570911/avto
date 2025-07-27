# 📁 boats/admin.py - ИСПРАВЛЕННАЯ АДМИНКА ДЛЯ ЛОДОК
# 🛥️ Админка с нормальным списком товаров + кнопка импорта в углу
# ✅ ИСПРАВЛЕНО: Убран change_list_template, добавлена кнопка импорта

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
    """📊 Форма импорта Excel для лодок"""

    excel_file = forms.FileField(
        label="📊 Excel файл с данными лодок",
        help_text="Формат: .xlsx, .xls. Колонки: A-Категория/SKU, B-Название, C-Длина(см), D-Ширина(см), E-Цена",
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control-file'
        })
    )

    images_zip = forms.FileField(
        label="🖼️ ZIP архив с изображениями",
        required=False,
        help_text="Необязательно. ZIP файл с изображениями лодок",
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
    """🛥️ Админка товаров лодок с кнопкой импорта"""

    # 🔗 Подключаем изображения
    inlines = [BoatProductImageInline]

    # ✅ ИСПРАВЛЕНО: Используем кастомный change_list с кнопкой импорта
    change_list_template = "admin/boats/boatproduct/change_list.html"

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
        """📊 Обработка импорта Excel для лодок"""
        if request.method == 'POST':
            form = BoatExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                return self._process_boats_import(request, form)
        else:
            form = BoatExcelImportForm()

        context = {
            'form': form,
            'title': '📊 Импорт лодок из Excel',
            'subtitle': 'Загрузка категорий и товаров лодок',
            'opts': self.model._meta,  # Для breadcrumbs
            'app_label': self.model._meta.app_label,  # 🔧 ИСПРАВЛЕНО: Добавляем app_label
            'has_change_permission': True,
            'has_view_permission': True,
        }

        return render(request, 'admin/boats/import_boats.html', context)

    def _process_boats_import(self, request, form):
        """🔄 Обработка загруженного Excel файла с лодками"""
        try:
            excel_file = request.FILES['excel_file']
            images_zip = request.FILES.get('images_zip')

            # 📊 Простая обработка Excel (базовая версия)
            result = self._process_boats_excel(excel_file)

            if result['success']:
                success_msg = f"✅ Импорт лодок завершен! Создано: {result['categories']} категорий, {result['products']} товаров"
                messages.success(request, success_msg)
            else:
                messages.error(request, f"❌ Ошибка импорта: {result['error']}")

        except Exception as e:
            logger.error(f"Ошибка импорта лодок: {e}")
            messages.error(request, f"❌ Критическая ошибка импорта: {str(e)}")

        return HttpResponseRedirect('../')

    def _process_boats_excel(self, excel_file):
        """📊 Базовая обработка Excel файла для лодок"""
        import openpyxl

        result = {
            'success': False,
            'categories': 0,
            'products': 0,
            'error': ''
        }

        try:
            # 📖 Читаем Excel файл
            workbook = openpyxl.load_workbook(excel_file)
            worksheet = workbook.active

            current_category = None

            for row in worksheet.iter_rows(min_row=2, values_only=True):  # Пропускаем заголовок
                if not any(row):  # Пропускаем пустые строки
                    continue

                identifier = str(row[0]).strip() if row[0] else ""
                name = str(row[1]).strip() if row[1] else ""
                length = row[2] if row[2] else None  # Длина коврика
                width = row[3] if row[3] else None  # Ширина коврика
                price = row[4] if row[4] else 0
                description = str(row[5]).strip() if row[5] else ""

                # 📂 Определяем тип строки (категория или товар)
                if '.' in identifier and not identifier.replace('.', '').isdigit():
                    # КАТЕГОРИЯ: формат "1.Yamaha"
                    category_name = name

                    category, created = BoatCategory.objects.get_or_create(
                        category_name=category_name,
                        defaults={
                            'description': description,
                            'is_active': True,
                            'display_order': 0
                        }
                    )

                    current_category = category
                    if created:
                        result['categories'] += 1

                else:
                    # ТОВАР ЛОДКИ
                    if not current_category:
                        continue

                    # 🛥️ Создаем товар лодки с размерами
                    product, created = BoatProduct.objects.get_or_create(
                        product_name=name,
                        category=current_category,
                        defaults={
                            'price': float(price) if price else 0,
                            'boat_mat_length': int(length) if length else None,
                            'boat_mat_width': int(width) if width else None,
                            'description': description,
                            'is_active': True
                        }
                    )

                    if created:
                        result['products'] += 1

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result


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

# 📝 КОММЕНТАРИИ:
#
# ✅ ИСПРАВЛЕНА ПРОБЛЕМА:
# • change_list_template теперь указывает на правильный шаблон
# • Шаблон наследует стандартный список и добавляет кнопку импорта
# • При заходе в "Товары лодок" показывается нормальный список
# • Кнопка "Импорт" в правом верхнем углу
#
# 🛥️ ФУНКЦИОНАЛЬНОСТЬ:
# • Обычный список товаров лодок
# • Кнопка импорта в header
# • Excel импорт с размерами лодок
# • Inline редактирование изображений
#
# 🎯 СЛЕДУЮЩИЙ ШАГ:
# Создать шаблон templates/admin/boats/boatproduct/change_list.html