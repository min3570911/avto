#!/usr/bin/env python
"""
Комплексный скрипт для создания приложения статей с SEO-оптимизацией
для проекта min3570911/avto
"""
import os
import sys
import subprocess
import shutil


def run_command(command):
    """Выполняет команду и выводит результат"""
    print(f"Выполнение: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True,
                                text=True, capture_output=True)
        print(f"Результат: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def create_file(path, content):
    """Создает файл с указанным содержимым"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Создан файл: {path}")


def update_file(path, content, mode='w'):
    """Обновляет содержимое файла"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode, encoding='utf-8') as f:
        f.write(content)
    print(f"Обновлен файл: {path}")


def main():
    # Получаем текущий каталог проекта
    project_dir = os.getcwd()
    print(f"Текущий каталог проекта: {project_dir}")

    # Проверяем, что мы находимся в корневом каталоге проекта
    if not os.path.exists(os.path.join(project_dir, 'manage.py')):
        print("Ошибка: Не найден файл manage.py. Запустите скрипт из корневого каталога проекта.")
        return False

    # Устанавливаем необходимые пакеты
    print("Установка необходимых пакетов...")
    if not run_command("pip install django-ckeditor pillow python-slugify"):
        return False

    # Создаем приложение articles
    print("Создание приложения articles...")
    if not run_command("python manage.py startapp articles"):
        return False

    # Создаем структуру приложения

    # 1. models.py
    models_content = '''from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from ckeditor_uploader.fields import RichTextUploadingField
import time

class SEOData(models.Model):
    """Абстрактная модель для SEO данных"""
    meta_title = models.CharField(max_length=70, blank=True, verbose_name="Meta Title")
    meta_description = models.CharField(max_length=160, blank=True, verbose_name="Meta Description")
    meta_keywords = models.CharField(max_length=255, blank=True, verbose_name="Meta Keywords")
    canonical_url = models.URLField(blank=True, verbose_name="Canonical URL")

    class Meta:
        abstract = True

class Article(SEOData):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(unique=True, verbose_name="URL")
    short_description = models.TextField(verbose_name="Краткое описание")
    content = RichTextUploadingField(verbose_name="Содержание")
    image = models.ImageField(upload_to="articles/", blank=True, null=True, verbose_name="Изображение")
    is_published = models.BooleanField(default=False, verbose_name="Опубликовано")
    created = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    # SEO-специфичные поля
    open_graph_title = models.CharField(max_length=70, blank=True, verbose_name="OG Title")
    open_graph_description = models.CharField(max_length=200, blank=True, verbose_name="OG Description")
    open_graph_image = models.ImageField(upload_to="articles/og/", blank=True, null=True, verbose_name="OG Image")

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("articles:article_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        # Генерируем slug, если его нет
        if not self.slug:
            # Транслитерация для русского текста
            from slugify import slugify as slugify_ru
            self.slug = slugify_ru(self.title)
            # Добавляем таймстамп для уникальности
            if Article.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{int(time.time())}"

        # Автоматическое заполнение SEO полей, если они не указаны
        if not self.meta_title:
            self.meta_title = self.title[:70]

        if not self.meta_description:
            self.meta_description = self.short_description[:160]

        if not self.open_graph_title:
            self.open_graph_title = self.title[:70]

        if not self.open_graph_description:
            self.open_graph_description = self.short_description[:200]

        super().save(*args, **kwargs)

class ArticleTag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название тега")
    slug = models.SlugField(unique=True, verbose_name="URL")
    articles = models.ManyToManyField(Article, related_name="tags", verbose_name="Статьи", blank=True)

    class Meta:
        verbose_name = "Тег статьи"
        verbose_name_plural = "Теги статей"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            if ArticleTag.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{int(time.time())}"
        super().save(*args, **kwargs)
'''
    update_file(os.path.join(project_dir, 'articles', 'models.py'), models_content)

    # 2. admin.py
    admin_content = '''from django.contrib import admin
from .models import Article, ArticleTag

class ArticleTagInline(admin.TabularInline):
    model = ArticleTag.articles.through
    extra = 1
    verbose_name = "Тег"
    verbose_name_plural = "Теги"

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "created")
    list_filter = ("is_published", "created", "tags")
    search_fields = ("title", "short_description", "content", "meta_keywords")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ArticleTagInline]
    readonly_fields = ("created", "updated")
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "short_description", "content", "image", "is_published", "created", "updated")
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": ("meta_title", "meta_description", "meta_keywords", "canonical_url")
        }),
        ("Open Graph", {
            "classes": ("collapse",),
            "fields": ("open_graph_title", "open_graph_description", "open_graph_image")
        }),
    )

@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    filter_horizontal = ("articles",)
    exclude = ("articles",)
'''
    update_file(os.path.join(project_dir, 'articles', 'admin.py'), admin_content)

    # 3. views.py
    views_content = '''from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Article, ArticleTag
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def article_list(request, tag_slug=None):
    articles = Article.objects.filter(is_published=True)
    tag = None
    page_title = "Статьи"

    if tag_slug:
        tag = get_object_or_404(ArticleTag, slug=tag_slug)
        articles = articles.filter(tags=tag)
        page_title = f"Статьи по тегу: {tag.name}"

    # Пагинация
    paginator = Paginator(articles, 9)  # 9 статей на страницу
    page = request.GET.get("page")
    try:
        articles_paginated = paginator.page(page)
    except PageNotAnInteger:
        # Если страница не является целым числом, возвращаем первую страницу
        articles_paginated = paginator.page(1)
    except EmptyPage:
        # Если страница больше максимальной, возвращаем последнюю
        articles_paginated = paginator.page(paginator.num_pages)

    tags = ArticleTag.objects.all()

    context = {
        "articles": articles_paginated,
        "tags": tags,
        "selected_tag": tag,
        "page_title": page_title,
        "meta_description": "Полезные статьи о наших товарах и услугах",
        "meta_keywords": "статьи, блог, советы, информация"
    }

    return render(request, "articles/article_list.html", context)

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)

    # Получаем связанные статьи (по тегам)
    related_articles = []
    if article.tags.exists():
        related_articles = Article.objects.filter(
            is_published=True, 
            tags__in=article.tags.all()
        ).exclude(id=article.id).distinct()[:3]

    context = {
        "article": article,
        "related_articles": related_articles
    }

    return render(request, "articles/article_detail.html", context)
'''
    update_file(os.path.join(project_dir, 'articles', 'views.py'), views_content)

    # 4. urls.py
    urls_content = '''from django.urls import path
from . import views

app_name = "articles"

urlpatterns = [
    path("", views.article_list, name="article_list"),
    path("tag/<slug:tag_slug>/", views.article_list, name="article_list_by_tag"),
    path("<slug:slug>/", views.article_detail, name="article_detail"),
]
'''
    update_file(os.path.join(project_dir, 'articles', 'urls.py'), urls_content)

    # 5. sitemap.py
    sitemap_content = '''from django.contrib.sitemaps import Sitemap
from .models import Article, ArticleTag
from django.urls import reverse

class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Article.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated

    def location(self, obj):
        return obj.get_absolute_url()

class ArticleTagSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ArticleTag.objects.all()

    def location(self, obj):
        return reverse("articles:article_list_by_tag", args=[obj.slug])

class ArticleStaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ["articles:article_list"]

    def location(self, item):
        return reverse(item)
'''
    update_file(os.path.join(project_dir, 'articles', 'sitemap.py'), sitemap_content)

    # 6. signals.py для автоматизации некоторых процессов
    signals_content = '''from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Article, ArticleTag
from django.utils.text import slugify
import time

@receiver(pre_save, sender=Article)
def article_pre_save(sender, instance, **kwargs):
    # Проверяем, есть ли у статьи slug, если нет - создаем из названия
    if not instance.slug:
        # Транслитерация для русского текста
        from slugify import slugify as slugify_ru
        instance.slug = slugify_ru(instance.title)
        # Проверяем уникальность
        if Article.objects.filter(slug=instance.slug).exists():
            instance.slug = f"{instance.slug}-{int(time.time())}"

@receiver(pre_save, sender=ArticleTag)
def tag_pre_save(sender, instance, **kwargs):
    # Создаем slug из названия тега, если его нет
    if not instance.slug:
        instance.slug = slugify(instance.name)
        if ArticleTag.objects.filter(slug=instance.slug).exists():
            instance.slug = f"{instance.slug}-{int(time.time())}"
'''
    update_file(os.path.join(project_dir, 'articles', 'signals.py'), signals_content)

    # 7. apps.py для регистрации сигналов
    apps_content = '''from django.apps import AppConfig

class ArticlesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "articles"
    verbose_name = "Статьи"

    def ready(self):
        import articles.signals
'''
    update_file(os.path.join(project_dir, 'articles', 'apps.py'), apps_content)

    # Создаем шаблоны
    os.makedirs(os.path.join(project_dir, 'templates', 'articles'), exist_ok=True)

    # 8. article_list.html
    article_list_template = '''{% extends 'base.html' %}
{% load static %}

{% block head %}
    <!-- SEO мета-теги -->
    <title>{{ page_title|default:"Статьи" }} | {{ request.site.name|default:"Название сайта" }}</title>
    <meta name="description" content="{{ meta_description|default:"" }}">
    <meta name="keywords" content="{{ meta_keywords|default:"" }}">

    <!-- Open Graph теги -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{{ request.build_absolute_uri }}">
    <meta property="og:title" content="{{ page_title|default:"Статьи" }} | {{ request.site.name|default:"Название сайта" }}">
    <meta property="og:description" content="{{ meta_description|default:"" }}">
    <meta property="og:image" content="{% static 'images/default-og-image.jpg' %}">

    <!-- Canonical URL -->
    <link rel="canonical" href="{{ request.build_absolute_uri }}">
{% endblock %}

{% block title %}{{ page_title|default:"Статьи" }}{% endblock %}

{% block content %}
<div class="container mt-5">
    <h1 class="mb-4">{{ page_title|default:"Статьи" }}</h1>

    <!-- Фильтр по тегам -->
    {% if tags %}
    <div class="article-tags mb-4">
        <span class="font-weight-bold mr-2">Теги:</span>
        <a href="{% url 'articles:article_list' %}" class="btn btn-sm {% if not selected_tag %}btn-primary{% else %}btn-outline-primary{% endif %} mr-2 mb-2">
            Все
        </a>
        {% for tag in tags %}
        <a href="{% url 'articles:article_list_by_tag' tag.slug %}" class="btn btn-sm {% if selected_tag == tag %}btn-primary{% else %}btn-outline-primary{% endif %} mr-2 mb-2">
            {{ tag.name }}
        </a>
        {% endfor %}
    </div>
    {% endif %}

    <div class="row">
        {% for article in articles %}
            <div class="col-md-4 mb-4">
                <div class="card h-100">
                    {% if article.image %}
                        <img src="{{ article.image.url }}" class="card-img-top" alt="{{ article.title }}">
                    {% else %}
                        <img src="{% static 'images/no-image.jpg' %}" class="card-img-top" alt="Нет изображения">
                    {% endif %}
                    <div class="card-body">
                        <h5 class="card-title">{{ article.title }}</h5>
                        <p class="card-text">{{ article.short_description }}</p>
                        <a href="{% url 'articles:article_detail' article.slug %}" class="btn btn-primary">Читать далее</a>
                    </div>
                    <div class="card-footer">
                        <small class="text-muted">Опубликовано: {{ article.created|date:"d.m.Y" }}</small>
                        {% if article.tags.exists %}
                        <div class="mt-2">
                            {% for tag in article.tags.all %}
                            <a href="{% url 'articles:article_list_by_tag' tag.slug %}" class="badge badge-secondary mr-1">{{ tag.name }}</a>
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        {% empty %}
            <div class="col-12">
                <p>Статьи пока не добавлены.</p>
            </div>
        {% endfor %}
    </div>

    <!-- Пагинация -->
    {% if articles.has_other_pages %}
    <nav aria-label="Навигация по страницам" class="mt-4">
        <ul class="pagination justify-content-center">
            {% if articles.has_previous %}
                <li class="page-item">
                    <a class="page-link" href="?page=1">&laquo; Первая</a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ articles.previous_page_number }}">Предыдущая</a>
                </li>
            {% endif %}

            {% for num in articles.paginator.page_range %}
                {% if articles.number == num %}
                    <li class="page-item active">
                        <span class="page-link">{{ num }} <span class="sr-only">(текущая)</span></span>
                    </li>
                {% elif num > articles.number|add:'-3' and num < articles.number|add:'3' %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ num }}">{{ num }}</a>
                    </li>
                {% endif %}
            {% endfor %}

            {% if articles.has_next %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ articles.next_page_number }}">Следующая</a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ articles.paginator.num_pages }}">Последняя &raquo;</a>
                </li>
            {% endif %}
        </ul>
    </nav>
    {% endif %}
</div>
{% endblock %}
'''
    update_file(os.path.join(project_dir, 'templates', 'articles', 'article_list.html'), article_list_template)

    # 9. article_detail.html
    article_detail_template = '''{% extends 'base.html' %}
{% load static %}

{% block head %}
    <!-- SEO мета-теги -->
    <title>{{ article.meta_title|default:article.title }} | {{ request.site.name|default:"Название сайта" }}</title>
    <meta name="description" content="{{ article.meta_description|default:article.short_description }}">
    <meta name="keywords" content="{{ article.meta_keywords }}">

    <!-- Open Graph теги -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="{{ request.build_absolute_uri }}">
    <meta property="og:title" content="{{ article.open_graph_title|default:article.meta_title|default:article.title }}">
    <meta property="og:description" content="{{ article.open_graph_description|default:article.meta_description|default:article.short_description }}">
    {% if article.open_graph_image %}
    <meta property="og:image" content="{{ article.open_graph_image.url }}">
    {% elif article.image %}
    <meta property="og:image" content="{{ article.image.url }}">
    {% else %}
    <meta property="og:image" content="{% static 'images/default-og-image.jpg' %}">
    {% endif %}
    <meta property="article:published_time" content="{{ article.created|date:'c' }}">
    <meta property="article:modified_time" content="{{ article.updated|date:'c' }}">
    {% for tag in article.tags.all %}
    <meta property="article:tag" content="{{ tag.name }}">
    {% endfor %}

    <!-- Twitter Card теги -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ article.open_graph_title|default:article.meta_title|default:article.title }}">
    <meta name="twitter:description" content="{{ article.open_graph_description|default:article.meta_description|default:article.short_description }}">
    {% if article.open_graph_image %}
    <meta name="twitter:image" content="{{ article.open_graph_image.url }}">
    {% elif article.image %}
    <meta name="twitter:image" content="{{ article.image.url }}">
    {% else %}
    <meta name="twitter:image" content="{% static 'images/default-twitter-image.jpg' %}">
    {% endif %}

    <!-- Canonical URL -->
    <link rel="canonical" href="{% if article.canonical_url %}{{ article.canonical_url }}{% else %}{{ request.build_absolute_uri }}{% endif %}">

    <!-- Структурированные данные Schema.org -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{{ article.title }}",
        "description": "{{ article.short_description }}",
        "image": "{% if article.image %}{{ article.image.url }}{% else %}{% static 'images/default-og-image.jpg' %}{% endif %}",
        "datePublished": "{{ article.created|date:'c' }}",
        "dateModified": "{{ article.updated|date:'c' }}",
        "author": {
            "@type": "Organization",
            "name": "{{ request.site.name|default:"Название компании" }}"
        },
        "publisher": {
            "@type": "Organization",
            "name": "{{ request.site.name|default:"Название компании" }}",
            "logo": {
                "@type": "ImageObject",
                "url": "{% static 'images/logo.png' %}"
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": "{{ request.build_absolute_uri }}"
        }
    }
    </script>
{% endblock %}

{% block title %}{{ article.title }}{% endblock %}

{% block content %}
<div class="container mt-5">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
            <li class="breadcrumb-item"><a href="/">Главная</a></li>
            <li class="breadcrumb-item"><a href="{% url 'articles:article_list' %}">Статьи</a></li>
            <li class="breadcrumb-item active" aria-current="page">{{ article.title }}</li>
        </ol>
    </nav>

    <div class="card mb-5">
        <div class="card-body">
            <h1 class="card-title">{{ article.title }}</h1>
            <p class="card-subtitle mb-3 text-muted">
                Опубликовано: {{ article.created|date:"d.m.Y" }}
            </p>

            {% if article.tags.exists %}
            <div class="mb-3">
                {% for tag in article.tags.all %}
                <a href="{% url 'articles:article_list_by_tag' tag.slug %}" class="badge badge-primary mr-1">{{ tag.name }}</a>
                {% endfor %}
            </div>
            {% endif %}

            {% if article.image %}
                <img src="{{ article.image.url }}" class="img-fluid mb-4" alt="{{ article.title }}">
            {% endif %}

            <div class="article-content">
                {{ article.content|safe }}
            </div>

            <!-- Социальные кнопки для шаринга -->
            <div class="share-buttons mt-4 pt-3 border-top">
                <h5>Поделиться статьей:</h5>
                <div class="d-flex flex-wrap">
                    <a href="https://vk.com/share.php?url={{ request.build_absolute_uri }}" target="_blank" class="btn btn-outline-primary mr-2 mb-2">
                        <i class="fab fa-vk"></i> ВКонтакте
                    </a>
                    <a href="https://t.me/share/url?url={{ request.build_absolute_uri }}&text={{ article.title|urlencode }}" target="_blank" class="btn btn-outline-info mr-2 mb-2">
                        <i class="fab fa-telegram"></i> Telegram
                    </a>
                    <a href="https://www.facebook.com/sharer/sharer.php?u={{ request.build_absolute_uri }}" target="_blank" class="btn btn-outline-primary mr-2 mb-2">
                        <i class="fab fa-facebook-f"></i> Facebook
                    </a>
                    <a href="whatsapp://send?text={{ article.title|urlencode }}%20{{ request.build_absolute_uri|urlencode }}" target="_blank" class="btn btn-outline-success mr-2 mb-2">
                        <i class="fab fa-whatsapp"></i> WhatsApp
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- Связанные статьи -->
    {% if related_articles %}
    <div class="related-articles">
        <h3 class="mb-4">Похожие статьи</h3>
        <div class="row">
            {% for related in related_articles %}
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        {% if related.image %}
                            <img src="{{ related.image.url }}" class="card-img-top" alt="{{ related.title }}">
                        {% else %}
                            <img src="{% static 'images/no-image.jpg' %}" class="card-img-top" alt="Нет изображения">
                        {% endif %}
                        <div class="card-body">
                            <h5 class="card-title">{{ related.title }}</h5>
                            <p class="card-text">{{ related.short_description }}</p>
                            <a href="{% url 'articles:article_detail' related.slug %}" class="btn btn-primary">Читать далее</a>
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
'''
    update_file(os.path.join(project_dir, 'templates', 'articles', 'article_detail.html'), article_detail_template)

    # Создаем static файлы для изображений по умолчанию
    os.makedirs(os.path.join(project_dir, 'static', 'images'), exist_ok=True)

    # Обновляем файл settings.py
    print("Обновление settings.py...")
    settings_path = os.path.join(project_dir, 'ecomm', 'settings.py')

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings_content = f.read()

        # Добавляем приложения в INSTALLED_APPS
        if "'articles.apps.ArticlesConfig'," not in settings_content and "'articles'," not in settings_content:
            settings_content = settings_content.replace(
                "INSTALLED_APPS = [",
                "INSTALLED_APPS = [\n    'articles.apps.ArticlesConfig',"
            )

        # Добавляем django-ckeditor и sitemaps
        if "'ckeditor'," not in settings_content:
            settings_content = settings_content.replace(
                "INSTALLED_APPS = [",
                "INSTALLED_APPS = [\n    'ckeditor',\n    'ckeditor_uploader',"
            )

        if "'django.contrib.sitemaps'," not in settings_content:
            settings_content = settings_content.replace(
                "'django.contrib.staticfiles',",
                "'django.contrib.staticfiles',\n    'django.contrib.sitemaps',"
            )

        # Добавляем настройки CKEditor
        if "CKEDITOR_CONFIGS" not in settings_content:
            ckeditor_settings = """
# CKEditor конфигурация
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Full',
        'height': 300,
        'width': '100%',
        'toolbar_Full': [
            ['Styles', 'Format', 'Bold', 'Italic', 'Underline', 'Strike', 'SpellChecker'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 
             'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink', 'Anchor'],
            ['Image', 'Flash', 'Table', 'HorizontalRule'],
            ['TextColor', 'BGColor'],
            ['Smiley', 'SpecialChar'], ['Source'],
        ],
    },
}
"""
            settings_content += ckeditor_settings

        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(settings_content)
        print("settings.py успешно обновлен")
    except Exception as e:
        print(f"Ошибка при обновлении settings.py: {e}")

    # Обновляем главный urls.py
    print("Обновление urls.py...")
    urls_path = os.path.join(project_dir, 'ecomm', 'urls.py')

    try:
        with open(urls_path, 'r', encoding='utf-8') as f:
            urls_content = f.read()

        # Обновляем импорты
        if 'from django.conf import settings' not in urls_content:
            urls_content = urls_content.replace(
                'from django.urls import path, include',
                'from django.urls import path, include\nfrom django.conf import settings\nfrom django.conf.urls.static import static'
            )

        # Добавляем импорты для sitemap
        if 'sitemap' not in urls_content:
            sitemap_imports = """from django.contrib.sitemaps.views import sitemap
from articles.sitemap import ArticleSitemap, ArticleTagSitemap, ArticleStaticSitemap

sitemaps = {
    'articles': ArticleSitemap,
    'article_tags': ArticleTagSitemap,
    'article_static': ArticleStaticSitemap,
}"""

            # Находим место после последнего импорта
            import_section_end = urls_content.find("urlpatterns")
            if import_section_end > 0:
                # Находим последнюю пустую строку перед urlpatterns
                last_newline = urls_content.rfind("\n\n", 0, import_section_end)
                if last_newline > 0:
                    urls_content = urls_content[:last_newline] + "\n\n" + sitemap_imports + "\n" + urls_content[
                                                                                                   last_newline:]
                else:
                    urls_content = urls_content[:import_section_end] + "\n\n" + sitemap_imports + "\n\n" + urls_content[
                                                                                                           import_section_end:]

        # Добавляем маршруты для articles и ckeditor
        if 'path(\'articles/\'' not in urls_content:
            urls_content = urls_content.replace(
                "urlpatterns = [",
                "urlpatterns = [\n    path('articles/', include('articles.urls', namespace='articles')),"
            )

        if 'path(\'ckeditor/\'' not in urls_content:
            urls_content = urls_content.replace(
                "urlpatterns = [",
                "urlpatterns = [\n    path('ckeditor/', include('ckeditor_uploader.urls')),"
            )

        # Добавляем sitemap
        if 'path(\'sitemap.xml\'' not in urls_content:
            urls_content = urls_content.replace(
                "urlpatterns = [",
                "urlpatterns = [\n    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),"
            )

        # Добавляем настройки для медиафайлов
        if 'static(settings.MEDIA_URL' not in urls_content:
            if ']' in urls_content:
                urls_content = urls_content.replace(
                    ']',
                    ']\n\nif settings.DEBUG:\n    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)'
                )

        with open(urls_path, 'w', encoding='utf-8') as f:
            f.write(urls_content)
        print("urls.py успешно обновлен")
    except Exception as e:
        print(f"Ошибка при обновлении urls.py: {e}")

    # Создаем миграции
    print("Создание миграций...")
    if not run_command("python manage.py makemigrations articles"):
        return False

    # Применяем миграции
    print("Применение миграций...")
    if not run_command("python manage.py migrate"):
        return False

    # Создаем management команду для тестовых данных
    os.makedirs(os.path.join(project_dir, 'articles', 'management', 'commands'), exist_ok=True)
    create_test_data = '''from django.core.management.base import BaseCommand
from articles.models import Article, ArticleTag
from django.utils.text import slugify
import os
from django.core.files.images import ImageFile

class Command(BaseCommand):
    help = "Создает тестовую статью и теги для демонстрации функционала"

    def handle(self, *args, **options):
        # Создаем теги
        tags = [
            {"name": "Новости", "slug": "news"},
            {"name": "Советы", "slug": "tips"},
            {"name": "Обзоры", "slug": "reviews"}
        ]

        created_tags = []
        for tag_data in tags:
            tag, created = ArticleTag.objects.get_or_create(
                slug=tag_data["slug"],
                defaults={"name": tag_data["name"]}
            )
            created_tags.append(tag)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Создан тег: {tag.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Тег уже существует: {tag.name}"))

        # Создаем тестовую статью
        article_title = "Тестовая статья"
        article_slug = "testovaya-statya"

        if Article.objects.filter(slug=article_slug).exists():
            self.stdout.write(self.style.WARNING("Тестовая статья уже существует"))
            return

        article = Article(
            title=article_title,
            slug=article_slug,
            short_description="Это тестовая статья для демонстрации функционала.",
            content='<h2>Добро пожаловать в блог!</h2><p>Это <strong>тестовая статья</strong> для демонстрации функционала блога. Вы можете создать собственные статьи через административную панель.</p><h3>Возможности блога:</h3><ul><li>SEO-оптимизация</li><li>Теги для категоризации</li><li>Форматированный текст</li><li>Загрузка изображений</li></ul><p>Удачного использования!</p>',
            is_published=True,
            meta_title="Тестовая статья - Демонстрация",
            meta_description="Это тестовая статья для демонстрации функционала блога на сайте.",
            meta_keywords="тест, блог, статья, демонстрация"
        )

        article.save()

        # Добавляем теги к статье
        for tag in created_tags:
            article.tags.add(tag)

        self.stdout.write(self.style.SUCCESS(f"Создана тестовая статья: {article.title}"))
'''
    update_file(os.path.join(project_dir, 'articles', 'management', 'commands', 'create_test_article.py'),
                create_test_data)

    # Запускаем команду создания тестовой статьи
    run_command("python manage.py create_test_article")

    print("\n===== УСТАНОВКА ЗАВЕРШЕНА =====")
    print("\nУспешно создано приложение статей с SEO-функциональностью!")
    print("\nЧто было реализовано:")
    print("1. Полноценное приложение для управления статьями")
    print("2. WYSIWYG-редактор CKEditor для удобного форматирования контента")
    print("3. SEO-оптимизация (мета-теги, Open Graph, Schema.org)")
    print("4. Система тегов для категоризации статей")
    print("5. Sitemap для улучшения индексации поисковыми системами")
    print("6. Шаблоны с оптимизированной разметкой")
    print("7. Возможность шаринга статей в социальные сети")
    print("8. Отображение связанных статей")

    print("\nЧто делать дальше:")
    print("1. Перезапустите сервер Django")
    print("2. Перейдите в административную панель по адресу /admin/")
    print("3. Проверьте раздел 'Статьи' и 'Теги статей' в админке")
    print("4. Откройте страницу статей на сайте по адресу /articles/")
    print("5. Добавьте ссылку на статьи в главное меню сайта")

    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
