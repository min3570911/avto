# 📁 blog/views.py - Views для раздела "Статьи"
# 🎯 Class-Based Views для отображения статей

from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import F
from django.utils import timezone
from .models import Article, Category


class ArticleListView(ListView):
    """📰 Главная страница блога - список всех статей"""
    model = Article
    template_name = 'blog/article_list.html'
    context_object_name = 'articles'
    paginate_by = 6  # 📄 6 статей на страницу

    def get_queryset(self):
        """🔍 Получаем только опубликованные статьи"""
        return Article.objects.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).select_related('category', 'author').order_by('-published_at')

    def get_context_data(self, **kwargs):
        """📊 Добавляем дополнительный контекст"""
        context = super().get_context_data(**kwargs)
        # 📂 Все категории для сайдбара
        context['categories'] = Category.objects.all().order_by('sort_order', 'name')
        # 🏷️ Метаданные для SEO
        context['page_title'] = 'Полезные статьи об автоковриках'
        context[
            'page_description'] = 'Советы по выбору, установке и уходу за автомобильными ковриками. Экспертные рекомендации и обзоры.'
        return context


class CategoryArticlesView(ListView):
    """📂 Список статей в конкретной категории"""
    model = Article
    template_name = 'blog/category_articles.html'
    context_object_name = 'articles'
    paginate_by = 6

    def get_queryset(self):
        """🔍 Фильтруем статьи по категории"""
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Article.objects.filter(
            category=self.category,
            is_published=True,
            published_at__lte=timezone.now()
        ).select_related('author').order_by('-published_at')

    def get_context_data(self, **kwargs):
        """📊 Контекст с информацией о категории"""
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.all().order_by('sort_order', 'name')
        # 🏷️ SEO метаданные
        context['page_title'] = f'{self.category.name} - Статьи об автоковриках'
        context['page_description'] = self.category.description or f'Статьи из категории {self.category.name}'
        return context


class ArticleDetailView(DetailView):
    """📄 Детальная страница статьи"""
    model = Article
    template_name = 'blog/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        """🔍 Только опубликованные статьи"""
        return Article.objects.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).select_related('category', 'author')

    def get_object(self, queryset=None):
        """👁️ Увеличиваем счетчик просмотров"""
        obj = super().get_object(queryset)
        # 🔧 Атомарное увеличение счетчика
        Article.objects.filter(pk=obj.pk).update(views=F('views') + 1)
        # 📊 Обновляем значение в текущем объекте
        obj.views += 1
        return obj

    def get_context_data(self, **kwargs):
        """📊 Дополнительный контекст для шаблона"""
        context = super().get_context_data(**kwargs)
        article = self.object

        # 🔗 Похожие статьи
        context['related_articles'] = article.get_related_articles()

        # ⬅️➡️ Навигация
        context['previous_article'] = article.get_previous_article()
        context['next_article'] = article.get_next_article()

        # 📂 Категории для сайдбара
        context['categories'] = Category.objects.all().order_by('sort_order', 'name')

        # 🏷️ SEO метаданные
        context['page_title'] = article.title
        context['page_description'] = article.excerpt[:160] if article.excerpt else article.title

        # ⏱️ Время чтения
        context['reading_time'] = article.reading_time

        return context