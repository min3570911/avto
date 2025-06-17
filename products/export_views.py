# 📁 products/export_views.py
# 🌐 View-функции для экспорта товаров в Excel
# 🚀 Максимально простое решение: одна кнопка → мгновенное скачивание

import logging
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied

from .export_utils import generate_excel_export, get_export_statistics

logger = logging.getLogger(__name__)


@staff_member_required
@require_http_methods(["GET"])
def export_excel_view(request):
    """
    📊 ГЛАВНАЯ VIEW: Экспорт товаров в Excel

    Генерирует Excel файл и сразу отдает на скачивание.
    Без предпросмотра, без асинхронности - максимально просто.

    Returns:
        HttpResponse: Excel файл для скачивания
    """
    try:
        logger.info(f"🚀 Пользователь {request.user.username} запустил экспорт товаров")

        # 📊 Проверяем есть ли данные для экспорта
        stats = get_export_statistics()

        if stats.get('estimated_rows', 0) == 0:
            logger.warning("⚠️ Нет данных для экспорта")
            messages.warning(request, "⚠️ Нет активных категорий или товаров для экспорта")
            return redirect('admin:index')

        logger.info(f"📊 Будет экспортировано: {stats['estimated_rows']} строк")

        # 🚀 Генерируем Excel файл
        excel_buffer = generate_excel_export()

        # 📅 Формируем имя файла с датой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tovary_export_{timestamp}.xlsx"

        # 📦 Создаем HTTP response для скачивания
        response = HttpResponse(
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(excel_buffer.getvalue())

        logger.info(f"✅ Экспорт завершен: {filename} ({len(excel_buffer.getvalue())} байт)")

        # 🎉 Добавляем сообщение об успехе (покажется на следующей странице)
        messages.success(
            request,
            f"✅ Экспорт завершен! Скачано: {stats['total_categories']} категорий, "
            f"{stats['total_products']} товаров"
        )

        return response

    except Exception as e:
        error_msg = f"❌ Ошибка экспорта: {str(e)}"
        logger.error(error_msg, exc_info=True)
        messages.error(request, error_msg)
        return redirect('admin:index')


@staff_member_required
def export_info_view(request):
    """
    📊 Страница информации об экспорте (опционально)

    Показывает статистику перед экспортом, если нужно
    """
    try:
        # 📊 Получаем статистику
        stats = get_export_statistics()

        context = {
            'title': 'Экспорт товаров',
            'statistics': stats,
            'has_data': stats.get('estimated_rows', 0) > 0
        }

        return render(request, 'admin/products/export_info.html', context)

    except Exception as e:
        logger.error(f"❌ Ошибка страницы информации об экспорте: {e}")
        messages.error(request, f"❌ Ошибка: {str(e)}")
        return redirect('admin:index')


@staff_member_required
def export_ajax_stats(request):
    """
    ⚡ AJAX получение статистики экспорта

    Для динамического обновления информации на странице
    """
    try:
        if not request.user.is_staff:
            raise PermissionDenied("❌ Доступ запрещен")

        stats = get_export_statistics()

        return JsonResponse({
            'success': True,
            'statistics': stats
        })

    except Exception as e:
        logger.error(f"❌ Ошибка AJAX статистики: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_export_button_html():
    """
    🎨 HTML код кнопки экспорта для встраивания в админку

    Returns:
        str: HTML код кнопки
    """
    return '''
    <div style="margin: 10px 0;">
        <a href="/products/export/" 
           class="btn btn-primary" 
           style="background-color: #28a745; border-color: #28a745; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">
            📊 Экспорт товаров в Excel
        </a>
        <small style="color: #666; margin-left: 10px;">
            Скачать все активные категории и товары
        </small>
    </div>
    '''


# 🔧 Вспомогательные функции для интеграции с админкой

def can_export(user) -> bool:
    """
    🔐 Проверка прав на экспорт

    Args:
        user: Пользователь Django

    Returns:
        bool: Может ли пользователь экспортировать
    """
    return user.is_authenticated and user.is_staff


def get_export_context():
    """
    📊 Контекст для шаблонов админки

    Returns:
        dict: Контекст с информацией об экспорте
    """
    try:
        stats = get_export_statistics()

        return {
            'export_available': stats.get('estimated_rows', 0) > 0,
            'export_stats': stats,
            'export_url': '/products/export/',
            'export_info_url': '/products/export/info/'
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения контекста экспорта: {e}")
        return {
            'export_available': False,
            'export_stats': {},
            'export_url': '/products/export/',
            'export_info_url': '/products/export/info/'
        }

# 🎯 ФУНКЦИИ ЭТОГО ФАЙЛА:
#
# ✅ export_excel_view() - главная view экспорта (GET → скачать файл)
# ✅ export_info_view() - страница статистики (опционально)
# ✅ export_ajax_stats() - AJAX статистика для UI
# ✅ get_export_button_html() - HTML кнопки для админки
# ✅ can_export() - проверка прав доступа
# ✅ get_export_context() - контекст для шаблонов
#
# 🚀 FLOW ЭКСПОРТА:
# 1. Админ переходит на /products/export/
# 2. Проверяются права и наличие данных
# 3. Генерируется Excel за 2-3 секунды
# 4. Файл сразу скачивается с именем tovary_export_YYYYMMDD_HHMMSS.xlsx
# 5. Показывается сообщение об успехе
#
# 🔒 БЕЗОПАСНОСТЬ:
# - @staff_member_required на всех view
# - Проверка прав в AJAX
# - Обработка ошибок с логированием