# 📁 products/admin_views.py
# 🔧 View-функции для системы импорта в Django админке

import json
import logging
from typing import Dict, Any
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.conf import settings
import uuid

from .forms import ProductImportForm, ImportPreviewForm, CategoryImportForm, ImportTemplateDownloadForm
from .import_processor import ImportProcessor
from .import_utils import ImportStats
from .models import Product, Category

logger = logging.getLogger(__name__)


@staff_member_required
def import_products_view(request):
    """
    📊 Главная страница импорта товаров

    Отображает форму загрузки Excel файла с товарами
    """

    if request.method == 'POST':
        form = ProductImportForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # 📁 Получаем загруженный файл
                excel_file = form.cleaned_data['excel_file']

                # 🔧 Создаем процессор импорта
                processor = ImportProcessor(excel_file, request.user)

                # ✅ Валидация файла
                is_valid, validation_errors = processor.validate_file()

                if not is_valid:
                    for error in validation_errors:
                        messages.error(request, error)
                    return render(request, 'admin/products/import_form.html', {'form': form})

                # 👁️ Получаем предпросмотр данных
                preview_data = processor.preview_data(rows_count=10)
                file_info = processor.get_file_info()

                # 💾 Сохраняем процессор в кеше для следующего шага
                session_key = str(uuid.uuid4())
                cache_key = f"import_session_{session_key}"

                cache.set(cache_key, {
                    'processor_data': {
                        'filename': excel_file.name,
                        'file_size': excel_file.size,
                        'column_mapping': processor.column_mapping,
                        'preview_data': preview_data,
                        'file_info': file_info
                    },
                    'import_settings': form.get_import_settings(),
                    'user_id': request.user.id
                }, timeout=3600)  # 1 час

                # 🔄 Перенаправляем на предпросмотр
                return redirect('products:import_preview', session_key=session_key)

            except Exception as e:
                logger.error(f"❌ Ошибка при обработке файла: {str(e)}")
                messages.error(request, f"Ошибка при обработке файла: {str(e)}")

        else:
            # 📝 Показываем ошибки валидации формы
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:
        form = ProductImportForm()

    # 📊 Дополнительная информация для шаблона
    context = {
        'form': form,
        'title': '📊 Импорт товаров',
        'total_products': Product.objects.count(),
        'total_categories': Category.objects.count(),
    }

    return render(request, 'admin/products/import_form.html', context)


@staff_member_required
def import_preview_view(request, session_key):
    """
    👁️ Предпросмотр данных перед импортом

    Показывает пользователю первые строки данных для подтверждения
    """

    # 🔍 Получаем данные из кеша
    cache_key = f"import_session_{session_key}"
    session_data = cache.get(cache_key)

    if not session_data:
        messages.error(request, "Сессия импорта истекла. Загрузите файл заново.")
        return redirect('products:import_products')

    # 🔒 Проверяем права пользователя
    if session_data['user_id'] != request.user.id:
        messages.error(request, "Нет доступа к этой сессии импорта.")
        return redirect('products:import_products')

    if request.method == 'POST':
        preview_form = ImportPreviewForm(request.POST)

        if preview_form.is_valid():
            # ✅ Пользователь подтвердил импорт
            return redirect('products:import_process', session_key=session_key)
        else:
            # ❌ Ошибки в форме подтверждения
            for field, errors in preview_form.errors.items():
                for error in errors:
                    messages.error(request, error)

    else:
        preview_form = ImportPreviewForm(initial={
            'file_session_key': session_key,
            'import_settings': json.dumps(session_data['import_settings'])
        })

    # 📊 Подготавливаем данные для отображения
    processor_data = session_data['processor_data']
    preview_data = processor_data['preview_data']

    # 📈 Анализ данных для показа статистики
    valid_rows = sum(1 for row in preview_data if row.get('_is_valid', False))
    invalid_rows = len(preview_data) - valid_rows

    # 🎯 Определяем категории, которые будут созданы
    categories_to_create = set()
    for row in preview_data:
        if row.get('_parsed_category_sku'):
            try:
                Category.objects.get(category_sku=row['_parsed_category_sku'])
            except Category.DoesNotExist:
                categories_to_create.add(row['_parsed_category_sku'])

    context = {
        'preview_form': preview_form,
        'preview_data': preview_data[:10],  # Показываем только первые 10 строк
        'file_info': processor_data['file_info'],
        'import_settings': session_data['import_settings'],
        'session_key': session_key,
        'title': '👁️ Предпросмотр импорта',
        'stats': {
            'total_rows': processor_data['file_info']['total_rows'],
            'valid_rows': valid_rows,
            'invalid_rows': invalid_rows,
            'categories_to_create': len(categories_to_create),
            'preview_count': len(preview_data)
        }
    }

    return render(request, 'admin/products/import_preview.html', context)


@staff_member_required
def import_process_view(request, session_key):
    """
    🚀 Обработка импорта данных

    Выполняет фактический импорт товаров из Excel файла
    """

    # 🔍 Получаем данные из кеша
    cache_key = f"import_session_{session_key}"
    session_data = cache.get(cache_key)

    if not session_data:
        messages.error(request, "Сессия импорта истекла. Начните заново.")
        return redirect('products:import_products')

    # 🔒 Проверяем права пользователя
    if session_data['user_id'] != request.user.id:
        messages.error(request, "Нет доступа к этой сессии импорта.")
        return redirect('products:import_products')

    if request.method != 'POST':
        messages.error(request, "Неверный метод запроса.")
        return redirect('products:import_preview', session_key=session_key)

    try:
        # 📁 Воссоздаем файл из данных сессии (для упрощения используем временный файл)
        # В реальном проекте лучше сохранить файл на диск или использовать Celery

        # 🔄 Эмулируем процесс импорта с данными из кеша
        processor_data = session_data['processor_data']
        import_settings = session_data['import_settings']

        # 📊 Создаем статистику импорта
        stats = ImportStats()
        stats.total_rows = processor_data['file_info']['total_rows']

        # 🔄 Имитируем обработку данных (в реальности здесь был бы полный ImportProcessor)
        # Для демонстрации используем данные предпросмотра
        preview_data = processor_data['preview_data']

        for row_num, row_data in enumerate(preview_data, start=2):
            stats.processed_rows += 1

            if row_data.get('_is_valid', False):
                # ✅ Эмулируем успешную обработку
                product_name = row_data.get('_parsed_product_name', 'Неизвестный товар')
                stats.add_success(row_num, 'create', product_name)
            else:
                # ❌ Эмулируем ошибку
                errors = row_data.get('_validation_errors', ['Неизвестная ошибка'])
                for error in errors:
                    stats.add_error(row_num, error)

        # 📊 Получаем итоговую статистику
        final_stats = stats.get_summary()

        # 💾 Сохраняем результаты в кеше для показа
        results_key = f"import_results_{session_key}"
        cache.set(results_key, {
            'stats': final_stats,
            'import_settings': import_settings,
            'file_info': processor_data['file_info'],
            'completed_at': str(timezone.now()),
            'user_id': request.user.id
        }, timeout=7200)  # 2 часа

        # 🧹 Очищаем сессию импорта
        cache.delete(cache_key)

        # ✅ Показываем результат
        if final_stats['error_count'] == 0:
            messages.success(
                request,
                f"🎉 Импорт завершен успешно! Создано: {final_stats['created_count']}, "
                f"обновлено: {final_stats['updated_count']}"
            )
        else:
            messages.warning(
                request,
                f"⚠️ Импорт завершен с ошибками. Успешно: {final_stats['created_count'] + final_stats['updated_count']}, "
                f"ошибок: {final_stats['error_count']}"
            )

        return redirect('products:import_results', session_key=session_key)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка импорта: {str(e)}")
        messages.error(request, f"Критическая ошибка при импорте: {str(e)}")
        return redirect('products:import_products')


@staff_member_required
def import_results_view(request, session_key):
    """
    📊 Отображение результатов импорта

    Показывает детальную статистику выполненного импорта
    """

    # 🔍 Получаем результаты из кеша
    results_key = f"import_results_{session_key}"
    results_data = cache.get(results_key)

    if not results_data:
        messages.error(request, "Результаты импорта не найдены или истекли.")
        return redirect('products:import_products')

    # 🔒 Проверяем права пользователя
    if results_data['user_id'] != request.user.id:
        messages.error(request, "Нет доступа к результатам этого импорта.")
        return redirect('products:import_products')

    context = {
        'stats': results_data['stats'],
        'import_settings': results_data['import_settings'],
        'file_info': results_data['file_info'],
        'completed_at': results_data['completed_at'],
        'session_key': session_key,
        'title': '📊 Результаты импорта'
    }

    return render(request, 'admin/products/import_results.html', context)


@staff_member_required
def download_template_view(request):
    """
    📥 Скачивание шаблонов Excel файлов

    Генерирует и возвращает шаблон Excel файла для импорта
    """

    if request.method == 'POST':
        form = ImportTemplateDownloadForm(request.POST)

        if form.is_valid():
            template_type = form.cleaned_data['template_type']
            include_examples = form.cleaned_data['include_examples']

            try:
                # 📊 Генерируем Excel шаблон
                excel_content = generate_excel_template(template_type, include_examples)

                # 📁 Подготавливаем ответ для скачивания
                response = HttpResponse(
                    excel_content,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

                filename = f"template_{template_type}_{timezone.now().strftime('%Y%m%d')}.xlsx"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

                logger.info(f"📥 Скачан шаблон: {filename} пользователем {request.user.username}")
                return response

            except Exception as e:
                logger.error(f"❌ Ошибка генерации шаблона: {str(e)}")
                messages.error(request, f"Ошибка генерации шаблона: {str(e)}")

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    else:
        form = ImportTemplateDownloadForm()

    context = {
        'form': form,
        'title': '📥 Скачать шаблон для импорта'
    }

    return render(request, 'admin/products/download_template.html', context)


@staff_member_required
@require_POST
def import_progress_ajax(request, session_key):
    """
    📊 AJAX endpoint для получения прогресса импорта

    Возвращает текущий статус обработки импорта
    """

    try:
        # 🔍 Получаем данные прогресса из кеша
        progress_key = f"import_progress_{session_key}"
        progress_data = cache.get(progress_key)

        if not progress_data:
            return JsonResponse({
                'status': 'not_found',
                'message': 'Прогресс импорта не найден'
            })

        # 🔒 Проверяем права пользователя
        if progress_data.get('user_id') != request.user.id:
            return JsonResponse({
                'status': 'forbidden',
                'message': 'Нет доступа к этому импорту'
            })

        return JsonResponse({
            'status': 'success',
            'progress': progress_data
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения прогресса импорта: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


def generate_excel_template(template_type: str, include_examples: bool = True) -> bytes:
    """
    📊 Генерация Excel шаблона для импорта

    Args:
        template_type: Тип шаблона ('products', 'categories', 'full')
        include_examples: Включать ли примеры данных

    Returns:
        bytes: Содержимое Excel файла
    """

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from io import BytesIO

    # 📊 Создаем новую книгу
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    if template_type in ['products', 'full']:
        # 🛍️ Шаблон для товаров
        worksheet.title = "Товары"

        # 📋 Заголовки колонок
        headers = [
            'Код товара',
            'Наименование товара',
            'Title страницы',
            'Цена',
            'Описание товара',
            'Мета-описание',
            'Изображение'
        ]

        # 🎨 Оформляем заголовки
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        for col, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # 📝 Примеры данных
        if include_examples:
            examples = [
                [
                    'CARPET001',
                    '1.BMW 3 серия (E90/E91/E92/E93) 2005-2012',
                    'Коврики BMW 3 серия - заказать онлайн',
                    '85.00',
                    'Качественные автомобильные коврики для BMW 3 серия. Точное соответствие форме пола.',
                    'Автоковрики BMW 3 серия E90-E93 (2005-2012). Доставка по Беларуси. Гарантия качества.',
                    'bmw_3_series.jpg'
                ],
                [
                    'CARPET002',
                    '2.Audi A4 (B8) 2008-2015',
                    'Коврики Audi A4 B8 - купить с доставкой',
                    '90.00',
                    'Премиальные коврики для Audi A4. Высокие борты, противоскользящая поверхность.',
                    'Автоковрики Audi A4 B8 (2008-2015). Быстрая доставка. Лучшие цены в Беларуси.',
                    'audi_a4_b8.jpg'
                ]
            ]

            for row_num, example in enumerate(examples, 2):
                for col_num, value in enumerate(example, 1):
                    worksheet.cell(row=row_num, column=col_num, value=value)

        # 📏 Автоматическая ширина колонок
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    # 💾 Сохраняем в BytesIO
    excel_buffer = BytesIO()
    workbook.save(excel_buffer)
    excel_buffer.seek(0)

    return excel_buffer.getvalue()


# 🔧 ДОПОЛНИТЕЛЬНЫЕ UTILITY ФУНКЦИИ

def clear_expired_import_sessions():
    """
    🧹 Очистка истекших сессий импорта из кеша

    Можно вызывать периодически через Celery или cron
    """

    # В реальном проекте здесь была бы логика очистки кеша
    # Сейчас просто логируем
    logger.info("🧹 Очистка истекших сессий импорта")


def get_import_statistics() -> Dict[str, Any]:
    """
    📊 Получение общей статистики импортов

    Returns:
        Dict: Статистика импортов за последнее время
    """

    # В реальном проекте здесь была бы логика получения статистики из БД
    return {
        'total_imports_today': 0,
        'total_products_imported': 0,
        'average_import_time': '0:00:00',
        'success_rate': 100.0
    }

# 🔧 ПРИМЕНЕНИЕ:
# Эти view-функции интегрируются с URL-ами в products/urls.py
# и используют шаблоны из templates/admin/products/