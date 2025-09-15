# 📁 common/apps.py - Конфигурация приложения common
# ✅ НЕОБХОДИМО: для правильной работы Django apps

from django.apps import AppConfig


class CommonConfig(AppConfig):
    """⚙️ Конфигурация приложения common"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'
    verbose_name = "🔧 Общие модели"

    def ready(self):
        """🚀 Инициализация приложения"""
        # 📝 Импортируем сигналы, если они есть
        try:
            import common.signals  # noqa F401
        except ImportError:
            pass

        # 🔧 Дополнительная инициализация, если нужна
        super().ready()