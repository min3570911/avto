# 🔧 ИНСТРУКЦИИ ПО ОБНОВЛЕНИЮ settings.py

# 🗑️ УДАЛИТЬ из settings.py:
# - RAZORPAY_KEY_ID и RAZORPAY_KEY_SECRET
# - EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT (если email не нужен)
# - Настройки Google API (GOOGLE_API_KEY и т.д.)
# - Настройки django-allauth

# ✅ ОБЯЗАТЕЛЬНО ДОБАВИТЬ для Telegram уведомлений:
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Получить у @BotFather
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"      # ID чата или группы

# 🔄 ОБНОВИТЬ INSTALLED_APPS (удалить лишнее):
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth', 
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Для красивых форм в админке
    'crispy_forms',
    'crispy_bootstrap4',

    # Приложения проекта
    'accounts',
    'products',
    'home', 
    'base',
]

# ✅ НАСТРОЙКИ CRISPY FORMS:
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"

# 🎯 ЛОГИРОВАНИЕ (для отладки Telegram):
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'orders.log',
        },
    },
    'loggers': {
        'accounts.views': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
