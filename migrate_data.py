# 📁 check_quill.py - Скрипт для проверки установки django-quill-editor
# 🔍 Проверяем, правильно ли установлен пакет и какие в нем есть компоненты

import sys
import os

def check_quill_installation():
    """🔍 Проверяет установку и структуру django-quill-editor"""

    print("🔍 Проверка django-quill-editor...")

    # Проверяем, установлен ли пакет
    try:
        import django_quill
        print("✅ Пакет django_quill успешно импортирован")
        print(f"📦 Версия: {getattr(django_quill, '__version__', 'Неизвестно')}")
        print(f"📁 Путь: {django_quill.__file__}")
    except ImportError as e:
        print(f"❌ Ошибка импорта django_quill: {e}")
        return False

    # Проверяем QuillField
    try:
        from django_quill.fields import QuillField
        print("✅ QuillField успешно импортирован")
    except ImportError as e:
        print(f"❌ Ошибка импорта QuillField: {e}")
        return False

    # Проверяем наличие urls.py
    try:
        import django_quill.urls
        print("✅ django_quill.urls существует")
    except ImportError:
        print("⚠️ django_quill.urls не найден (это нормально для некоторых версий)")

    # Проверяем структуру пакета
    package_dir = os.path.dirname(django_quill.__file__)
    print(f"\n📁 Содержимое пакета django_quill:")

    for item in os.listdir(package_dir):
        if not item.startswith('__pycache__'):
            print(f"   📄 {item}")

    return True

if __name__ == "__main__":
    if check_quill_installation():
        print("\n🎉 django-quill-editor установлен корректно!")
    else:
        print("\n❌ Проблемы с установкой django-quill-editor")