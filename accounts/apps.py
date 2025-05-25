# 📁 accounts/apps.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """⚙️ Конфигурация приложения accounts"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """🔄 Инициализация при загрузке приложения"""
        try:
            # 🔄 ПОЗДНИЙ ИМПОРТ сигналов для избежания циклического импорта
            import accounts.signals
        except ImportError as e:
            # 📝 Логируем ошибку, но не прерываем загрузку
            print(f"⚠️ Ошибка загрузки сигналов accounts: {e}")

# 🔧 ИСПРАВЛЕНИЯ:
# ✅ ДОБАВЛЕНА обработка ошибок при импорте сигналов
# ✅ ПОЗДНИЙ ИМПОРТ в методе ready()
# ✅ СОХРАНЕНА функциональность автоматического создания профилей

# 💡 ПРИМЕЧАНИЕ:
# Метод ready() вызывается после загрузки всех моделей,
# что помогает избежать циклических импортов