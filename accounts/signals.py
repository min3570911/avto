# 📁 accounts/signals.py - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ циклического импорта

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


# 🗑️ УБРАН ПРЯМОЙ ИМПОРТ: from accounts.models import Profile
# ✅ ИСПОЛЬЗУЕМ ПОЗДНИЙ ИМПОРТ внутри функций


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """👤 Создание профиля при создании пользователя"""
    if created:
        # 🔄 ПОЗДНИЙ ИМПОРТ для избежания циклического импорта
        from accounts.models import Profile
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """💾 Автоматическое сохранение профиля"""
    try:
        # 🔄 ПОЗДНИЙ ИМПОРТ для избежания циклического импорта
        from accounts.models import Profile

        # 🛡️ Проверяем существование профиля перед сохранением
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # 🆕 Создаем профиль если его нет
            Profile.objects.get_or_create(user=instance)
    except Exception as e:
        # 📝 Логируем ошибку, но не прерываем процесс
        print(f"⚠️ Ошибка при сохранении профиля для {instance.username}: {e}")

# 🔧 ИСПРАВЛЕНИЯ:
# ✅ УБРАН прямой импорт Profile (причина циклического импорта)
# ✅ ИСПОЛЬЗУЕТСЯ поздний импорт внутри функций
# ✅ ДОБАВЛЕНА обработка ошибок
# ✅ СОХРАНЕНА вся функциональность сигналов

# 💡 ПРИМЕЧАНИЕ:
# Поздний импорт позволяет избежать циклических зависимостей
# при загрузке Django приложений