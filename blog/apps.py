# 📁 blog/apps.py
# ⚙️ Конфигурация приложения блога

from django.apps import AppConfig


class BlogConfig(AppConfig):
    """⚙️ Конфигурация приложения блога"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'Блог - Статьи'

    def ready(self):
        """🚀 Инициализация при запуске приложения"""
        # 🔔 Подключаем сигналы
        import blog.signals