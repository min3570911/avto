# 📁 products/templatetags/__init__.py
# 🔧 Файл инициализации для template tags Django

# Этот файл нужен для того, чтобы Django распознал директорию
# products/templatetags как Python пакет с template фильтрами

# 🎯 Без этого файла Django не сможет загрузить фильтры
# из category_filters.py и будет выдавать ошибку:
# "Invalid filter: 'smart_truncate_sentences'"