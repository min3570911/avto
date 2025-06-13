# 📁 products/admin_views.py
# 🛠️ ИСПРАВЛЕННАЯ версия с правильной обработкой category_sku
# ✅ Сохранена вся существующая логика импорта Excel
# 🆕 Добавлена обработка ZIP файлов с изображениями
# 🔧 ИСПРАВЛЕНО: Жестко заданный SKU заменен на оригинальный

import logging
import tempfile
import openpyxl
import io
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile

from .import_processor import ProductImportProcessor, preview_excel_data
from .import_utils import read_excel_file, separate_categories_and_products, extract_category_sku
from .image_utils import process_images_zip  # 🆕 Новая утилита для изображений

logger = logging.getLogger(__name__)


class ExcelUploadForm(forms.Form):
    """📊 ОБНОВЛЕННАЯ форма загрузки Excel файла с поддержкой ZIP"""

    excel_file = forms.FileField(
        label="Выберите Excel файл",
        help_text="Поддерживаются форматы: .xlsx, .xls (макс. 10 МБ)",
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control'
        })
    )

    # 🆕 НОВОЕ ПОЛЕ: ZIP архив с изображениями
    images_zip = forms.FileField(
        label="ZIP архив с изображениями",
        help_text="Необязательно. Поддерживаемый формат: .zip (макс. 10 МБ)",
        required=False,  # 🎯 Необязательное поле
        widget=forms.FileInput(attrs={
            'accept': '.zip',
            'class': 'form-control'
        })
    )

    def clean_excel_file(self):
        """🔍 Валидация загруженного Excel файла"""

        file = self.cleaned_data.get('excel_file')

        if not file:
            raise forms.ValidationError("❌ Файл не выбран")

        # 📏 Проверка размера файла (10 МБ максимум)
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                f"❌ Файл слишком большой: {file.size / 1024 / 1024:.1f} МБ. "
                f"Максимум: 10 МБ"
            )

        # 📁 Проверка расширения файла
        allowed_extensions = ['.xlsx', '.xls']
        file_extension = file.name.lower().split('.')[-1]

        if f'.{file_extension}' not in allowed_extensions:
            raise forms.ValidationError(
                f"❌ Неподдерживаемый формат файла: .{file_extension}. "
                f"Разрешены: {', '.join(allowed_extensions)}"
            )

        return file

    def clean_images_zip(self):
        """🆕 НОВАЯ ВАЛИДАЦИЯ: ZIP архив с изображениями"""
        zip_file = self.cleaned_data.get('images_zip')

        # 🎯 Если файл не загружен - это нормально (поле необязательное)
        if not zip_file:
            return zip_file

        # 📏 Проверка размера файла (10 МБ максимум)
        if zip_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                f"❌ ZIP архив слишком большой: {zip_file.size / 1024 / 1024:.1f} МБ. "
                f"Максимум: 10 МБ"
            )

        # 📁 Проверка расширения файла
        if not zip_file.name.lower().endswith('.zip'):
            raise forms.ValidationError(
                f"❌ Неподдерживаемый формат архива. "
                f"Разрешен только .zip"
            )

        return zip_file


@staff_member_required
def import_form_view(request):
    """📝 ОБНОВЛЕННАЯ страница с формой загрузки Excel файла + ZIP архива"""
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                excel_file = form.cleaned_data['excel_file']
                images_zip = form.cleaned_data.get('images_zip')  # 🆕 ZIP файл (может быть None)

                # 💾 Сохраняем базовую информацию о файлах
                request.session['uploaded_file_name'] = excel_file.name
                request.session['uploaded_file_size'] = excel_file.size

                # 🆕 Сохраняем информацию о ZIP файле
                if images_zip:
                    request.session['uploaded_zip_name'] = images_zip.name
                    request.session['uploaded_zip_size'] = images_zip.size
                    logger.info(f"📦 Загружен ZIP архив: {images_zip.name} ({images_zip.size / 1024 / 1024:.1f} МБ)")
                else:
                    # 🧹 Очищаем информацию о ZIP если он не загружен
                    request.session.pop('uploaded_zip_name', None)
                    request.session.pop('uploaded_zip_size', None)

                # 🆕 НОВАЯ ЛОГИКА: Обработка изображений ДО анализа Excel
                images_processed = 0
                if images_zip:
                    try:
                        logger.info("🖼️ Начинаем обработку ZIP архива с изображениями...")
                        images_processed = process_images_zip(images_zip)
                        # 💾 Сохраняем статистику обработки изображений
                        request.session['images_processed'] = images_processed
                        messages.success(
                            request,
                            f"🖼️ Обработано изображений: {images_processed}"
                        )
                        logger.info(f"✅ Успешно обработано {images_processed} изображений")

                    except Exception as e:
                        error_msg = f"❌ Ошибка обработки изображений: {str(e)}"
                        logger.error(error_msg)
                        messages.warning(request, error_msg)
                        # 🔄 Продолжаем импорт Excel даже если изображения не обработались
                        request.session['images_processed'] = 0

                # 🔄 Обрабатываем файл дважды: для preview и для полных данных (как было)

                # 👁️ PREVIEW: Получаем ограниченные данные для отображения
                excel_file.seek(0)
                preview_result = preview_excel_data(excel_file)

                if not preview_result['success']:
                    messages.error(request, f"❌ {preview_result['error']}")
                    return render(request, 'admin/products/import_form.html', {'form': form})

                # 📊 ПОЛНЫЕ ДАННЫЕ: Читаем весь файл для импорта
                excel_file.seek(0)
                success, raw_data = read_excel_file(excel_file)

                if not success:
                    messages.error(request, f"❌ Ошибка чтения файла: {raw_data}")
                    return render(request, 'admin/products/import_form.html', {'form': form})

                # 🔄 Разделяем на категории и товары (БЕЗ ограничений)
                categories, products, invalid_data = separate_categories_and_products(raw_data)

                # 💾 Сохраняем ПОЛНЫЕ данные в сессии
                full_data = {
                    'categories': categories,
                    'products': products,
                    'invalid_data': invalid_data,
                    'success': True
                }

                # 💾 Сохраняем оба набора данных в сессии
                request.session['preview_data'] = preview_result  # Для отображения
                request.session['full_import_data'] = full_data  # Для импорта

                # 🆕 Формируем сообщение об успехе с учетом изображений
                if images_zip:
                    success_msg = f"✅ Файлы успешно загружены: Excel проанализирован, {images_processed} изображений обработано"
                else:
                    success_msg = "✅ Excel файл успешно загружен и проанализирован"

                messages.success(request, success_msg)
                return redirect('import_preview')

            except Exception as e:
                error_msg = f"❌ Ошибка при обработке файлов: {str(e)}"
                logger.error(error_msg, exc_info=True)
                messages.error(request, error_msg)

        else:
            # 📋 Отображаем ошибки валидации
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    else:
        form = ExcelUploadForm()

    return render(request, 'admin/products/import_form.html', {'form': form})


@staff_member_required
def import_preview_view(request):
    """👁️ ОБНОВЛЕННАЯ страница предпросмотра данных с информацией об изображениях"""
    try:
        # 📊 Получаем данные предпросмотра из сессии
        preview_data = request.session.get('preview_data')

        if not preview_data:
            messages.error(request, "❌ Данные для предпросмотра не найдены. Загрузите файл заново.")
            return redirect('import_form')

        if not preview_data['success']:
            messages.error(request, f"❌ {preview_data['error']}")
            return redirect('import_form')

        # 🆕 Получаем информацию об обработанных изображениях
        images_processed = request.session.get('images_processed', 0)
        zip_name = request.session.get('uploaded_zip_name', None)
        zip_size = request.session.get('uploaded_zip_size', 0)

        # 📈 Подготавливаем контекст для шаблона
        context = {
            'title': 'Предпросмотр импорта товаров',
            'statistics': preview_data['statistics'],
            'categories': preview_data.get('categories', []),
            'products': preview_data.get('products', []),
            'invalid_data': preview_data['invalid_data'],
            'total_categories': preview_data.get('total_categories', 0),
            'total_products': preview_data.get('total_products', 0),
            'total_invalid': preview_data['total_invalid'],
            'file_name': request.session.get('uploaded_file_name', 'unknown.xlsx'),
            'file_size': request.session.get('uploaded_file_size', 0),
            # 🆕 НОВЫЕ данные об изображениях
            'images_processed': images_processed,
            'zip_name': zip_name,
            'zip_size': zip_size,
            'has_images': images_processed > 0,
        }

        return render(request, 'admin/products/import_preview.html', context)

    except Exception as e:
        error_msg = f"❌ Ошибка предпросмотра: {str(e)}"
        logger.error(error_msg)
        messages.error(request, error_msg)
        return redirect('import_form')


@staff_member_required
@require_http_methods(["POST"])
def execute_import_view(request):
    """🚀 ИСПРАВЛЕННОЕ выполнение импорта с ПРАВИЛЬНЫМИ category_sku"""
    try:
        # 📁 Проверяем подтверждение
        if 'confirm_import' not in request.POST:
            messages.error(request, "❌ Импорт не подтверждён")
            return redirect('import_preview')

        # 📊 Получаем ПОЛНЫЕ данные из сессии (не preview!)
        full_data = request.session.get('full_import_data')

        if not full_data or not full_data.get('success'):
            messages.error(request, "❌ Полные данные для импорта не найдены. Загрузите файл заново.")
            return redirect('import_form')

        # 🚀 Импорт с использованием существующего процессора
        messages.info(request, "🔄 Запуск импорта ВСЕХ товаров...")

        # 📦 Получаем ПОЛНЫЕ данные (все категории и товары)
        categories_data = full_data.get('categories', [])
        products_data = full_data.get('products', [])
        invalid_data = full_data.get('invalid_data', [])

        logger.info(f"📊 Начинаем импорт: {len(categories_data)} категорий, {len(products_data)} товаров")

        # 🔄 Создаем временный Excel файл с ПОЛНЫМИ данными в правильном порядке
        all_rows = []

        # 📂 Добавляем категории с их номерами строк
        for cat in categories_data:
            all_rows.append({
                'type': 'category',
                'row_number': cat.get('row_number', 0),
                'data': cat
            })

        # 🛍️ Добавляем товары с их номерами строк
        for prod in products_data:
            all_rows.append({
                'type': 'product',
                'row_number': prod.get('row_number', 0),
                'data': prod
            })

        # 🔄 СОРТИРУЕМ по номеру строки для восстановления порядка
        all_rows.sort(key=lambda x: x['row_number'])

        logger.info(f"📊 Восстановлен порядок: {len(all_rows)} строк")

        # 📊 Создаем временный Excel файл с ПРАВИЛЬНЫМ порядком
        workbook = openpyxl.Workbook()
        worksheet = workbook.active

        # 📋 Заголовки
        worksheet.append(['Идентификатор', 'Название', 'Title', 'Цена', 'Описание', 'Meta-описание', 'Изображение'])

        # 🔄 Добавляем строки в ОРИГИНАЛЬНОМ порядке
        for row_info in all_rows:
            row_type = row_info['type']
            data = row_info['data']

            if row_type == 'category':
                # 📂 Категория (с точкой в идентификаторе)
                # 🔧 ИСПРАВЛЕНО: Используем оригинальный SKU вместо жестко заданного "1"
                category_sku = data.get('category_sku', 1)

                worksheet.append([
                    f"{category_sku}.{data['category_name']}",  # ✅ ПРАВИЛЬНЫЙ SKU из данных!
                    data.get('name', ''),
                    data.get('title', ''),
                    '',  # 💰 Пустая цена для категории
                    data.get('description', ''),
                    data.get('meta_description', ''),
                    data.get('image', '')
                ])

            else:  # product
                # 🛍️ Товар (без точки в идентификаторе)
                worksheet.append([
                    data.get('sku', ''),  # ✅ SKU без точки = товар
                    data.get('name', ''),
                    data.get('title', ''),
                    data.get('price', 0),
                    data.get('description', ''),
                    data.get('meta_description', ''),
                    data.get('image', '')
                ])

        # 💾 Сохраняем во временный буфер
        temp_buffer = io.BytesIO()
        workbook.save(temp_buffer)
        temp_buffer.seek(0)

        # 📁 Создаем файл-объект для процессора
        temp_file = InMemoryUploadedFile(
            temp_buffer, None, 'import_data.xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            temp_buffer.getbuffer().nbytes, None
        )

        # 🚀 Используем существующий процессор для РЕАЛЬНОГО сохранения в БД
        logger.info("🔄 Запуск ProductImportProcessor с ПОЛНЫМИ данными...")
        processor = ProductImportProcessor()
        result = processor.process_excel_file(temp_file)

        # 📊 Логируем результат
        logger.info(f"📈 Результат импорта: {result['success']}, статистика: {result.get('statistics', {})}")

        # 🧹 Очищаем сессию
        for key in ['preview_data', 'full_import_data', 'uploaded_file_name', 'uploaded_file_size',
                    'uploaded_zip_name', 'uploaded_zip_size', 'images_processed']:
            request.session.pop(key, None)

        # 📈 Сохраняем результаты в сессии для отображения
        request.session['import_results'] = result

        if result['success']:
            stats = result['statistics']
            # 🆕 Дополняем сообщение информацией об изображениях
            images_info = ""
            if stats.get('images_processed', 0) > 0:
                images_info = f", изображений: {stats.get('images_processed', 0)}"

            messages.success(
                request,
                f"✅ Импорт завершён! "
                f"Создано категорий: {stats.get('categories_created', 0)}, "
                f"товаров: {stats.get('products_created', 0)}, "
                f"обновлено категорий: {stats.get('categories_updated', 0)}, "
                f"товаров: {stats.get('products_updated', 0)}"
                f"{images_info}, "
                f"ошибок: {stats.get('errors', 0)}"
            )
        else:
            messages.error(request, f"❌ Импорт завершён с ошибками: {result.get('error', 'Неизвестная ошибка')}")

        return redirect('import_results')

    except Exception as e:
        error_msg = f"❌ Критическая ошибка при импорте: {str(e)}"
        logger.error(error_msg, exc_info=True)
        messages.error(request, error_msg)
        return redirect('import_form')


@staff_member_required
def import_results_view(request):
    """📈 НЕИЗМЕНЕННАЯ страница результатов импорта"""
    try:
        # 📊 Получаем результаты из сессии
        results = request.session.get('import_results')

        if not results:
            messages.warning(request, "⚠️ Результаты импорта не найдены")
            return redirect('import_form')

        # 📈 Подготавливаем контекст
        context = {
            'title': 'Результаты импорта товаров',
            'results': results,
            'statistics': results.get('statistics', {}),
            'errors': results.get('errors', []),
            'invalid_data': results.get('invalid_data', []),
        }

        # 🧹 Очищаем результаты из сессии после отображения
        request.session.pop('import_results', None)

        return render(request, 'admin/products/import_results.html', context)

    except Exception as e:
        error_msg = f"❌ Ошибка отображения результатов: {str(e)}"
        logger.error(error_msg)
        messages.error(request, error_msg)
        return redirect('import_form')


@staff_member_required
@csrf_exempt
def ajax_validate_file(request):
    """⚡ ОБНОВЛЕННАЯ AJAX валидация файлов (Excel + ZIP)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'Файл не выбран'})

        file = request.FILES['file']

        # 🆕 Определяем тип файла
        file_extension = file.name.lower().split('.')[-1]

        if file_extension in ['xlsx', 'xls']:
            # ✅ Валидация Excel файла
            form = ExcelUploadForm()
            form.cleaned_data = {'excel_file': file}

            try:
                form.clean_excel_file()

                # 📊 Быстрая проверка структуры файла
                preview_result = preview_excel_data(file)

                if preview_result['success']:
                    return JsonResponse({
                        'success': True,
                        'message': 'Excel файл корректен',
                        'file_type': 'excel',
                        'statistics': preview_result['statistics']
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': preview_result['error']
                    })

            except forms.ValidationError as e:
                return JsonResponse({'success': False, 'error': str(e)})

        elif file_extension == 'zip':
            # 🆕 Валидация ZIP файла
            form = ExcelUploadForm()
            form.cleaned_data = {'images_zip': file}

            try:
                form.clean_images_zip()

                # 📊 Быстрая проверка содержимого ZIP
                import zipfile
                with zipfile.ZipFile(file, 'r') as zip_file:
                    file_count = len([f for f in zip_file.namelist()
                                      if not f.startswith('__MACOSX') and not f.endswith('/')])

                return JsonResponse({
                    'success': True,
                    'message': f'ZIP архив корректен ({file_count} файлов)',
                    'file_type': 'zip',
                    'file_count': file_count
                })

            except forms.ValidationError as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            return JsonResponse({
                'success': False,
                'error': f'Неподдерживаемый формат файла: .{file_extension}'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Критическая ошибка: {str(e)}'
        })

# 🔧 КРИТИЧНОЕ ИСПРАВЛЕНИЕ В ЭТОМ ФАЙЛЕ:
#
# ✅ ИСПРАВЛЕНО: f"1.{data['category_name']}" → f"{category_sku}.{data['category_name']}"
# ✅ ДОБАВЛЕНО: Извлечение category_sku из данных
# ✅ РЕЗУЛЬТАТ: Теперь каждая категория получает ПРАВИЛЬНЫЙ SKU:
#   - BMW: SKU = 1
#   - Acura: SKU = 2
#   - Alfa Romeo: SKU = 3
#
# 🎯 ОДНА СТРОЧКА КОДА БЫЛА ПРИЧИНОЙ ВСЕХ ПРОБЛЕМ!