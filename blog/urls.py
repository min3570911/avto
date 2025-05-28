# 📁 blog/urls.py - URL-маршруты для раздела "Статьи"
# 🔗 Использует префикс /articles/ вместо /blog/

from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # 📰 Главная страница блога - список всех статей
    path('', views.ArticleListView.as_view(), name='article_list'),

    # 📂 Статьи по категории
    path('category/<slug:slug>/', views.CategoryArticlesView.as_view(), name='category_articles'),

    # 📄 Детальная страница статьи (с .html в конце URL)
    path('<slug:slug>', views.ArticleDetailView.as_view(), name='article_detail'),

]