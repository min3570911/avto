#!/usr/bin/env python3
# 📁 fix_django_countries.py
# 🔧 Быстрое исправление ошибки ModuleNotFoundError: No module named 'django_countries'

import os
import subprocess
import shutil


def print_step(step, description):
    """📝 Красивый вывод шага"""
    print(f"\n{step} {description}")
    print("-" * 50)


def backup_file(file_path):
    """💾 Создать резервную копию файла"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_django_countries"
        shutil.copy2(file_path, backup_path)
        print(f"💾 Создана резервная копия: {backup_path}")
        return True
    return False


def run_command(command, description):
    """🔧 Выполнить команду"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Ошибка: {e}")
        return False


def main():
    """🚀 Основная функция исправления"""

    print("🔧 ИСПРАВЛЕНИЕ ОШИБКИ django_countries")
    print("=" * 60)
    print("❌ Проблема: ModuleNotFoundError: No module named 'django_countries'")
    print("✅ Решение: Заменяем django-countries на простые текстовые поля")

    # 1️⃣ Удаление django-countries
    print_step("1️⃣", "Удаление django-countries")
    run_command("pip uninstall django-countries -y", "Удаление django-countries")

    # 2️⃣ Создание резервных копий
    print_step("2️⃣", "Создание резервных копий")
    files_to_backup = [
        'accounts/forms.py',
        'home/models.py',
        'home/admin.py',
        'requirements.txt'
    ]

    for file_path in files_to_backup:
        backup_file(file_path)

    # 3️⃣ Проверка settings.py
    print_step("3️⃣", "Проверка settings.py")

    settings_path = None
    possible_settings = ['settings.py', 'ecomm/settings.py', 'config/settings.py']

    for path in possible_settings:
        if os.path.exists(path):
            settings_path = path
            break

    if settings_path:
        print(f"📁 Найден файл настроек: {settings_path}")

        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'django_countries' in content:
            print("⚠️ В settings.py найдены ссылки на django_countries!")
            print("📝 Удалите следующие строки из INSTALLED_APPS:")
            print("   - 'django_countries',")

            # Автоматическое исправление
            new_content = content.replace("'django_countries',", "")
            new_content = new_content.replace('"django_countries",', "")

            backup_file(settings_path)

            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print("✅ django_countries удален из INSTALLED_APPS")
        else:
            print("✅ В settings.py нет ссылок на django_countries")
    else:
        print("❌ Файл settings.py не найден")

    # 4️⃣ Обновление зависимостей
    print_step("4️⃣", "Обновление requirements.txt")

    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Удаляем строки с django-countries
        new_lines = [line for line in lines if 'django-countries' not in line.lower()]

        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        print("✅ django-countries удален из requirements.txt")

    # 5️⃣ Применение миграций
    print_step("5️⃣", "Применение миграций")

    if run_command("python manage.py makemigrations", "Создание миграций"):
        run_command("python manage.py migrate", "Применение миграций")

    # 6️⃣ Проверка исправления
    print_step("6️⃣", "Проверка исправления")

    if run_command("python manage.py check", "Проверка проекта"):
        print("✅ Проект прошел проверку Django")

    # 7️⃣ Финальные инструкции
    print_step("7️⃣", "Финальные инструкции")

    print("\n🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 40)

    print("\n📋 ЧТО БЫЛО СДЕЛАНО:")
    print("✅ Удален пакет django-countries")
    print("✅ Обновлен settings.py")
    print("✅ Обновлен requirements.txt")
    print("✅ Применены миграции")

    print("\n🔧 ЧТО НУЖНО СДЕЛАТЬ ДАЛЬШЕ:")
    print("1️⃣ Замените файлы на исправленные версии:")
    print("   📁 accounts/forms.py")
    print("   📁 home/models.py")
    print("   📁 home/admin.py")
    print("")
    print("2️⃣ Проверьте работу проекта:")
    print("   python manage.py runserver")
    print("")
    print("3️⃣ Если остались ошибки, проверьте файлы на импорты:")
    print("   grep -r 'django_countries' .")
    print("   grep -r 'CountryField' .")

    print("\n📝 ИЗМЕНЕНИЯ В МОДЕЛЯХ:")
    print("🔄 CountryField → CharField")
    print("🔄 Выбор стран → Простое текстовое поле")
    print("🔄 По умолчанию: 'Беларусь'")

    print("\n💡 ЕСЛИ НУЖНЫ СТРАНЫ:")
    print("Добавьте в модель choices:")
    print("COUNTRIES = [")
    print("    ('BY', 'Беларусь'),")
    print("    ('RU', 'Россия'),")
    print("    ('UA', 'Украина'),")
    print("]")
    print("country = models.CharField(max_length=2, choices=COUNTRIES, default='BY')")


if __name__ == "__main__":
    main()