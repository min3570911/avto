# 📁 blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # 📰 Список статей
    path('', views.ArticleListView.as_view(), name='article_list'),

    # 📂 Статьи по категории
    path('category/<slug:slug>/', views.CategoryArticlesView.as_view(), name='category_articles'),

    # 📝 Детальная страница статьи
    path('article/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),

    # 🏷️ Статьи по тегу
    path('tag/<slug:slug>/', views.TagArticlesView.as_view(), name='tag_articles'),
]