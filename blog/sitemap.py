# 📁 blog/sitemap.py
# 🗺️ Карта сайта для SEO оптимизации блога

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Article, Category


class ArticleSitemap(Sitemap):
    """📰 Карта сайта для статей"""
    changefreq = "weekly"
    priority = 0.8
    protocol = 'https'

    def items(self):
        """📋 Получаем все опубликованные статьи"""
        return Article.objects.filter(is_published=True).order_by('-published_at')

    def lastmod(self, obj):
        """📅 Дата последнего изменения"""
        return obj.updated_at

    def location(self, obj):
        """🔗 URL статьи"""
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    """📂 Карта сайта для категорий"""
    changefreq = "weekly"
    priority = 0.6
    protocol = 'https'

    def items(self):
        """📋 Все категории"""
        return Category.objects.all()

    def location(self, obj):
        """🔗 URL категории"""
        return obj.get_absolute_url()


class BlogStaticSitemap(Sitemap):
    """📄 Статические страницы блога"""
    changefreq = "daily"
    priority = 0.7
    protocol = 'https'

    def items(self):
        """📋 Список статических страниц"""
        return ['blog:article_list']

    def location(self, item):
        """🔗 URL страницы"""
        return reverse(item)


# 🗺️ Объединенная карта сайта для блога
blog_sitemaps = {
    'articles': ArticleSitemap,
    'categories': CategorySitemap,
    'blog_static': BlogStaticSitemap,
}

# 📝 Добавьте в основной urls.py:
# from django.contrib.sitemaps.views import sitemap
# from blog.sitemap import blog_sitemaps
#
# sitemaps = {
#     **blog_sitemaps,
#     # другие карты сайта
# }
#
# urlpatterns = [
#     path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
# ]