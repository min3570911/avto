# 📁 ecomm/settings.py
# 🔧 Полная конфигурация Django проекта с CKEditor 5
# ✅ СОВРЕМЕННО: Переход на django-ckeditor-5

import os
import sys
from pathlib import Path
from decouple import config, Csv

# 📁 Базовые пути проекта
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

# ================================
# 🛡️ НАСТРОЙКИ БЕЗОПАСНОСТИ
# ================================

# 🔑 Секретный ключ (ОБЯЗАТЕЛЬНО вынести в .env!)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# 🐛 Режим отладки
DEBUG = config('DEBUG', default=True, cast=bool)

# 🌐 Разрешенные хосты
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,192.168.1.1', cast=Csv())

# ================================
# 📱 ПРИЛОЖЕНИЯ
# ================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap4',
    # ✅ НОВОЕ: CKEditor 5 для современного WYSIWYG редактирования
    'django_ckeditor_5',
]

LOCAL_APPS = [
    'base',
    'common',
    'accounts',
    'products',
    'boats',
    'home',
    'blog',  # Приложение для статей
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ================================
# 🔗 MIDDLEWARE
# ================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecomm.urls'

# ================================
# 🎨 ШАБЛОНЫ
# ================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# 📧 Добавляем директорию для шаблонов писем
TEMPLATES[0]['DIRS'] += [os.path.join(BASE_DIR, 'templates/emails')]

WSGI_APPLICATION = 'ecomm.wsgi.application'

# ================================
# 📊 БАЗА ДАННЫХ
# ================================

# 🔧 Настройка базы данных с поддержкой .env
if config('DB_NAME', default=''):
    # PostgreSQL конфигурация
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    # SQLite по умолчанию для разработки
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ================================
# 🔍 ЛОГИРОВАНИЕ (ИСПРАВЛЕНО ДЛЯ WINDOWS)
# ================================

# Создаем папку для логов если её нет
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# 🔧 Исправленная конфигурация логирования БЕЗ эмодзи в консоли
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        # 🆕 Форматтер БЕЗ эмодзи для Windows консоли
        'console_safe': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'django.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',  # 🔧 Явно указываем UTF-8 для файлов
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console_safe',  # 🔧 Используем безопасный форматтер
            'stream': sys.stdout,
        },
        # 🆕 Отдельный обработчик для Telegram логов
        'telegram_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'telegram.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'accounts': {  # 🤖 Логи для accounts (включая Telegram)
            'handlers': ['telegram_file'],
            'level': 'INFO',
            'propagate': False,  # Не дублируем в django логгер
        },
        # 🆕 Отдельный логгер только для Telegram
        'telegram': {
            'handlers': ['telegram_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# 🔧 Дополнительные настройки для Windows
if os.name == 'nt':  # Windows
    # Отключаем эмодзи в консольных логах на Windows
    import locale

    try:
        # Пытаемся установить UTF-8 локаль
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            # Если UTF-8 недоступна, используем системную локаль
            pass

# ================================
# 🤖 TELEGRAM УВЕДОМЛЕНИЯ
# ================================

# 🚨 ВАЖНО: Эти настройки теперь читаются из .env файла!
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='YOUR_TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = config('TELEGRAM_CHAT_ID', default='YOUR_TELEGRAM_CHAT_ID')

# ⚠️ Проверка наличия обязательных Telegram настроек
if TELEGRAM_BOT_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN' or TELEGRAM_CHAT_ID == 'YOUR_TELEGRAM_CHAT_ID':
    import warnings

    warnings.warn(
        "⚠️ Telegram настройки не найдены в .env файле! "
        "Уведомления о заказах работать не будут. "
        "Добавьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env файл.",
        UserWarning
    )

# ================================
# 📧 EMAIL НАСТРОЙКИ
# ================================

# 🔧 Email backend из переменных окружения
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_USE_SSL = False

# ================================
# 💳 ПЛАТЕЖНЫЕ СИСТЕМЫ
# ================================

# Razorpay настройки
RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='')
RAZORPAY_SECRET_KEY = config('RAZORPAY_SECRET_KEY', default='')

# ================================
# 🗄️ СТАТИЧЕСКИЕ ФАЙЛЫ И МЕДИА
# ================================

# 📄 Статические файлы (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 🔧 ВАЖНО: Сохраняем старый путь к статическим файлам, как было в оригинальном файле
STATICFILES_DIRS = [os.path.join(BASE_DIR, "public/media")]

# 🖼️ Медиа файлы (загруженные пользователями)
MEDIA_ROOT = os.path.join(BASE_DIR, 'public/media')
MEDIA_URL = '/media/'

# 📁 Создаем директории, если их нет
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.dirname(STATIC_ROOT), exist_ok=True)

# ================================
# 🌐 ИНТЕРНАЦИОНАЛИЗАЦИЯ
# ================================

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Minsk'
USE_I18N = True
USE_TZ = True

# ================================
# 🔧 ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
# ================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 🎨 Crispy Forms настройки
CRISPY_TEMPLATE_PACK = 'bootstrap4'
CRISPY_ALLOWED_TEMPLATE_PACKS = ['bootstrap4']

# ================================
# 🛡️ НАСТРОЙКИ БЕЗОПАСНОСТИ ДЛЯ ПРОДАКШЕНА
# ================================

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ================================
# 📊 ВАЛИДАЦИЯ ПАРОЛЕЙ
# ================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ================================
# 🔐 СЕССИИ
# ================================

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 недели
SESSION_SAVE_EVERY_REQUEST = True

# ================================
# 🔒 АУТЕНТИФИКАЦИЯ
# ================================

# 🔑 Конфигурация бэкендов авторизации
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ================================
# 📝 ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
# ================================

# 📦 Максимальный размер загружаемого файла (в байтах)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# 💬 Настройки для Django messages
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# 🌐 Настройка домена для писем
DEFAULT_DOMAIN = '127.0.0.1:8000'
DEFAULT_HTTP_PROTOCOL = 'http'

# ================================
# ✅ НАСТРОЙКИ CKEDITOR 5
# ================================

# 🎨 Кастомные конфигурации для разных типов контента
customColorPalette = [
    {'color': 'hsl(4, 90%, 58%)', 'label': 'Red'},
    {'color': 'hsl(340, 82%, 52%)', 'label': 'Pink'},
    {'color': 'hsl(291, 64%, 42%)', 'label': 'Purple'},
    {'color': 'hsl(262, 52%, 47%)', 'label': 'Deep Purple'},
    {'color': 'hsl(231, 48%, 48%)', 'label': 'Indigo'},
    {'color': 'hsl(207, 90%, 54%)', 'label': 'Blue'},
]

# 🎯 Основные конфигурации редактора
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': {
            'items': [
                'heading', '|',
                'bold', 'italic', 'underline', 'strikethrough', '|',
                'bulletedList', 'numberedList', '|',
                'outdent', 'indent', '|',
                'insertTable', 'link', 'imageUpload', 'blockQuote', '|',
                'fontSize', 'fontColor', 'fontBackgroundColor', '|',
                'alignment', '|',
                'undo', 'redo', 'sourceEditing'
            ]
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'}
            ]
        },
        'fontSize': {
            'options': [9, 11, 13, 'default', 17, 19, 21]
        },
        'fontColor': {
            'colors': customColorPalette
        },
        'fontBackgroundColor': {
            'colors': customColorPalette
        },
        'image': {
            'toolbar': [
                'imageTextAlternative', '|',
                'imageStyle:alignLeft', 'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side', '|'
            ],
            'styles': [
                'full', 'side', 'alignLeft', 'alignRight', 'alignCenter'
            ]
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells']
        },
        'link': {
            'decorators': {
                'addTargetToExternalLinks': True,
                'defaultProtocol': 'https://',
                'toggleDownloadable': {
                    'mode': 'manual',
                    'label': 'Downloadable',
                    'attributes': {
                        'download': 'file'
                    }
                }
            }
        },
        'htmlSupport': {
            'allow': [
                {'name': '/./', 'attributes': True, 'classes': True, 'styles': True}
            ]
        }
    },

    # 📝 Конфигурация для блога (расширенная)
    'blog': {
        'toolbar': {
            'items': [
                'heading', 'style', '|',
                'bold', 'italic', 'underline', 'strikethrough', 'subscript', 'superscript', '|',
                'bulletedList', 'numberedList', 'todoList', '|',
                'outdent', 'indent', '|',
                'insertTable', 'link', 'imageUpload', 'mediaEmbed', 'blockQuote', 'horizontalLine', '|',
                'fontSize', 'fontColor', 'fontBackgroundColor', 'highlight', '|',
                'alignment', '|',
                'specialCharacters', 'pageBreak', '|',
                'undo', 'redo', 'sourceEditing', 'showBlocks'
            ]
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'},
                {'model': 'heading4', 'view': 'h4', 'title': 'Heading 4', 'class': 'ck-heading_heading4'},
                {'model': 'heading5', 'view': 'h5', 'title': 'Heading 5', 'class': 'ck-heading_heading5'},
                {'model': 'heading6', 'view': 'h6', 'title': 'Heading 6', 'class': 'ck-heading_heading6'}
            ]
        },
        'fontSize': {
            'options': [9, 11, 13, 'default', 17, 19, 21, 23, 25]
        },
        'fontColor': {
            'colors': customColorPalette
        },
        'fontBackgroundColor': {
            'colors': customColorPalette
        },
        'image': {
            'toolbar': [
                'imageTextAlternative', '|',
                'imageStyle:alignLeft', 'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side', '|',
                'imageStyle:block', 'imageStyle:inline'
            ],
            'styles': [
                'full', 'side', 'alignLeft', 'alignRight', 'alignCenter', 'block', 'inline'
            ]
        },
        'table': {
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells',
                'tableCellProperties', 'tableProperties'
            ]
        },
        'link': {
            'decorators': {
                'addTargetToExternalLinks': True,
                'defaultProtocol': 'https://',
                'toggleDownloadable': {
                    'mode': 'manual',
                    'label': 'Downloadable',
                    'attributes': {
                        'download': 'file'
                    }
                }
            }
        },
        'mediaEmbed': {
            'previewsInData': True
        },
        'htmlSupport': {
            'allow': [
                {'name': '/./', 'attributes': True, 'classes': True, 'styles': True}
            ]
        }
    },

    # 📄 Базовая конфигурация (простая)
    'basic': {
        'toolbar': {
            'items': [
                'bold', 'italic', 'underline', '|',
                'bulletedList', 'numberedList', '|',
                'link', '|',
                'undo', 'redo'
            ]
        },
        'link': {
            'decorators': {
                'addTargetToExternalLinks': True,
                'defaultProtocol': 'https://'
            }
        }
    }
}

# 📁 Настройки загрузки файлов для CKEditor 5
CKEDITOR_5_UPLOAD_PATH = "ckeditor5_uploads/"
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# 🔒 Ограничения загрузки
CKEDITOR_5_ALLOW_ALL_FILE_TYPES = False
CKEDITOR_5_UPLOAD_FILE_TYPES = ['jpeg', 'jpg', 'png', 'gif', 'webp']

# 🎯 ПРЕИМУЩЕСТВА CKEDITOR 5:
# ✅ Современный интерфейс - отзывчивый и мобильный
# ✅ Лучшая безопасность - последние патчи безопасности
# ✅ Расширенная функциональность - больше возможностей редактирования
# ✅ Лучшая производительность - оптимизированный код
# ✅ Активная поддержка - регулярные обновления