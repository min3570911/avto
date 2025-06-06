# 📁 products/templatetags/category_filters.py
# 🔧 Template фильтры для умной обработки контента категорий

import re
from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def smart_truncate_sentences(value, count=3):
    """
    📝 Умное извлечение N предложений с сохранением HTML-форматирования

    Args:
        value: HTML-контент
        count: количество предложений (по умолчанию 3)

    Returns:
        HTML с N предложениями и сохранением форматирования
    """
    if not value:
        return ""

    try:
        count = int(count)
    except (ValueError, TypeError):
        count = 3

    # 🧹 Очищаем от тегов для анализа структуры предложений
    clean_text = strip_tags(value)

    # 🔍 Разбиваем на предложения по точкам
    sentences = re.split(r'(?<=[.!?])\s+', clean_text.strip())

    # 📏 Берем первые N предложений
    if len(sentences) <= count:
        return mark_safe(value)  # Возвращаем весь контент если предложений мало

    # 🎯 Находим позицию, где должен быть обрез в оригинальном HTML
    target_sentences = sentences[:count]
    target_text = ' '.join(target_sentences)

    # 📍 Ищем позицию конца последнего предложения в HTML
    # Находим последнюю точку из целевых предложений
    last_sentence = target_sentences[-1]

    # 🔍 Ищем эту точку в оригинальном HTML
    html_lower = value.lower()
    last_sentence_lower = last_sentence.lower()

    # Находим позицию последнего предложения в HTML
    sentence_pos = html_lower.find(last_sentence_lower)
    if sentence_pos == -1:
        # Fallback: если не найдено, берем приблизительно
        target_length = len(target_text)
        return mark_safe(value[:target_length] + '...')

    # 📍 Находим конец предложения (точку) после найденной позиции
    sentence_end_search_start = sentence_pos + len(last_sentence_lower)
    dot_pos = value.find('.', sentence_end_search_start)

    if dot_pos == -1:
        dot_pos = sentence_end_search_start
    else:
        dot_pos += 1  # Включаем точку

    # ✂️ Обрезаем HTML до найденной позиции
    truncated_html = value[:dot_pos]

    # 🔧 Закрываем незакрытые HTML теги
    truncated_html = close_unclosed_tags(truncated_html)

    return mark_safe(truncated_html)


@register.filter
def mobile_truncate_sentences(value, count=2):
    """
    📱 Мобильная версия truncate - меньше предложений

    Args:
        value: HTML-контент
        count: количество предложений для мобильных (по умолчанию 2)
    """
    return smart_truncate_sentences(value, count)


def close_unclosed_tags(html):
    """
    🔧 Закрытие незакрытых HTML тегов после обрезки

    Args:
        html: обрезанный HTML

    Returns:
        HTML с правильно закрытыми тегами
    """
    if not html:
        return html

    # 🏷️ Теги, которые нужно закрывать (не самозакрывающиеся)
    closing_tags = ['p', 'div', 'span', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol',
                    'li', 'blockquote']

    # 📚 Стек открытых тегов
    open_tags = []

    # 🔍 Находим все теги в HTML
    tag_pattern = r'<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*>'
    matches = re.finditer(tag_pattern, html)

    for match in matches:
        is_closing = bool(match.group(1))  # группа 1 содержит "/" для закрывающих тегов
        tag_name = match.group(2).lower()

        if tag_name in closing_tags:
            if is_closing:
                # 🔚 Закрывающий тег - убираем из стека
                if tag_name in open_tags:
                    open_tags.remove(tag_name)
            else:
                # 🔛 Открывающий тег - добавляем в стек
                # Проверяем, что это не самозакрывающийся тег
                if not match.group(0).endswith('/>'):
                    open_tags.append(tag_name)

    # 🔐 Закрываем все незакрытые теги в обратном порядке
    closing_tags_html = ''
    for tag in reversed(open_tags):
        closing_tags_html += f'</{tag}>'

    return html + closing_tags_html


@register.filter
def has_youtube_video(value):
    """
    🎬 Проверка наличия YouTube видео в контенте

    Args:
        value: HTML-контент

    Returns:
        True если есть YouTube iframe
    """
    if not value:
        return False

    return 'youtube.com/embed' in value or 'youtube-video-container' in value


@register.filter
def extract_text_content(value):
    """
    📝 Извлечение чистого текста без HTML тегов

    Args:
        value: HTML-контент

    Returns:
        Чистый текст
    """
    if not value:
        return ""

    return strip_tags(value)


@register.filter
def word_count(value):
    """
    🔢 Подсчет количества слов в контенте

    Args:
        value: HTML-контент

    Returns:
        Количество слов
    """
    if not value:
        return 0

    clean_text = strip_tags(value)
    words = clean_text.split()
    return len(words)


@register.filter
def reading_time(value, wpm=200):
    """
    ⏱️ Примерное время чтения контента

    Args:
        value: HTML-контент
        wpm: слов в минуту (по умолчанию 200)

    Returns:
        Время чтения в минутах
    """
    if not value:
        return 0

    try:
        wpm = int(wpm)
    except (ValueError, TypeError):
        wpm = 200

    word_count_val = word_count(value)
    minutes = word_count_val / wpm
    return max(1, round(minutes))  # Минимум 1 минута


@register.simple_tag
def category_preview_sentences(category, device='desktop'):
    """
    🖥️📱 Умная генерация превью предложений в зависимости от устройства

    Args:
        category: объект категории
        device: 'desktop' или 'mobile'

    Returns:
        HTML превью с правильным количеством предложений
    """
    if not category.description:
        return ""

    # 📊 Количество предложений в зависимости от устройства
    sentences_count = 2 if device == 'mobile' else 3

    return smart_truncate_sentences(category.description, sentences_count)


@register.inclusion_tag('products/partials/category_content.html')
def render_category_content(category):
    """
    📄 Рендер полного контента категории через отдельный шаблон

    Args:
        category: объект категории

    Returns:
        Контекст для шаблона partials/category_content.html
    """
    return {
        'category': category,
        'has_description': bool(category.description),
        'has_additional_content': bool(category.additional_content),
        'has_video': has_youtube_video(category.additional_content) if category.additional_content else False,
        'total_words': word_count(category.description) + word_count(category.additional_content or ''),
        'reading_time': reading_time(category.description or '' + category.additional_content or ''),
    }

# 🔧 СОЗДАННЫЕ ФИЛЬТРЫ:
# ✅ smart_truncate_sentences - умное извлечение предложений с HTML
# ✅ mobile_truncate_sentences - мобильная версия с меньшим количеством
# ✅ close_unclosed_tags - закрытие незакрытых тегов после обрезки
# ✅ has_youtube_video - проверка наличия YouTube видео
# ✅ extract_text_content - извлечение чистого текста
# ✅ word_count - подсчет слов
# ✅ reading_time - время чтения контента
# ✅ category_preview_sentences - умное превью для разных устройств
# ✅ render_category_content - inclusion tag для полного контента