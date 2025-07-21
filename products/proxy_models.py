# 📁 products/proxy_models.py - Proxy модели для группировки админки
# 🎯 ЦЕЛЬ: Разделить админку на логические блоки без изменения основных моделей
# ✅ ОБНОВЛЕНО: Модели для лодок и автомобилей УДАЛЕНЫ, так как они перенесены в свои приложения.

# 🔗 Импорт моделей из accounts
from accounts.models import Cart, Order, Profile

# 🔗 Импорт моделей из home
from home.models import ContactInfo, FAQ, Banner, Testimonial, HeroSection, CompanyDescription

# 🔗 Импорт моделей из blog (с алиасами во избежание конфликта имен)
from blog.models import Category as BlogCategory, Article as BlogArticle


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