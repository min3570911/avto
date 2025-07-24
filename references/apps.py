# 📁 references/apps.py - Конфигурация приложения справочников
# 🔧 ОБНОВЛЕНО: Изменено имя и описание приложения

from django.apps import AppConfig


class ReferencesConfig(AppConfig):
    """📚 Конфигурация приложения справочников"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'references'  # ✅ ИЗМЕНЕНО: products → references
    verbose_name = '📚 Справочники'  # ✅ ИЗМЕНЕНО: новое название

    def ready(self):
        """🚀 Инициализация при запуске приложения"""
        # 📝 В будущем здесь можно добавить специальные сигналы
        pass

# 📝 КОММЕНТАРИЙ:
#
# ✅ ИЗМЕНЕНИЯ:
# - name: 'products' → 'references'
# - verbose_name: описательное название для админки
#
# 🎯 ЦЕЛЬ:
# Приложение теперь называется 'references' и содержит
# справочные данные: цвета, комплектации, купоны, отзывы
#
# 📋 В БУДУЩЕМ (этап 7):
# Из этого приложения будут удалены модели Category, Product, ProductImage
# и останутся только справочники: Color, KitVariant, Coupon, ProductReview, Wishlist