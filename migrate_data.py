#!/usr/bin/env python3
# 📁 fix_migrations.py - Скрипт для исправления конфликта миграций
# 🔧 Безопасное удаление проблемных миграций и пересоздание

import os
import shutil
from pathlib import Path


def backup_migrations():
    """📦 Создаем резервную копию миграций"""
    print("📦 Создаем резервную копию миграций...")

    # Создаем папку для бэкапов
    backup_dir = Path("migrations_backup")
    backup_dir.mkdir(exist_ok=True)

    # Копируем миграции
    for app in ['products', 'blog']:
        app_migrations = Path(app) / 'migrations'
        if app_migrations.exists():
            backup_app_dir = backup_dir / app
            if backup_app_dir.exists():
                shutil.rmtree(backup_app_dir)
            shutil.copytree(app_migrations, backup_app_dir)
            print(f"✅ Скопированы миграции {app}")


def remove_problematic_migrations():
    """🗑️ Удаляем проблемные миграции"""
    print("🗑️ Удаляем проблемные миграции...")

    # Файлы для удаления
    files_to_remove = [
        'products/migrations/0026_alter_product_product_desription.py',
        'blog/migrations/0001_initial.py',
        'blog/migrations/0002_migrate_to_ckeditor5.py',
        'products/migrations/0027_migrate_to_ckeditor5.py'
    ]

    for file_path in files_to_remove:
        file_path = Path(file_path)
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️ Удален файл: {file_path}")
        else:
            print(f"⚠️ Файл не найден: {file_path}")


def show_commands():
    """📋 Показываем команды для выполнения"""
    print("\n" + "=" * 60)
    print("📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("=" * 60)
    print()
    print("1️⃣ Откатите миграции к безопасной версии:")
    print("   python manage.py migrate products 0025")
    print("   python manage.py migrate blog zero")
    print()
    print("2️⃣ Создайте новые миграции:")
    print("   python manage.py makemigrations blog")
    print("   python manage.py makemigrations products")
    print()
    print("3️⃣ Примените новые миграции:")
    print("   python manage.py migrate")
    print()
    print("4️⃣ Соберите статические файлы:")
    print("   python manage.py collectstatic --clear --noinput")
    print()
    print("5️⃣ Запустите сервер:")
    print("   python manage.py runserver localhost:8000")
    print()
    print("=" * 60)


def main():
    """🚀 Главная функция"""
    print("🔧 Исправление конфликта миграций Django")
    print("=" * 50)

    response = input("📦 Создать резервную копию миграций? (y/n): ")
    if response.lower() == 'y':
        backup_migrations()

    response = input("🗑️ Удалить проблемные файлы миграций? (y/n): ")
    if response.lower() == 'y':
        remove_problematic_migrations()

    show_commands()

    print("\n✅ Скрипт завершен!")
    print("⚠️ ВАЖНО: Выполните команды выше по порядку!")


if __name__ == "__main__":
    main()