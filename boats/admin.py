# 📁 boats/admin.py - ПУСТАЯ АДМИНКА (временно отключена)
# 🛥️ Админка для лодок временно отключена
#
# ⚠️ ПРИЧИНА: Избежание конфликта регистрации моделей Category и Product
# Эти модели уже зарегистрированы в products/admin.py
#
# 🎯 ПЛАНЫ: После создания отдельных моделей BoatCategory и BoatProduct
# эта админка будет восстановлена с полным функционалом

from django.contrib import admin

# 📝 КОММЕНТАРИЙ:
# Все регистрации админок временно закомментированы
# до завершения рефакторинга и создания отдельных моделей

# 🔄 ЧТО БУДЕТ ПОСЛЕ РЕФАКТОРИНГА:
# @admin.register(BoatCategory)
# class BoatCategoryAdmin(admin.ModelAdmin):
#     ...
#
# @admin.register(BoatProduct)
# class BoatProductAdmin(admin.ModelAdmin):
#     ...

# 🎯 ВРЕМЕННОЕ РЕШЕНИЕ:
# Используйте центральную админку products/admin.py
# Фильтр по типу: category__category_type = 'boats'