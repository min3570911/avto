# 📁 home/views.py - ФИНАЛЬНАЯ ВЕРСИЯ с CompanyDescription
# 🆕 ДОБАВЛЕНО: Получение описания компании для главной страницы
# ✅ СОХРАНЕНО: Все существующие функции без изменений

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from products.models import Product, Category, KitVariant, ProductImage
from boats.models import BoatCategory  # 🛥️ ДОБАВЛЕНО: импорт категорий лодок
from .models import FAQ, HeroSection, CompanyDescription, ContactInfo
import random


def index(request):
    """
    🏠 Главная страница - ФИНАЛЬНАЯ версия с описанием компании

    Структура главной страницы:
    - Hero-секция с видео и преимуществами
    - 📝 Описание компании (новое)
    - Компактный каталог категорий
    - Галерея примеров работ (неглавные фото товаров)
    - FAQ для аккордеона

    🆕 ДОБАВЛЕНО: Получение описания компании CompanyDescription
    """

    # 🎬 Получаем активную hero-секцию с преимуществами
    hero_section = None
    try:
        hero_section = HeroSection.objects.filter(is_active=True).prefetch_related('advantages').first()
    except HeroSection.DoesNotExist:
        pass  # 🔄 Будем отображать дефолтную секцию

    # 📝 Получаем описание компании (только одно)
    company_description = CompanyDescription.objects.first()

    # 📂 Получаем только активные категории для каталога
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'category_name')

    # 🛥️ Получаем активные категории лодок
    boat_categories = BoatCategory.objects.filter(is_active=True).order_by('display_order', 'category_name')

    # ❓ Получаем активные FAQ для аккордеона
    faqs = FAQ.objects.filter(is_active=True).order_by('order', 'created_at')

    # 📦 Комплектация "Салон" (для совместимости с существующим кодом)
    salon_kit = KitVariant.objects.filter(code='salon').first()

    # 🎲 Получаем случайные неглавные изображения для галереи
    gallery_images = get_random_product_gallery_images()

    # 📊 Контекст для шаблона
    context = {
        # 🎬 Hero-секция
        'hero_section': hero_section,

        # 📝 Описание компании
        'company_description': company_description,

        # 📂 Каталог категорий
        'categories': categories,
        'boat_categories': boat_categories,

        # ❓ FAQ для аккордеона
        'faqs': faqs,

        # 🎨 Галерея примеров работ
        'gallery_images': gallery_images,

        # 📦 Совместимость (для существующих элементов, если нужно)
        'salon_kit': salon_kit,

        # 📊 Дополнительная информация для шаблона
        'categories_count': categories.count(),
        'boat_categories_count': boat_categories.count(),
        'faqs_count': faqs.count(),
        'gallery_count': len(gallery_images),
    }

    return render(request, 'home/index.html', context)


def get_random_product_gallery_images(count=12):
    """
    🎲 Получает случайные неглавные изображения товаров для галереи

    Args:
        count (int): Количество изображений для галереи (по умолчанию 12)

    Returns:
        list: Список объектов ProductImage с дополнительной информацией о товаре

    🎯 Логика:
    1. Получаем все товары с изображениями и категориями
    2. Для каждого товара берем только неглавные изображения (пропускаем первое)
    3. Делаем случайную выборку из всех неглавных изображений
    4. Добавляем информацию о товаре к каждому изображению
    """

    # 📸 Получаем все неглавные изображения товаров
    all_secondary_images = []

    # 🔍 Получаем товары с изображениями и категориями (исключаем товары без категории)
    products_with_images = Product.objects.filter(
        category__isnull=False  # ✅ ИСПРАВЛЕНО: убрана фильтрация по is_active
    ).prefetch_related('product_images').select_related('category')

    for product in products_with_images:
        # 📱 Получаем все изображения товара
        product_images = list(product.product_images.all())

        # 🎯 Берем только неглавные изображения (пропускаем первое)
        if len(product_images) > 1:
            secondary_images = product_images[1:]  # Все кроме первого

            # 🏷️ Добавляем информацию о товаре к каждому изображению
            for image in secondary_images:
                # 📦 Расширяем объект изображения информацией о товаре
                image.product_name = product.product_name
                image.product_slug = product.slug
                image.product_category = product.category.category_name if product.category else "Автоковрики"
                all_secondary_images.append(image)

    # 🎲 Делаем случайную выборку
    if len(all_secondary_images) > count:
        selected_images = random.sample(all_secondary_images, count)
    else:
        # 📊 Если изображений меньше чем нужно, возвращаем все
        selected_images = all_secondary_images

    # 🔄 Перемешиваем для разнообразия
    random.shuffle(selected_images)

    return selected_images


# ✅ ВСЕ ОСТАЛЬНЫЕ ФУНКЦИИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ

def category_view(request, slug):
    """
    🛍️ Отображение страницы категории с товарами

    Args:
        request: HTTP-запрос
        slug: Слаг категории из URL

    Returns:
        Отрендеренный шаблон со списком товаров выбранной категории и описанием внизу
    """
    # Получаем категорию или возвращаем 404
    category = get_object_or_404(Category, slug=slug)

    # 🔧 ИСПРАВЛЕНО: Убран filter(parent=None)
    # Получаем все продукты этой категории
    products_query = Product.objects.filter(category=category)

    # Сортировка товаров (аналогично index view)
    sort_option = request.GET.get('sort')
    if sort_option == 'newest':
        products_query = products_query.filter(newest_product=True)
    elif sort_option == 'priceAsc':
        products_query = products_query.order_by('price')
    elif sort_option == 'priceDesc':
        products_query = products_query.order_by('-price')

    # Пагинация
    page = request.GET.get('page', 1)
    paginator = Paginator(products_query, 12)  # 12 товаров на странице
    products = paginator.get_page(page)

    # Получаем все категории для фильтра
    categories = Category.objects.all()

    # 🔄 Здесь можно добавить получение описания категории из базы данных или CMS
    # Например, если бы у модели Category было поле description:
    # category_description = category.description
    category_description = None  # Пока используем значение по умолчанию в шаблоне

    # Получаем комплектацию "Салон"
    salon_kit = KitVariant.objects.filter(code='salon').first()

    context = {
        'category': category,
        'products': products,
        'categories': categories,
        'selected_sort': sort_option,
        'category_description': category_description,
        'salon_kit': salon_kit,
    }

    return render(request, 'home/category.html', context)


# ВАЖНО: Здесь функция называется product_search в соответствии с urls.py
def product_search(request):
    """🔍 Поиск товаров по запросу"""
    query = request.GET.get('q', '')
    products = None

    if query:
        products = Product.objects.filter(product_name__icontains=query)

    context = {
        'query': query,
        'products': products,
    }

    return render(request, 'home/search.html', context)


def send_contact_telegram_notification(contact_message):
    """🤖 Отправляет уведомление о новом сообщении обратной связи в Telegram"""
    import requests
    import logging
    from django.conf import settings

    logger = logging.getLogger(__name__)

    try:
        # Получаем настройки из Django settings
        telegram_token = settings.TELEGRAM_BOT_TOKEN
        telegram_chat_id = settings.TELEGRAM_CHAT_ID

        # ⚠️ Проверяем наличие настроек
        if not telegram_token or not telegram_chat_id:
            logger.warning("⚠️ Telegram настройки отсутствуют. Добавьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env")
            return

        # 🔍 Проверяем что токен и чат ID не дефолтные
        if telegram_token == 'YOUR_TELEGRAM_BOT_TOKEN' or telegram_chat_id == 'YOUR_TELEGRAM_CHAT_ID':
            logger.warning("⚠️ Telegram настройки содержат заглушки. Обновите .env файл")
            return

        # 📝 Формируем красивое сообщение
        message = f"""📧 <b>НОВОЕ СООБЩЕНИЕ ОБРАТНОЙ СВЯЗИ</b>

👤 <b>Отправитель:</b> {contact_message.name}
📧 <b>Email:</b> {contact_message.email}"""

        # Добавляем телефон если указан
        if contact_message.phone:
            message += f"\n📞 <b>Телефон:</b> {contact_message.phone}"

        # Добавляем тему если указана
        if contact_message.subject:
            message += f"\n📝 <b>Тема:</b> {contact_message.subject}"

        # Добавляем текст сообщения
        message += f"""

💬 <b>Сообщение:</b>
{contact_message.message}

🕐 <b>Время:</b> {contact_message.created_at.strftime('%d.%m.%Y %H:%M')}
🔗 <b>ID:</b> {contact_message.uid}

<i>Ответить можно через админку: /admin/home/contactmessage/{contact_message.uid}/change/</i>"""

        # 🚀 Отправляем в Telegram
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

        data = {
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, json=data, timeout=10)

        if response.status_code == 200:
            logger.info(f"✅ Telegram уведомление отправлено для сообщения {contact_message.uid}")
        else:
            logger.error(f"❌ Ошибка отправки в Telegram: {response.status_code} - {response.text}")

    except Exception as e:
        logger.error(f"💥 Исключение при отправке в Telegram: {e}")


def contact(request):
    """📞 Страница контактов с формой обратной связи"""
    from .forms import ContactForm
    from django.contrib import messages

    # Получаем контактную информацию из модели с предзагрузкой телефонов
    contact_info = ContactInfo.objects.filter(is_active=True).prefetch_related('phone_numbers').first()

    if request.method == 'POST':
        # Обрабатываем отправку формы
        form = ContactForm(request.POST)

        if form.is_valid():
            # Сохраняем сообщение в базу данных
            contact_message = form.save()

            # Успешное сообщение пользователю
            messages.success(
                request,
                '✅ Ваше сообщение отправлено! Мы свяжемся с вами в ближайшее время.'
            )

            # 🤖 Отправляем уведомление в Telegram
            send_contact_telegram_notification(contact_message)

            # Перенаправляем на ту же страницу (POST-redirect-GET pattern)
            return redirect('contact')
        else:
            # Если форма содержит ошибки, показываем их
            messages.error(
                request,
                '❌ Пожалуйста, исправьте ошибки в форме.'
            )
    else:
        # GET запрос - показываем пустую форму
        form = ContactForm()

    context = {
        'contact_info': contact_info,
        'form': form,
    }

    return render(request, 'home/contact.html', context)


def about(request):
    """ℹ️ Страница о нас"""
    # 📝 МОЖНО ДОПОЛНИТЬ: Получение описания компании для страницы "О нас"
    company_description = CompanyDescription.objects.first()

    context = {
        'company_description': company_description,
    }

    return render(request, 'home/about.html', context)


def terms_and_conditions(request):
    """📋 Страница условий оплаты и доставки"""
    from .models import Terms

    # Получаем условия из базы данных
    terms = Terms.objects.first()

    context = {
        'terms': terms,
        'page_title': 'Условия оплаты и доставки'
    }

    return render(request, 'home/terms.html', context)


def privacy_policy(request):
    """🔒 Страница политики конфиденциальности"""
    from .models import PrivacyPolicy

    # Получаем политику из базы данных
    privacy_policy = PrivacyPolicy.objects.first()

    context = {
        'privacy_policy': privacy_policy,
        'page_title': 'Политика конфиденциальности'
    }

    return render(request, 'home/privacy.html', context)




def delivery(request):
    """🚚 Страница оплаты и доставки"""
    from .models import DeliveryOption

    queryset = DeliveryOption.objects.filter(is_active=True).order_by('order', 'title')
    delivery_options = list(queryset)

    coverage_labels_map = dict(DeliveryOption.COVERAGE_TAG_CHOICES)
    grouped_options = []

    for tag, label in DeliveryOption.COVERAGE_TAG_CHOICES:
        tagged = [option for option in delivery_options if option.coverage_tag == tag]
        if tagged:
            grouped_options.append({
                'tag': tag,
                'label': label,
                'options': tagged,
            })

    extra_tags = {
        option.coverage_tag: option.coverage_label() for option in delivery_options
        if option.coverage_tag not in coverage_labels_map
    }

    for tag, label in extra_tags.items():
        tagged = [option for option in delivery_options if option.coverage_tag == tag]
        grouped_options.append({
            'tag': tag,
            'label': label,
            'options': tagged,
        })

    payment_methods = sorted({
        payment_method
        for option in delivery_options
        for payment_method in option.payment_methods_list()
    })

    price_examples = []
    for option in delivery_options:
        if option.price_info and option.price_info not in price_examples:
            price_examples.append(option.price_info)
        if len(price_examples) >= 3:
            break

    delivery_time_examples = []
    for option in delivery_options:
        if option.delivery_time and option.delivery_time not in delivery_time_examples:
            delivery_time_examples.append(option.delivery_time)
        if len(delivery_time_examples) >= 3:
            break

    coverage_examples = [
        option.coverage_area for option in delivery_options if option.coverage_area
    ]

    last_updated = max(
        (option.updated_at for option in delivery_options),
        default=None
    )

    delivery_summary = {
        'options_count': len(delivery_options),
        'payment_methods': payment_methods,
        'price_examples': price_examples,
        'delivery_time_examples': delivery_time_examples,
        'coverage_examples': coverage_examples[:3],
        'coverage_labels': [group['label'] for group in grouped_options],
        'last_updated': last_updated,
    }

    context = {
        'delivery_options': delivery_options,
        'grouped_options': grouped_options,
        'delivery_summary': delivery_summary,
    }

    return render(request, 'home/delivery.html', context)


def auto_catalog(request):
    """🚗 Каталог автоковриков"""
    from products.models import AutoCatalogDescription

    auto_categories = Category.objects.filter(is_active=True).order_by('display_order', 'category_name')
    catalog_description = AutoCatalogDescription.objects.first()

    return render(request, 'home/auto_catalog.html', {
        'auto_categories': auto_categories,
        'catalog_description': catalog_description,
    })


def boat_catalog(request):
    """🛥️ Каталог лодочных ковриков"""
    from boats.models import BoatCatalogDescription

    boat_categories = BoatCategory.objects.filter(is_active=True).order_by('display_order', 'category_name')
    catalog_description = BoatCatalogDescription.objects.first()

    return render(request, 'home/boat_catalog.html', {
        'boat_categories': boat_categories,
        'catalog_description': catalog_description,
    })

# 🔧 ИТОГОВЫЕ ИЗМЕНЕНИЯ В ФАЙЛЕ:
#
# 🆕 В функции index():
#   ✅ ДОБАВЛЕНО: company_description = CompanyDescription.objects.first()
#   ✅ ДОБАВЛЕНО: 'company_description' в контекст шаблона
#   ✅ СОХРАНЕНО: все существующие данные (hero_section, categories, faqs, gallery_images)
#
# 🆕 В функции about():
#   ✅ ДОБАВЛЕНО: получение описания компании для страницы "О нас"
#   ✅ ЛОГИКА: можно использовать то же описание на разных страницах
#
# 📊 Новые поля в контексте:
#   - company_description: описание компании (только одно)
#
# 🎯 Особенности реализации:
#   ✅ Простое получение одного объекта через .first()
#   ✅ Безопасное использование - может быть None
#   ✅ Совместимость с существующим кодом
#   ✅ Возможность использования на других страницах (about)
