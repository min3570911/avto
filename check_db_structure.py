# check_db_structure.py - Улучшенная версия с диагностикой

import os
import sys

# --- Диагностика: Шаг 1 ---
print("✅ Скрипт запущен...")

# --- Настройка окружения Django ---
try:
    # Указываем путь к файлу настроек вашего проекта
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecomm.settings')
    # --- Диагностика: Шаг 2 ---
    print(f"⚙️  Используется файл настроек: {os.environ['DJANGO_SETTINGS_MODULE']}")

    import django

    # --- Диагностика: Шаг 3 ---
    print(f"🐍 Версия Django: {django.get_version()}. Загружаю модели...")

    django.setup()
    # --- Диагностика: Шаг 4 ---
    print("🚀 Модели Django успешно загружены!")

    # Импортируем модели только ПОСЛЕ django.setup()
    from django.apps import apps

except Exception as e:
    print("\n" + "=" * 80)
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось настроить окружение Django.")
    print(f"   Детали: {e}")
    print("   Возможные причины:")
    print("   1. Вы запускаете скрипт не из корневой папки проекта (D:\\YandexDisk\\avtokovriki).")
    print("   2. Виртуальное окружение не активировано.")
    print("   3. Имя проекта в 'ecomm.settings' указано неверно.")
    print("=" * 80)
    sys.exit(1)  # Выход с кодом ошибки


# --- Основная функция сканирования ---
def run_db_scan():
    """Главная функция для анализа и вывода структуры БД."""
    print("\n" + "=" * 80)
    print("🕵️  НАЧИНАЮ ПОЛНОЕ СКАНИРОВАНИЕ БАЗЫ ДАННЫХ...")
    print("=" * 80)

    # Получаем все модели, зарегистрированные в проекте
    all_models = apps.get_models()

    if not all_models:
        print("⚠️ Не найдено ни одной модели в проекте.")
        return

    # Фильтруем служебные приложения, чтобы не загромождать вывод
    excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions']
    models_to_scan = [m for m in all_models if m._meta.app_label not in excluded_apps]

    if not models_to_scan:
        print("⚠️ Не найдено моделей для сканирования (только служебные Django).")
        return

    for model in models_to_scan:
        app_label = model._meta.app_label
        model_name = model.__name__
        table_name = model._meta.db_table

        print("\n" + "-" * 80)
        print(f"📱 Приложение: {app_label.upper()} | 📦 Модель: {model_name} | 🗂️ Таблица: {table_name}")
        print("-" * 80)

        try:
            count = model.objects.count()
            print(f"  📈 Количество записей: {count}")

            print(f"  🔩 Поля модели:")
            for field in model._meta.get_fields():
                if not (field.auto_created and not field.concrete):  # Убираем "мусорные" поля
                    print(f"    - {field.name}: {field.get_internal_type()}")

            if count > 0:
                print(f"  📝 Примеры записей (первые 3):")
                examples = model.objects.all()[:3]
                for i, item in enumerate(examples):
                    print(f"    {i + 1}. {str(item)}")
            else:
                print(f"  📝 Примеры записей: (таблица пуста)")

        except Exception as e:
            print(f"  ❌ Ошибка при анализе модели {model_name}: {e}")

    print("\n" + "=" * 80)
    print("✅ СКАНИРОВАНИЕ УСПЕШНО ЗАВЕРШЕНО.")
    print("=" * 80)


# --- Точка входа в скрипт ---
# Этот блок выполняется, только когда файл запускается напрямую
if __name__ == "__main__":
    # --- Диагностика: Шаг 5 ---
    print("Точка входа (__main__) обнаружена. Запускаю сканирование...")
    run_db_scan()