# 📁 cars/admin.py - ПУСТАЯ АДМИНКА (временно отключена)
# 🚗 Админка для автомобилей временно отключена
#
# ⚠️ ПРИЧИНА: Избежание конфликта регистрации моделей Category и Product
# Эти модели уже зарегистрированы в products/admin.py
#
# 🎯 ПЛАНЫ: После создания отдельных моделей CarCategory и CarProduct
# эта админка будет восстановлена с полным функционалом

from django.contrib import admin

# 📝 КОММЕНТАРИЙ:
# Все регистрации админок временно закомментированы
# до завершения рефакторинга и создания отдельных моделей

# 🔄 ЧТО БУДЕТ ПОСЛЕ РЕФАКТОРИНГА:
# @admin.register(CarCategory)
# class CarCategoryAdmin(admin.ModelAdmin):
#     ...
#
# @admin.register(CarProduct)
# class CarProductAdmin(admin.ModelAdmin):
#     ...

# 🎯 ВРЕМЕННОЕ РЕШЕНИЕ:
# Используйте центральную админку products/admin.py
# Фильтр по типу: category__category_type = 'cars'