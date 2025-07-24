# 📁 products/admin_views.py
# 🛠️ ФИНАЛЬНАЯ версия БЕЗ костыля с пересозданием Excel
# ✅ Используем process_structured_data() напрямую
# ✅ Убрана временная Excel-книга в execute_import_view()

import logging
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile

from .import_processor import ProductImportProcessor, preview_excel_data
from .import_utils import read_excel_file, separate_categories_and_products
from .image_utils import process_images_zip

logger = logging.getLogger(__name__)


class UnifiedImportForm(forms.Form):
    """
    📊 ЕДИНАЯ форма для загрузки Excel + ZIP

    Заменяет дублирование ExcelUploadForm и ProductImportForm
    """

    excel_file = forms.FileField(
        label="📊 Excel файл с товарами",
        help_text="Поддерживаемые форматы: .xlsx, .xls (макс. 10 МБ)",
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control'
        })
    )

    images_zip = forms.FileField(
        label="🖼️ ZIP архив с изображениями",
        help_text="Необязательно. Поддерживаемый формат: .zip (макс. 10 МБ)",
        required=False,
        widget=forms.FileInput(attrs={
            'accept': '.zip',
            'class': 'form-control'
        })
    )

    def clean_excel_file(self):
        """🔍 Валидация Excel файла"""
        file = self.cleaned_data.get('excel_file')

        if not file:
            raise forms.ValidationError("❌ Файл не выбран")

        # 📏 Размер файла
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                f"❌ Файл слишком большой: {file.size / 1024 / 1024:.1f} МБ. Максимум: 10 МБ"
            )

        # 📁 Расширение
        allowed_extensions = ['.xlsx', '.xls']
        file_extension = file.name.lower().split('.')[-1]

        if f'.{file_extension}' not in allowed_extensions:
            raise forms.ValidationError(
                f"❌ Неподдерживаемый формат: .{file_extension}. Разрешены: {', '.join(allowed_extensions)}"
            )

        return file

    def clean_images_zip(self):
        """🆕 Валидация ZIP архива"""
        zip_file = self.cleaned_data.get('images_zip')

        if not zip_file:
            return zip_file

        # 📏 Размер файла
        if zip_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                f"❌ ZIP слишком большой: {zip_file.size / 1024 / 1024:.1f} МБ. Максимум: 10 МБ"
            )

        # 📁 Расширение
        if not zip_file.name.lower().endswith('.zip'):
            raise forms.ValidationError("❌ Неподдерживаемый формат. Разрешен только .zip")

        return zip_file


@staff_member_required
def import_form_view(request):
    """📝 Страница с формой загрузки файлов"""
    if request.method == 'POST':
        form = UnifiedImportForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                excel_file = form.cleaned_data['excel_file']
                images_zip = form.cleaned_data.get('images_zip')

                # 💾 Сохраняем информацию о файлах
                request.session['uploaded_file_name'] = excel_file.name
                request.session['uploaded_file_size'] = excel_file.size

                # 🖼️ Обработка изображений ДО анализа Excel
                images_processed = 0
                if images_zip:
                    try:
                        request.session['uploaded_zip_name'] = images_zip.name
                        request.session['uploaded_zip_size'] = images_zip.size

                        logger.info("🖼️ Начинаем обработку ZIP архива с изображениями...")
                        images_processed = process_images_zip(images_zip)
                        request.session['images_processed'] = images_processed

                        messages.success(request, f"🖼️ Обработано изображений: {images_processed}")
                        logger.info(f"✅ Успешно обработано {images_processed} изображений")

                    except Exception as e:
                        error_msg = f"❌ Ошибка обработки изображений: {str(e)}"
                        logger.error(error_msg)
                        messages.warning(request, error_msg)
                        request.session['images_processed'] = 0
                else:
                    # 🧹 Очищаем данные о ZIP если не загружен
                    request.session.pop('uploaded_zip_name', None)
                    request.session.pop('uploaded_zip_size', None)
                    request.session['images_processed'] = 0

                # 📊 Анализируем Excel файл
                excel_file.seek(0)
                preview_result = preview_excel_data(excel_file)

                if not preview_result['success']:
                    messages.error(request, f"❌ {preview_result['error']}")
                    return render(request, 'admin/products/import_form.html', {'form': form})

                # 📊 Читаем ПОЛНЫЕ данные для импорта
                excel_file.seek(0)
                success, raw_data = read_excel_file(excel_file)

                if not success:
                    messages.error(request, f"❌ Ошибка чтения файла: {raw_data}")
                    return render(request, 'admin/products/import_form.html', {'form': form})

                # 🔄 Разделяем на категории и товары
                categories, products, invalid_data = separate_categories_and_products(raw_data)

                # 💾 Сохраняем данные в сессии
                request.session['preview_data'] = preview_result  # Для отображения
                request.session['full_import_data'] = {  # 🎯 СТРУКТУРИРОВАННЫЕ данные (не Excel!)
                    'categories': categories,
                    'products': products,
                    'invalid_data': invalid_data,
                    'success': True
                }

                # 🎉 Формируем сообщение об успехе
                if images_zip:
                    success_msg = f"✅ Файлы загружены: Excel проанализирован, {images_processed} изображений обработано"
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
        form = UnifiedImportForm()

    return render(request, 'admin/products/import_form.html', {'form': form})


@staff_member_required
def import_preview_view(request):
    """👁️ Страница предпросмотра данных с информацией об изображениях"""
    try:
        # 📊 Получаем данные предпросмотра
        preview_data = request.session.get('preview_data')

        if not preview_data:
            messages.error(request, "❌ Данные для предпросмотра не найдены. Загрузите файл заново.")
            return redirect('import_form')

        if not preview_data['success']:
            messages.error(request, f"❌ {preview_data['error']}")
            return redirect('import_form')

        # 🖼️ Информация об изображениях
        images_processed = request.session.get('images_processed', 0)
        zip_name = request.session.get('uploaded_zip_name')
        zip_size = request.session.get('uploaded_zip_size', 0)

        # 📈 Контекст для шаблона
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
            # 🖼️ Данные об изображениях
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
    """
    🚀 ИСПРАВЛЁННОЕ выполнение импорта БЕЗ костыля с Excel

    Теперь использует process_structured_data() напрямую с готовыми данными
    """
    try:
        # 📁 Проверяем подтверждение
        if 'confirm_import' not in request.POST:
            messages.error(request, "❌ Импорт не подтверждён")
            return redirect('import_preview')

        # 📊 Получаем структурированные данные из сессии
        full_data = request.session.get('full_import_data')

        if not full_data or not full_data.get('success'):
            messages.error(request, "❌ Данные для импорта не найдены. Загрузите файл заново.")
            return redirect('import_form')

        # 🎯 Извлекаем готовые списки
        categories_data = full_data.get('categories', [])
        products_data = full_data.get('products', [])
        invalid_data = full_data.get('invalid_data', [])

        logger.info(f"🚀 Начинаем прямой импорт: {len(categories_data)} категорий, {len(products_data)} товаров")
        messages.info(request, "🔄 Запуск импорта товаров...")

        # 🎯 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Используем новый метод без Excel!
        processor = ProductImportProcessor()
        result = processor.process_structured_data(categories_data, products_data, invalid_data)

        # 📊 Логируем результат
        logger.info(f"📈 Результат импорта: {result['success']}, статистика: {result.get('statistics', {})}")

        # 🧹 Очищаем сессию
        session_keys = [
            'preview_data', 'full_import_data', 'uploaded_file_name', 'uploaded_file_size',
            'uploaded_zip_name', 'uploaded_zip_size', 'images_processed'
        ]
        for key in session_keys:
            request.session.pop(key, None)

        # 📈 Сохраняем результаты для отображения
        request.session['import_results'] = result

        if result['success']:
            stats = result['statistics']
            # 🖼️ Дополняем сообщение информацией об изображениях
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
    """📈 Страница результатов импорта"""
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
    """⚡ AJAX валидация файлов (Excel + ZIP)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'Файл не выбран'})

        file = request.FILES['file']
        file_extension = file.name.lower().split('.')[-1]

        if file_extension in ['xlsx', 'xls']:
            # ✅ Валидация Excel файла
            form = UnifiedImportForm()
            form.cleaned_data = {'excel_file': file}

            try:
                form.clean_excel_file()

                # 📊 Быстрая проверка структуры
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
            # 🖼️ Валидация ZIP файла
            form = UnifiedImportForm()
            form.cleaned_data = {'images_zip': file}

            try:
                form.clean_images_zip()

                # 📊 Быстрая проверка содержимого
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
                'error': f'Неподдерживаемый формат: .{file_extension}'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Критическая ошибка: {str(e)}'
        })

# 🔧 КРИТИЧНЫЕ ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ✅ СОЗДАНО: UnifiedImportForm - единая форма вместо дублирования
# ✅ УБРАНО: Пересоздание временной Excel-книги в execute_import_view()
# ✅ ДОБАВЛЕНО: Прямой вызов processor.process_structured_data()
# ✅ УПРОЩЕНО: Логика обработки данных - меньше промежуточных шагов
# ✅ СОХРАНЕНО: Вся логика валидации и обработки ошибок
#
# 🎯 РЕЗУЛЬТАТ:
# - НЕТ костыля с временным Excel файлом
# - Одна форма вместо дублирования
# - Прямая передача данных в процессор
# - Более чистая архитектура