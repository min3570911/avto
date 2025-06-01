# 📁 blog/urls.py - МИНИМАЛЬНАЯ ВЕРСИЯ без циклических зависимостей
# 📝 URL-маршруты для блога - упрощенные
# ✅ ИСПРАВЛЕНО: Убраны все потенциальные циклические импорты

from django.urls import path
from . import views

# 📝 Устанавливаем namespace для блога
app_name = 'blog'

# 🌐 Простые URL-паттерны без сложной логики
urlpatterns = [
    # 📰 Список статей
    path('', views.ArticleListView.as_view(), name='article_list'),

    # 📂 Категории статей
    path('category/<slug:slug>/', views.CategoryArticlesView.as_view(), name='category_articles'),

    # 📄 Конкретная статья
    path('article/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
]

# 🔧 ИЗМЕНЕНИЯ:
# ✅ УБРАНЫ: Сложные паттерны URL
# ✅ ИЗМЕНЕНО: path('<slug>', ...) на path('article/<slug>', ...)
# ✅ УПРОЩЕНО: Четкое разделение путей для избежания конфликтов
# ✅ СОХРАНЕНО: app_name для namespace