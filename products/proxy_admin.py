# 📁 products/proxy_admin.py - Админки для бизнес-группировки (Jazzmin)
# ✅ ОБНОВЛЕНО: Админки для лодок и автомобилей УДАЛЕНЫ, так как они перенесены в свои приложения.

from django.contrib import admin
from .proxy_models import (
    SalesCart, SalesOrder, SalesProfile,
    ContentContactInfo, ContentFAQ, ContentBanner,
    ContentTestimonial, ContentHeroSection, ContentCompanyDescription,
    ContentBlogCategory, ContentBlogArticle
)
from accounts.admin import CartAdmin, OrderAdmin, ProfileAdmin
from home.admin import (
    ContactInfoAdmin, FAQAdmin, BannerAdmin,
    TestimonialAdmin, HeroSectionAdmin, CompanyDescriptionAdmin
)
from blog.admin import CategoryAdmin as BlogCategoryAdmin, ArticleAdmin as BlogArticleAdmin


# 💼 ПРОДАЖИ И ЗАКАЗЫ - Группа 3: SALES 💰

@admin.register(SalesCart)
class SalesCartAdmin(CartAdmin):
    """🛒 Админка корзин в разделе продаж - наследует всю функциональность CartAdmin"""
    pass

@admin.register(SalesOrder)
class SalesOrderAdmin(OrderAdmin):
    """📦 Админка заказов в разделе продаж - наследует всю функциональность OrderAdmin"""
    pass

@admin.register(SalesProfile)
class SalesProfileAdmin(ProfileAdmin):
    """👤 Админка профилей в разделе продаж - наследует всю функциональность ProfileAdmin"""
    pass


# 🌐 КОНТЕНТ САЙТА - Группа 4: ГЛАВНАЯ СТРАНИЦА 🏠

@admin.register(ContentContactInfo)
class ContentContactInfoAdmin(ContactInfoAdmin):
    """📞 Админка контактов в разделе контента - наследует всю функциональность ContactInfoAdmin"""
    pass

@admin.register(ContentFAQ)
class ContentFAQAdmin(FAQAdmin):
    """❓ Админка FAQ в разделе контента - наследует всю функциональность FAQAdmin"""
    pass

@admin.register(ContentBanner)
class ContentBannerAdmin(BannerAdmin):
    """🎨 Админка баннеров в разделе контента - наследует всю функциональность BannerAdmin"""
    pass

@admin.register(ContentTestimonial)
class ContentTestimonialAdmin(TestimonialAdmin):
    """💬 Админка отзывов в разделе контента - наследует всю функциональность TestimonialAdmin"""
    pass

@admin.register(ContentHeroSection)
class ContentHeroSectionAdmin(HeroSectionAdmin):
    """🎬 Админка hero-секции в разделе контента - наследует всю функциональность HeroSectionAdmin"""
    pass

@admin.register(ContentCompanyDescription)
class ContentCompanyDescriptionAdmin(CompanyDescriptionAdmin):
    """📝 Админка описания компании в разделе контента - наследует всю функциональность CompanyDescriptionAdmin"""
    pass


# 🌐 КОНТЕНТ САЙТА - Группа 5: БЛОГ 📝

@admin.register(ContentBlogCategory)
class ContentBlogCategoryAdmin(BlogCategoryAdmin):
    """📂 Админка категорий блога в разделе контента - наследует всю функциональность CategoryAdmin"""
    pass

@admin.register(ContentBlogArticle)
class ContentBlogArticleAdmin(BlogArticleAdmin):
    """📝 Админка статей блога в разделе контента - наследует всю функциональность ArticleAdmin"""
    pass