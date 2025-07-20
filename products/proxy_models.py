# 📁 products/proxy_models.py - Proxy модели для группировки админки
# 🎯 ЦЕЛЬ: Разделить админку на логические блоки без изменения основных моделей
# ✅ БЕЗОПАСНО: Не изменяет существующие модели и логику
# 🔍 ИЗУЧЕН ПРОЕКТ: Все импорты проверены и соответствуют реальным моделям

# 🔗 Импорт моделей из products
from .models import Category, Product

# 🔗 Импорт моделей из accounts
from accounts.models import Cart, Order, Profile

# 🔗 Импорт моделей из home
from home.models import ContactInfo, FAQ, Banner, Testimonial, HeroSection, CompanyDescription

# 🔗 Импорт моделей из blog (с алиасами во избежание конфликта имен)
from blog.models import Category as BlogCategory, Article as BlogArticle


# 📦 ТОВАРЫ И КАТАЛОГ - Группа 1: ЛОДКИ 🛥️

class CategoryBoats(Category):
    """🛥️ Proxy модель для категорий лодок"""

    class Meta:
        proxy = True
        verbose_name = '🛥️ Категория лодок'
        verbose_name_plural = '🛥️ Категории лодок'


class ProductBoats(Product):
    """🛥️ Proxy модель для товаров лодок"""

    class Meta:
        proxy = True
        verbose_name = '🛥️ Товар лодок'
        verbose_name_plural = '🛥️ Товары лодок'


# 📦 ТОВАРЫ И КАТАЛОГ - Группа 2: АВТОМОБИЛИ 🚗

class CategoryCars(Category):
    """🚗 Proxy модель для категорий автомобилей"""

    class Meta:
        proxy = True
        verbose_name = '🚗 Категория автомобилей'
        verbose_name_plural = '🚗 Категории автомобилей'


class ProductCars(Product):
    """🚗 Proxy модель для товаров автомобилей"""

    class Meta:
        proxy = True
        verbose_name = '🚗 Товар автомобилей'
        verbose_name_plural = '🚗 Товары автомобилей'


# 💼 ПРОДАЖИ И ЗАКАЗЫ - Группа 3: SALES 💰

class SalesCart(Cart):
    """🛒 Proxy модель для корзин в разделе продаж"""

    class Meta:
        proxy = True
        verbose_name = '🛒 Корзина'
        verbose_name_plural = '🛒 Корзины'


class SalesOrder(Order):
    """📦 Proxy модель для заказов в разделе продаж"""

    class Meta:
        proxy = True
        verbose_name = '📦 Заказ'
        verbose_name_plural = '📦 Заказы'


class SalesProfile(Profile):
    """👤 Proxy модель для профилей в разделе продаж"""

    class Meta:
        proxy = True
        verbose_name = '👤 Профиль пользователя'
        verbose_name_plural = '👤 Профили пользователей'


# 🌐 КОНТЕНТ САЙТА - Группа 4: ГЛАВНАЯ СТРАНИЦА 🏠

class ContentContactInfo(ContactInfo):
    """📞 Proxy модель для контактов в разделе контента"""

    class Meta:
        proxy = True
        verbose_name = '📞 Контактная информация'
        verbose_name_plural = '📞 Контактная информация'


class ContentFAQ(FAQ):
    """❓ Proxy модель для FAQ в разделе контента"""

    class Meta:
        proxy = True
        verbose_name = '❓ Частый вопрос'
        verbose_name_plural = '❓ Частые вопросы'


class ContentBanner(Banner):
    """🎨 Proxy модель для баннеров в разделе контента"""

    class Meta:
        proxy = True
        verbose_name = '🎨 Баннер'
        verbose_name_plural = '🎨 Баннеры'


class ContentTestimonial(Testimonial):
    """💬 Proxy модель для отзывов в разделе контента"""

    class Meta:
        proxy = True
        verbose_name = '💬 Отзыв клиента'
        verbose_name_plural = '💬 Отзывы клиентов'


class ContentHeroSection(HeroSection):
    """🎬 Proxy модель для hero-секции в разделе контента"""

    class Meta:
        proxy = True
        verbose_name = '🎬 Hero-секция'
        verbose_name_plural = '🎬 Hero-секции'


class ContentCompanyDescription(CompanyDescription):
    """📝 Proxy модель для описания компании в разделе контента"""

    class Meta:
        proxy = True
        verbose_name = '📝 Описание компании'
        verbose_name_plural = '📝 Описание компании'


# 🌐 КОНТЕНТ САЙТА - Группа 5: БЛОГ 📝

class ContentBlogCategory(BlogCategory):
    """📂 Proxy модель для категорий блога в разделе контента"""

    class Meta:
        proxy = True
        verbose_name = '📂 Категория статьи'
        verbose_name_plural = '📂 Категории статей'


class ContentBlogArticle(BlogArticle):
    """📝 Proxy модель для статей блога в разделе контента"""

    class Meta:
        proxy = True
        verbose_name = '📝 Статья'
        verbose_name_plural = '📝 Статьи'

# 🎯 ИТОГОВАЯ СТРУКТУРА АДМИНКИ:
#
# 📦 PRODUCTS (обновленная структура)
# ├── 🛥️ Категории лодок (CategoryBoats) - только category_type='boats'
# ├── 🛥️ Товары лодок (ProductBoats) - только товары из категорий лодок
# ├── 🚗 Категории автомобилей (CategoryCars) - только category_type='cars'
# ├── 🚗 Товары автомобилей (ProductCars) - только товары из категорий авто
# ├── Типы комплектаций (KitVariant) - остается как есть
# └── Цвета (Color) - остается как есть
#
# Остальные приложения остаются без изменений:
# - ACCOUNTS, HOME, BLOG - как были
# - Группировка происходит через эмоджи в названиях
# - Фильтрация через get_queryset() в админках
#
# ✅ ПРЕИМУЩЕСТВА:
# - Логическое разделение товаров по типам
# - Удобная навигация через эмоджи
# - Сохранение всей существующей функциональности
# - Нет ошибок с app_label
# - Не ломает существующий код
# - Все импорты проверены и корректны
#
# 🔍 ИСПРАВЛЕНО:
# - Убраны app_label (причина ошибки)
# - Добавлены эмоджи для визуальной группировки
# - Используются только стандартные Django возможности
# - Все ссылки на несуществующие приложения удалены