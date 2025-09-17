# 📁 products/forms.py - ОБНОВЛЕННАЯ версия с формой звездочек
# ⭐ ДОБАВЛЕНО: Интерактивная форма отзывов с кликабельными звездочками
# 🔒 ДОБАВЛЕНО: Поддержка модерации отзывов (is_approved=False по умолчанию)

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import os
import zipfile

# 📝 Импорт модели для отзывов
from common.models import ProductReview


class StarRatingWidget(forms.Widget):
    """⭐ Кастомный виджет для интерактивной оценки звездочками"""

    template_name = 'widgets/star_rating.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'star-rating-input',
            'data-max-rating': '5',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def format_value(self, value):
        """🔢 Преобразование значения для отображения"""
        if value is None:
            return '0'
        return str(value)

    def render(self, name, value, attrs=None, renderer=None):
        """🎨 Рендеринг HTML для звездочек"""
        if value is None:
            value = 0
        else:
            value = int(value)

        if attrs is None:
            attrs = {}

        attrs.update(self.attrs)

        # 🎯 Генерация HTML для звездочек
        html = f'<div class="star-rating-widget" data-field-name="{name}">'
        html += f'<input type="hidden" name="{name}" value="{value}" id="id_{name}">'

        for i in range(1, 6):  # 5 звездочек
            active_class = 'active' if i <= value else ''
            html += f'''<span class="star {active_class}" data-value="{i}" title="{i} звезд{'ы' if i in [2, 3, 4] else ('а' if i == 1 else '')}">
                        <i class="fas fa-star"></i>
                    </span>'''

        html += '</div>'

        return html

    def value_from_datadict(self, data, files, name):
        """📥 Получение значения из POST данных"""
        value = data.get(name, '0')
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0


class ReviewForm(forms.ModelForm):
    """📝 ОБНОВЛЕННАЯ форма для отзывов с интерактивными звездочками"""

    class Meta:
        model = ProductReview
        fields = ['stars', 'content']
        widgets = {
            "stars": StarRatingWidget(attrs={
                "class": "star-rating-input",
                "data-required": "true"
            }),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control review-content-textarea",
                    "rows": 4,
                    "placeholder": "Поделитесь вашим мнением о товаре...",
                    "maxlength": "1000"
                }
            ),
        }
        labels = {
            "stars": "Ваша оценка",
            "content": "Комментарий"
        }

    def __init__(self, *args, **kwargs):
        """🏗️ Инициализация формы"""
        super().__init__(*args, **kwargs)

        # 🎯 Настройка полей
        self.fields['stars'].required = True
        self.fields['content'].required = True

        # 💡 Подсказки для пользователей
        self.fields['stars'].help_text = "Кликните на звездочки для выбора оценки"
        self.fields['content'].help_text = "Минимум 10 символов, максимум 1000"

    def clean_stars(self):
        """✅ Валидация оценки"""
        stars = self.cleaned_data.get('stars')

        if not stars or stars < 1:
            raise ValidationError("Пожалуйста, выберите оценку от 1 до 5 звезд")

        if stars > 5:
            raise ValidationError("Максимальная оценка - 5 звезд")

        return stars

    def clean_content(self):
        """✅ Валидация комментария"""
        content = self.cleaned_data.get('content', '').strip()

        if not content:
            raise ValidationError("Пожалуйста, напишите комментарий к отзыву")

        if len(content) < 10:
            raise ValidationError("Комментарий слишком короткий. Минимум 10 символов")

        if len(content) > 1000:
            raise ValidationError("Комментарий слишком длинный. Максимум 1000 символов")

        # 🚫 Простая проверка на спам (можно расширить)
        spam_words = ['спам', 'реклама', 'купить дешево', 'скидка 90%']
        content_lower = content.lower()

        for spam_word in spam_words:
            if spam_word in content_lower:
                raise ValidationError("Комментарий содержит недопустимый контент")

        return content

    def save(self, commit=True):
        """💾 Сохранение с модерацией"""
        instance = super().save(commit=False)

        # 🔒 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Новые отзывы требуют модерации
        if not instance.pk:  # Новый отзыв
            instance.is_approved = False

        if commit:
            instance.save()
        return instance


# ============== ОСТАЛЬНЫЕ ФОРМЫ (БЕЗ ИЗМЕНЕНИЙ) ==============

class ProductImportForm(forms.Form):
    """📊 ЕДИНАЯ УНИВЕРСАЛЬНАЯ форма для импорта товаров"""

    excel_file = forms.FileField(
        label="📊 Excel файл с товарами",
        help_text="Поддерживаемые форматы: .xlsx, .xls. Максимальный размер: 10MB",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls',
            'style': 'margin-bottom: 10px;'
        })
    )

    images_zip = forms.FileField(
        label="🖼️ ZIP архив с изображениями",
        help_text="Необязательно. Поддерживаемый формат: .zip. Максимальный размер: 10MB",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.zip',
            'style': 'margin-bottom: 10px;'
        })
    )

    update_existing = forms.BooleanField(
        label="🔄 Обновлять существующие товары",
        help_text="Если товар с таким SKU уже существует, обновить его данные",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    create_categories = forms.BooleanField(
        label="📂 Создавать новые категории автоматически",
        help_text="Создавать категории, если они не найдены по SKU",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    process_images = forms.BooleanField(
        label="🖼️ Обрабатывать изображения товаров",
        help_text="Искать и привязывать изображения по именам файлов",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    skip_errors = forms.BooleanField(
        label="⏭️ Пропускать строки с ошибками",
        help_text="Продолжать импорт при обнаружении ошибок в отдельных строках",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean_excel_file(self):
        """✅ Валидация загруженного Excel файла"""
        excel_file = self.cleaned_data.get('excel_file')

        if not excel_file:
            raise ValidationError("Необходимо выбрать файл для загрузки")

        file_extension = os.path.splitext(excel_file.name)[1].lower()
        allowed_extensions = ['.xlsx', '.xls']

        if file_extension not in allowed_extensions:
            raise ValidationError(
                f"Неподдерживаемый формат файла: {file_extension}. "
                f"Разрешены только: {', '.join(allowed_extensions)}"
            )

        max_size = 10 * 1024 * 1024  # 10MB в байтах
        if excel_file.size > max_size:
            raise ValidationError(
                f"Файл слишком большой: {excel_file.size / 1024 / 1024:.1f}MB. "
                f"Максимальный размер: {max_size / 1024 / 1024:.0f}MB"
            )

        if excel_file.size == 0:
            raise ValidationError("Загруженный файл пустой")

        return excel_file

    def clean_images_zip(self):
        """🖼️ Валидация ZIP архива с изображениями"""
        images_zip = self.cleaned_data.get('images_zip')

        if not images_zip:
            return images_zip

        file_extension = os.path.splitext(images_zip.name)[1].lower()
        if file_extension != '.zip':
            raise ValidationError(
                f"Неподдерживаемый формат архива: {file_extension}. "
                f"Разрешен только: .zip"
            )

        max_size = 10 * 1024 * 1024  # 10MB в байтах
        if images_zip.size > max_size:
            raise ValidationError(
                f"Архив слишком большой: {images_zip.size / 1024 / 1024:.1f}MB. "
                f"Максимальный размер: {max_size / 1024 / 1024:.0f}MB"
            )

        if images_zip.size == 0:
            raise ValidationError("Загруженный архив пустой")

        images_zip.seek(0)
        return images_zip

    def get_import_settings(self) -> dict:
        """⚙️ Получение настроек импорта в виде словаря"""
        return {
            'update_existing': self.cleaned_data.get('update_existing', True),
            'create_categories': self.cleaned_data.get('create_categories', True),
            'process_images': self.cleaned_data.get('process_images', True),
            'skip_errors': self.cleaned_data.get('skip_errors', True),
        }


class ImportPreviewForm(forms.Form):
    """👁️ Форма для подтверждения импорта после предпросмотра"""

    confirm_import = forms.BooleanField(
        label="✅ Подтвердить импорт данных",
        help_text="Я проверил данные и готов начать импорт",
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    file_session_key = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

    import_settings = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def clean_confirm_import(self):
        """✅ Валидация подтверждения"""
        confirm = self.cleaned_data.get('confirm_import')

        if not confirm:
            raise ValidationError("Необходимо подтвердить импорт для продолжения")

        return confirm


class CategoryImportForm(forms.Form):
    """📂 Форма для импорта только категорий"""

    excel_file = forms.FileField(
        label="📂 Excel файл с категориями",
        help_text="Формат: SKU категории | Название | Описание | Активна",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )

    update_existing_categories = forms.BooleanField(
        label="🔄 Обновлять существующие категории",
        help_text="Обновлять данные категорий, если они уже существуют",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    activate_new_categories = forms.BooleanField(
        label="✅ Активировать новые категории",
        help_text="Устанавливать флаг 'активна' для новых категорий",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean_excel_file(self):
        """✅ Валидация файла категорий"""
        excel_file = self.cleaned_data.get('excel_file')

        if not excel_file:
            raise ValidationError("Необходимо выбрать файл с категориями")

        file_extension = os.path.splitext(excel_file.name)[1].lower()
        if file_extension not in ['.xlsx', '.xls']:
            raise ValidationError(f"Неподдерживаемый формат: {file_extension}")

        max_size = 5 * 1024 * 1024  # 5MB для категорий
        if excel_file.size > max_size:
            raise ValidationError(f"Файл слишком большой: {excel_file.size / 1024 / 1024:.1f}MB")

        return excel_file


class ImportTemplateDownloadForm(forms.Form):
    """📥 Форма для скачивания шаблонов Excel файлов"""

    TEMPLATE_CHOICES = [
        ('products', '🛍️ Шаблон для товаров'),
        ('categories', '📂 Шаблон для категорий'),
        ('full', '🗂️ Полный шаблон (товары + категории)'),
    ]

    template_type = forms.ChoiceField(
        label="📄 Тип шаблона",
        choices=TEMPLATE_CHOICES,
        initial='products',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    include_examples = forms.BooleanField(
        label="📝 Включить примеры данных",
        help_text="Добавить в шаблон несколько строк с примерами заполнения",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class BulkProductUpdateForm(forms.Form):
    """🔄 Форма для массового обновления товаров"""

    excel_file = forms.FileField(
        label="📊 Excel файл с обновлениями",
        help_text="Файл должен содержать SKU товаров и поля для обновления",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )

    UPDATE_FIELD_CHOICES = [
        ('price', '💰 Только цены'),
        ('descriptions', '📝 Только описания'),
        ('seo', '🔍 Только SEO поля (title, meta)'),
        ('all', '🔄 Все поля'),
    ]

    update_fields = forms.ChoiceField(
        label="🎯 Какие поля обновлять",
        choices=UPDATE_FIELD_CHOICES,
        initial='price',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    dry_run = forms.BooleanField(
        label="🔍 Режим предпросмотра",
        help_text="Показать что будет изменено, но не применять изменения",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean_excel_file(self):
        """✅ Валидация файла обновлений"""
        excel_file = self.cleaned_data.get('excel_file')

        if not excel_file:
            raise ValidationError("Необходимо выбрать файл с обновлениями")

        file_extension = os.path.splitext(excel_file.name)[1].lower()
        if file_extension not in ['.xlsx', '.xls']:
            raise ValidationError(f"Неподдерживаемый формат: {file_extension}")

        return excel_file

# 🔧 ОСНОВНЫЕ ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ⭐ ДОБАВЛЕНО: StarRatingWidget - кастомный виджет интерактивных звездочек
# 🔒 ДОБАВЛЕНО: Поддержка модерации в ReviewForm.save()
# ✅ УЛУЧШЕНО: Валидация формы отзывов (анти-спам, длина текста)
# 🎨 ДОБАВЛЕНО: CSS классы и атрибуты для стилизации
# 📝 СОХРАНЕНО: Все остальные формы импорта без изменений
#
# 🎯 РЕЗУЛЬТАТ:
# - Интерактивные кликабельные звездочки вместо числового поля
# - Автоматическая модерация новых отзывов
# - Улучшенная валидация и защита от спама
# - Готовность к стилизации через CSS/JS