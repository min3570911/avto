# 📁 common/utils.py
# 🛡️ АНТИ-СПАМ УТИЛИТЫ и защита от автоматических отзывов
# 🎯 ФУНКЦИИ: анализ текста, IP репутация, временные ограничения, валидация
# 📊 СТАТИСТИКА: сбор метрик для улучшения защиты

import re
import time
import hashlib
import ipaddress
from collections import Counter
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User

import logging
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


# ==================== УНИВЕРСАЛЬНЫЕ ФУНКЦИИ ДЛЯ ТОВАРОВ ====================

def get_product_by_review(review):
    """
    🎯 Универсальная функция для получения товара по отзыву
    Работает и с автомобилями (Product) и с лодками (BoatProduct)

    Args:
        review: объект ProductReview

    Returns:
        tuple: (product_object, product_type, product_url_prefix, images_field)

    Примеры:
        - Для автомобилей: (product, 'product', '/products/', 'product_images')
        - Для лодок: (boat_product, 'boat', '/boats/product/', 'images')
    """
    try:
        if review.content_type.model == 'product':
            # 🚗 Автомобильные коврики
            from products.models import Product
            product = Product.objects.select_related('category').prefetch_related('product_images').get(uid=review.object_id)
            return product, 'product', '/products/', 'product_images'

        elif review.content_type.model == 'boatproduct':
            # 🛥️ Лодочные коврики
            from boats.models import BoatProduct
            product = BoatProduct.objects.select_related('category').prefetch_related('images').get(uid=review.object_id)
            return product, 'boat', '/boats/product/', 'images'

        else:
            logger.warning(f"Неизвестный тип товара: {review.content_type.model}")
            return None, None, None, None

    except Exception as e:
        logger.error(f"Ошибка получения товара для отзыва {review.uid}: {e}")
        return None, None, None, None


def get_product_images(product, product_type):
    """
    🖼️ Универсальная функция для получения картинок товара

    Args:
        product: объект Product или BoatProduct
        product_type: 'product' или 'boat'

    Returns:
        QuerySet: картинки товара
    """
    if not product:
        return None

    try:
        if product_type == 'product':
            return product.product_images.all()
        elif product_type == 'boat':
            return product.images.all()
        else:
            return None
    except Exception:
        return None


def get_product_url(product, product_type):
    """
    🔗 Универсальная функция для получения URL товара

    Args:
        product: объект Product или BoatProduct
        product_type: 'product' или 'boat'

    Returns:
        str: URL страницы товара
    """
    if not product or not hasattr(product, 'slug'):
        return '#'

    if product_type == 'product':
        return f'/products/{product.slug}/'
    elif product_type == 'boat':
        return f'/boats/product/{product.slug}/'
    else:
        return '#'

# ==================== КОНСТАНТЫ И НАСТРОЙКИ ====================

# 🚫 Списки спам-слов (можно вынести в settings.py)
DEFAULT_SPAM_WORDS = [
    # Коммерческие
    'casino', 'gambling', 'bet', 'poker', 'loan', 'credit', 'debt', 'money',
    'buy now', 'discount', 'sale', 'cheap', 'free shipping', 'limited offer',

    # Взрослый контент
    'porn', 'xxx', 'sex', 'adult', 'dating', 'webcam', 'escort',

    # Медицинские
    'viagra', 'cialis', 'weight loss', 'diet pills', 'miracle cure',

    # Технические спам-индикаторы
    'click here', 'visit now', 'act now', 'limited time', 'guaranteed',

    # Русские спам-слова
    'казино', 'ставки', 'кредит', 'займ', 'заработок', 'доход', 'инвестиции',
    'похудение', 'диета', 'секс', 'знакомства', 'эскорт',
]

DEFAULT_SUSPICIOUS_DOMAINS = [
    'tempmail.', 'guerrillamail.', '10minutemail.', 'mailinator.',
    'trashmail.', 'sharklasers.', 'grr.la', 'maildrop.',
]

DEFAULT_BLOCKED_IPS = [
    # Можно добавить известные прокси и VPN
    '127.0.0.1',  # Localhost для тестирования
]


def get_spam_config():
    """⚙️ Получение конфигурации анти-спам защиты"""
    return getattr(settings, 'SPAM_DETECTION', {
        'SPAM_WORDS': DEFAULT_SPAM_WORDS,
        'SUSPICIOUS_DOMAINS': DEFAULT_SUSPICIOUS_DOMAINS,
        'BLOCKED_IPS': DEFAULT_BLOCKED_IPS,
        'SPAM_SCORE_THRESHOLD': 70.0,
        'SUSPICIOUS_THRESHOLD': 50.0,
        'MIN_FORM_FILL_TIME': 3.0,  # секунд
        'MAX_REVIEWS_PER_HOUR': 3,  # для анонимных
        'MAX_REVIEWS_PER_HOUR_AUTH': 5,  # для авторизованных
        'ENABLE_IP_CHECKING': True,
        'ENABLE_TEXT_ANALYSIS': True,
        'ENABLE_SIMILARITY_CHECK': True,
        'SIMILARITY_THRESHOLD': 0.85,  # 85% схожести = подозрительно
    })


# ==================== АНАЛИЗ ТЕКСТА НА СПАМ ====================

def check_spam_words(text: str, custom_words: List[str] = None) -> Dict:
    """
    🔍 Проверка текста на наличие спам-слов

    Args:
        text: Анализируемый текст
        custom_words: Дополнительные спам-слова

    Returns:
        dict: {'score': float, 'found_words': list, 'details': dict}
    """
    config = get_spam_config()
    spam_words = config['SPAM_WORDS']

    if custom_words:
        spam_words.extend(custom_words)

    text_lower = text.lower()
    found_words = []
    word_scores = {}

    for word in spam_words:
        if word.lower() in text_lower:
            found_words.append(word)
            # Разные веса для разных типов спам-слов
            if word in ['casino', 'gambling', 'porn', 'xxx']:
                weight = 25.0  # Высокий вес
            elif word in ['free', 'discount', 'cheap']:
                weight = 15.0  # Средний вес
            else:
                weight = 10.0  # Низкий вес

            word_scores[word] = weight

    total_score = sum(word_scores.values())

    return {
        'score': min(total_score, 100.0),  # Максимум 100
        'found_words': found_words,
        'word_scores': word_scores,
        'details': {
            'total_words_checked': len(spam_words),
            'found_count': len(found_words)
        }
    }


def analyze_text_quality(text: str) -> Dict:
    """
    📊 Анализ качества текста отзыва

    Args:
        text: Анализируемый текст

    Returns:
        dict: Различные метрики качества текста
    """
    if not text:
        return {'score': 100.0, 'issues': ['empty_text']}

    issues = []
    score = 0.0

    # Длина текста
    length = len(text.strip())
    if length < 10:
        score += 30.0
        issues.append('too_short')
    elif length > 2000:
        score += 20.0
        issues.append('too_long')

    # Повторяющиеся символы
    if re.search(r'(.)\1{4,}', text):  # 5+ одинаковых символов
        score += 25.0
        issues.append('repeated_chars')

    # Слишком много заглавных букв
    upper_ratio = sum(1 for c in text if c.isupper()) / len(text)
    if upper_ratio > 0.5:
        score += 20.0
        issues.append('too_many_caps')

    # URL и email в тексте
    if re.search(r'https?://|www\.|\.[a-z]{2,4}(?:\s|$)', text.lower()):
        score += 30.0
        issues.append('contains_urls')

    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
        score += 25.0
        issues.append('contains_email')

    # Странные символы или кодировка
    weird_chars = re.findall(r'[^\w\s\-.,!?()«»""\'@#№$%&*+=/\\|<>[\]{}~`^]', text)
    if len(weird_chars) > 3:
        score += 15.0
        issues.append('weird_characters')

    # Соотношение букв к цифрам
    letters = sum(1 for c in text if c.isalpha())
    digits = sum(1 for c in text if c.isdigit())
    if letters > 0 and (digits / letters) > 0.3:
        score += 10.0
        issues.append('too_many_numbers')

    return {
        'score': min(score, 100.0),
        'issues': issues,
        'stats': {
            'length': length,
            'upper_ratio': round(upper_ratio, 2),
            'digits_count': digits,
            'letters_count': letters,
            'weird_chars_count': len(weird_chars)
        }
    }


def check_text_similarity(new_text: str, existing_texts: List[str], threshold: float = 0.85) -> Dict:
    """
    🔄 Проверка схожести текста с существующими отзывами

    Args:
        new_text: Новый текст для проверки
        existing_texts: Список существующих текстов для сравнения
        threshold: Порог схожести (0-1)

    Returns:
        dict: Результаты анализа схожести
    """
    if not new_text or not existing_texts:
        return {'score': 0.0, 'similar_texts': [], 'max_similarity': 0.0}

    similarities = []
    similar_texts = []

    new_text_clean = re.sub(r'\s+', ' ', new_text.lower().strip())

    for existing_text in existing_texts:
        if not existing_text:
            continue

        existing_clean = re.sub(r'\s+', ' ', existing_text.lower().strip())
        similarity = SequenceMatcher(None, new_text_clean, existing_clean).ratio()

        similarities.append(similarity)

        if similarity >= threshold:
            similar_texts.append({
                'text': existing_text[:100] + '...' if len(existing_text) > 100 else existing_text,
                'similarity': round(similarity, 3)
            })

    max_similarity = max(similarities) if similarities else 0.0

    # Оценка: чем больше схожесть, тем выше спам-score
    score = 0.0
    if max_similarity >= 0.95:
        score = 80.0  # Почти идентичный текст
    elif max_similarity >= 0.85:
        score = 60.0  # Очень похожий
    elif max_similarity >= 0.70:
        score = 30.0  # Похожий
    elif max_similarity >= 0.50:
        score = 15.0  # Частично похожий

    return {
        'score': score,
        'max_similarity': round(max_similarity, 3),
        'similar_texts': similar_texts,
        'similarities_count': len([s for s in similarities if s >= threshold])
    }


# ==================== IP АДРЕСА И СЕТЕВАЯ БЕЗОПАСНОСТЬ ====================

def is_ip_blocked(ip_address: str) -> bool:
    """
    🚫 Проверка IP адреса на блокировку

    Args:
        ip_address: IP адрес для проверки

    Returns:
        bool: True если IP заблокирован
    """
    if not ip_address:
        return False

    config = get_spam_config()
    blocked_ips = config.get('BLOCKED_IPS', [])

    try:
        ip = ipaddress.ip_address(ip_address)

        # Проверяем прямое совпадение
        if ip_address in blocked_ips:
            return True

        # Проверяем подсети
        for blocked_ip in blocked_ips:
            try:
                if '/' in blocked_ip:  # Это подсеть
                    if ip in ipaddress.ip_network(blocked_ip, strict=False):
                        return True
            except ValueError:
                continue

        return False

    except ValueError:
        # Некорректный IP
        logger.warning(f"Invalid IP address format: {ip_address}")
        return True  # Блокируем некорректные IP


def analyze_ip_reputation(ip_address: str) -> Dict:
    """
    🔍 Анализ репутации IP адреса

    Args:
        ip_address: IP адрес для анализа

    Returns:
        dict: Результаты анализа репутации
    """
    if not ip_address:
        return {'score': 0.0, 'issues': ['no_ip'], 'reputation': 'unknown'}

    issues = []
    score = 0.0
    reputation = 'good'

    try:
        ip = ipaddress.ip_address(ip_address)

        # Проверяем на приватные/локальные адреса
        if ip.is_private:
            score += 5.0
            issues.append('private_ip')

        if ip.is_loopback:
            score += 20.0
            issues.append('loopback_ip')

        if ip.is_reserved:
            score += 15.0
            issues.append('reserved_ip')

        # Проверяем на известные прокси/VPN диапазоны
        # Это упрощенная проверка, в реальности нужна база данных IP репутации
        suspicious_ranges = [
            '10.0.0.0/8',  # Приватная сеть
            '172.16.0.0/12',  # Приватная сеть
            '192.168.0.0/16',  # Приватная сеть
        ]

        for range_ip in suspicious_ranges:
            try:
                if ip in ipaddress.ip_network(range_ip):
                    score += 10.0
                    issues.append(f'in_range_{range_ip}')
            except ValueError:
                continue

        # Определяем итоговую репутацию
        if score >= 30:
            reputation = 'bad'
        elif score >= 15:
            reputation = 'suspicious'
        elif score >= 5:
            reputation = 'questionable'

    except ValueError:
        score = 50.0
        issues.append('invalid_ip_format')
        reputation = 'bad'
        logger.warning(f"Invalid IP address for reputation check: {ip_address}")

    return {
        'score': min(score, 100.0),
        'issues': issues,
        'reputation': reputation,
        'ip': ip_address
    }


# ==================== RATE LIMITING И ВРЕМЕННЫЕ ОГРАНИЧЕНИЯ ====================

def check_rate_limit(ip_address: str, user: Optional[User] = None) -> Dict:
    """
    ⏱️ Проверка ограничений по частоте отправки отзывов

    Args:
        ip_address: IP адрес отправителя
        user: Пользователь (если авторизован)

    Returns:
        dict: Результат проверки лимитов
    """
    config = get_spam_config()

    if user and user.is_authenticated:
        limit = config.get('MAX_REVIEWS_PER_HOUR_AUTH', 5)
        cache_key = f'review_limit_user_{user.id}'
        identifier = f'user_{user.id}'
    else:
        limit = config.get('MAX_REVIEWS_PER_HOUR', 3)
        cache_key = f'review_limit_ip_{ip_address}'
        identifier = f'ip_{ip_address}'

    # Получаем текущий счетчик
    current_count = cache.get(cache_key, 0)

    is_exceeded = current_count >= limit
    remaining = max(0, limit - current_count)

    # Время до сброса лимита
    ttl = cache.ttl(cache_key)
    if ttl is None or ttl < 0:
        ttl = 3600  # 1 час по умолчанию

    return {
        'is_exceeded': is_exceeded,
        'current_count': current_count,
        'limit': limit,
        'remaining': remaining,
        'reset_in_seconds': ttl,
        'identifier': identifier,
        'cache_key': cache_key
    }


def increment_rate_limit(ip_address: str, user: Optional[User] = None) -> bool:
    """
    📈 Увеличение счетчика отзывов для rate limiting

    Args:
        ip_address: IP адрес отправителя
        user: Пользователь (если авторизован)

    Returns:
        bool: True если лимит не превышен после увеличения
    """
    rate_limit_result = check_rate_limit(ip_address, user)

    if rate_limit_result['is_exceeded']:
        return False

    cache_key = rate_limit_result['cache_key']
    current_count = rate_limit_result['current_count']

    # Устанавливаем счетчик на час
    cache.set(cache_key, current_count + 1, 3600)

    logger.info(f"Rate limit incremented for {rate_limit_result['identifier']}: {current_count + 1}")

    return True


def check_form_timing(form_load_time: float) -> Dict:
    """
    ⏱️ Проверка времени заполнения формы

    Args:
        form_load_time: Время загрузки формы (timestamp)

    Returns:
        dict: Результат анализа времени
    """
    config = get_spam_config()
    min_time = config.get('MIN_FORM_FILL_TIME', 3.0)

    if not form_load_time:
        return {
            'score': 20.0,
            'issues': ['no_timing_data'],
            'fill_time': None,
            'is_too_fast': True
        }

    current_time = time.time()
    fill_time = current_time - form_load_time

    issues = []
    score = 0.0

    if fill_time < min_time:
        score = 40.0
        issues.append('too_fast')
        is_too_fast = True
    elif fill_time < 1.0:
        score = 60.0
        issues.append('extremely_fast')
        is_too_fast = True
    elif fill_time > 3600:  # Больше часа
        score = 10.0
        issues.append('too_long')
        is_too_fast = False
    else:
        is_too_fast = False

    return {
        'score': score,
        'issues': issues,
        'fill_time': round(fill_time, 2),
        'is_too_fast': is_too_fast,
        'min_required_time': min_time
    }


# ==================== ОБЩИЙ АНАЛИЗ СПАМА ====================

def calculate_spam_score(review_data: Dict) -> float:
    """
    🎯 Комплексный расчет спам-оценки отзыва

    Args:
        review_data: Данные отзыва для анализа
        {
            'content': str,
            'ip_address': str,
            'form_submit_time': float,
            'user_agent': str,
            'reviewer_name': str (optional),
            'existing_reviews': List[str] (optional)
        }

    Returns:
        float: Спам-оценка от 0 до 100
    """
    config = get_spam_config()

    if not config.get('ENABLE_TEXT_ANALYSIS', True):
        return 0.0

    total_score = 0.0
    weights = {
        'spam_words': 0.3,  # 30%
        'text_quality': 0.25,  # 25%
        'ip_reputation': 0.2,  # 20%
        'timing': 0.15,  # 15%
        'similarity': 0.1  # 10%
    }

    # 1. Анализ спам-слов
    content = review_data.get('content', '')
    if content:
        spam_result = check_spam_words(content)
        total_score += spam_result['score'] * weights['spam_words']

        # Анализ качества текста
        quality_result = analyze_text_quality(content)
        total_score += quality_result['score'] * weights['text_quality']

    # 2. IP репутация
    ip_address = review_data.get('ip_address')
    if ip_address and config.get('ENABLE_IP_CHECKING', True):
        ip_result = analyze_ip_reputation(ip_address)
        total_score += ip_result['score'] * weights['ip_reputation']

    # 3. Время заполнения формы
    form_submit_time = review_data.get('form_submit_time')
    if form_submit_time:
        timing_result = check_form_timing(form_submit_time)
        total_score += timing_result['score'] * weights['timing']

    # 4. Проверка схожести с существующими отзывами
    existing_reviews = review_data.get('existing_reviews', [])
    if existing_reviews and config.get('ENABLE_SIMILARITY_CHECK', True):
        similarity_result = check_text_similarity(content, existing_reviews)
        total_score += similarity_result['score'] * weights['similarity']

    return min(round(total_score, 2), 100.0)


def is_review_suspicious(review_data: Dict) -> Tuple[bool, Dict]:
    """
    🚨 Определение подозрительности отзыва

    Args:
        review_data: Данные отзыва

    Returns:
        Tuple[bool, Dict]: (is_suspicious, analysis_details)
    """
    spam_score = calculate_spam_score(review_data)
    config = get_spam_config()
    threshold = config.get('SUSPICIOUS_THRESHOLD', 50.0)

    is_suspicious = spam_score >= threshold

    analysis = {
        'spam_score': spam_score,
        'threshold': threshold,
        'is_suspicious': is_suspicious,
        'recommendation': 'block' if spam_score >= 80 else 'review' if is_suspicious else 'allow'
    }

    return is_suspicious, analysis


# ==================== СТАТИСТИКА И МОНИТОРИНГ ====================

def log_spam_detection(review_data: Dict, result: Dict):
    """
    📊 Логирование результатов анти-спам проверки

    Args:
        review_data: Данные отзыва
        result: Результаты анализа
    """
    log_data = {
        'timestamp': timezone.now().isoformat(),
        'ip_address': review_data.get('ip_address'),
        'user_agent': review_data.get('user_agent', '')[:200],  # Ограничиваем длину
        'content_length': len(review_data.get('content', '')),
        'spam_score': result.get('spam_score', 0),
        'is_suspicious': result.get('is_suspicious', False),
        'recommendation': result.get('recommendation', 'unknown')
    }

    logger.info(f"Spam detection result: {log_data}")

    # Кэшируем статистику на час
    stats_key = 'spam_detection_hourly_stats'
    stats = cache.get(stats_key, {
        'total_checks': 0,
        'suspicious_count': 0,
        'blocked_count': 0,
        'avg_score': 0
    })

    stats['total_checks'] += 1
    if result.get('is_suspicious'):
        stats['suspicious_count'] += 1
    if result.get('recommendation') == 'block':
        stats['blocked_count'] += 1

    # Обновляем средний score
    current_avg = stats.get('avg_score', 0)
    new_score = result.get('spam_score', 0)
    stats['avg_score'] = round((current_avg * (stats['total_checks'] - 1) + new_score) / stats['total_checks'], 2)

    cache.set(stats_key, stats, 3600)


def get_spam_statistics() -> Dict:
    """
    📊 Получение статистики анти-спам защиты

    Returns:
        dict: Статистика за последний час
    """
    stats_key = 'spam_detection_hourly_stats'
    stats = cache.get(stats_key, {
        'total_checks': 0,
        'suspicious_count': 0,
        'blocked_count': 0,
        'avg_score': 0
    })

    if stats['total_checks'] > 0:
        stats['suspicious_rate'] = round((stats['suspicious_count'] / stats['total_checks']) * 100, 1)
        stats['block_rate'] = round((stats['blocked_count'] / stats['total_checks']) * 100, 1)
    else:
        stats['suspicious_rate'] = 0
        stats['block_rate'] = 0

    return stats


# ==================== УТИЛИТЫ ОЧИСТКИ И ОБСЛУЖИВАНИЯ ====================

def clean_old_rate_limits():
    """
    🧹 Очистка устаревших записей rate limiting

    Эта функция может вызываться периодически через cron или Celery
    """
    # Django cache автоматически удаляет истекшие записи,
    # но можно добавить дополнительную логику если нужно
    pass


def reset_user_rate_limit(user_id: int = None, ip_address: str = None):
    """
    🔄 Сброс лимитов для конкретного пользователя или IP

    Args:
        user_id: ID пользователя
        ip_address: IP адрес
    """
    if user_id:
        cache_key = f'review_limit_user_{user_id}'
        cache.delete(cache_key)
        logger.info(f"Rate limit reset for user {user_id}")

    if ip_address:
        cache_key = f'review_limit_ip_{ip_address}'
        cache.delete(cache_key)
        logger.info(f"Rate limit reset for IP {ip_address}")


# ==================== ТЕСТОВЫЕ ФУНКЦИИ ====================

def test_spam_detection():
    """
    🧪 Тестирование системы анти-спам защиты

    Используется для проверки работоспособности алгоритмов
    """
    test_cases = [
        {
            'name': 'Normal review',
            'data': {
                'content': 'Отличный коврик, качество супер! Рекомендую всем.',
                'ip_address': '192.168.1.100',
                'form_submit_time': time.time() - 30,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        },
        {
            'name': 'Spam review',
            'data': {
                'content': 'Buy cheap casino gambling poker free money loan click here now!!!',
                'ip_address': '127.0.0.1',
                'form_submit_time': time.time() - 1,  # Слишком быстро
                'user_agent': 'Bot/1.0'
            }
        }
    ]

    results = []
    for test_case in test_cases:
        spam_score = calculate_spam_score(test_case['data'])
        is_suspicious, analysis = is_review_suspicious(test_case['data'])

        results.append({
            'name': test_case['name'],
            'spam_score': spam_score,
            'is_suspicious': is_suspicious,
            'analysis': analysis
        })

    return results