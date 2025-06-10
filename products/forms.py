# 📁 products/forms.py - ДОПОЛНЕНИЕ к существующим формам
# 🔧 Добавляем формы для импорта данных

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import os

# Если уже есть импорт ReviewForm, оставляем его
try:
    from .forms import ReviewForm
except ImportError:
    # Если файла forms.py еще нет, создаем ReviewForm
    from .models import ProductReview


    class ReviewForm(forms.ModelForm):
        class Meta:
            model = ProductReview
            fields = ['stars', 'content']
            widgets = {
                "stars": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
                "content": forms.Textarea(
                    attrs={"class": "form-control", "rows": 4, "placeholder": "Напишите ваш отзыв здесь..."}),
            }
            labels = {
                "stars": "Оценка",
                "content": "Комментарий"
            }


class ProductImportForm(forms.Form):
    """
    📊 Форма для загрузки Excel файла с товарами

    Поддерживает:
    - Валидацию формата файла
    - Ограничение размера файла
    - Настройки импорта
    """

    excel_file = forms.FileField(
        label="📊 Excel файл с товарами",
        help_text="Поддерживаемые форматы: .xlsx, .xls. Максимальный размер: 10MB",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls',
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
        """✅ Валидация загруженного файла"""

        excel_file = self.cleaned_data.get('excel_file')

        if not excel_file:
            raise ValidationError("Необходимо выбрать файл для загрузки")

        # 📁 Проверка расширения файла
        file_extension = os.path.splitext(excel_file.name)[1].lower()
        allowed_extensions = ['.xlsx', '.xls']

        if file_extension not in allowed_extensions:
            raise ValidationError(
                f"Неподдерживаемый формат файла: {file_extension}. "
                f"Разрешены только: {', '.join(allowed_extensions)}"
            )

        # 📊 Проверка размера файла (максимум 10MB)
        max_size = 10 * 1024 * 1024  # 10MB в байтах
        if excel_file.size > max_size:
            raise ValidationError(
                f"Файл слишком большой: {excel_file.size / 1024 / 1024:.1f}MB. "
                f"Максимальный размер: {max_size / 1024 / 1024:.0f}MB"
            )

        # 🔍 Проверка на пустой файл
        if excel_file.size == 0:
            raise ValidationError("Загруженный файл пустой")

        return excel_file

    def get_import_settings(self) -> dict:
        """⚙️ Получение настроек импорта в виде словаря"""

        return {
            'update_existing': self.cleaned_data.get('update_existing', True),
            'create_categories': self.cleaned_data.get('create_categories', True),
            'process_images': self.cleaned_data.get('process_images', True),
            'skip_errors': self.cleaned_data.get('skip_errors', True),
        }


class ImportPreviewForm(forms.Form):
    """
    👁️ Форма для подтверждения импорта после предпросмотра

    Используется на этапе подтверждения данных перед импортом
    """

    confirm_import = forms.BooleanField(
        label="✅ Подтвердить импорт данных",
        help_text="Я проверил данные и готов начать импорт",
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    # 🔒 Скрытые поля для передачи настроек импорта
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
    """
    📂 Форма для импорта категорий (отдельно от товаров)

    Используется для массового импорта категорий
    """

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

        # Аналогичная валидация как в ProductImportForm
        file_extension = os.path.splitext(excel_file.name)[1].lower()
        if file_extension not in ['.xlsx', '.xls']:
            raise ValidationError(f"Неподдерживаемый формат: {file_extension}")

        max_size = 5 * 1024 * 1024  # 5MB для категорий
        if excel_file.size > max_size:
            raise ValidationError(f"Файл слишком большой: {excel_file.size / 1024 / 1024:.1f}MB")

        return excel_file


class ImportTemplateDownloadForm(forms.Form):
    """
    📥 Форма для скачивания шаблонов Excel файлов

    Позволяет пользователям скачать правильно оформленные шаблоны
    """

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
    """
    🔄 Форма для массового обновления товаров

    Позволяет обновить определенные поля у всех товаров из файла
    """

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

        # Стандартная валидация Excel файла
        file_extension = os.path.splitext(excel_file.name)[1].lower()
        if file_extension not in ['.xlsx', '.xls']:
            raise ValidationError(f"Неподдерживаемый формат: {file_extension}")

        return excel_file


# 🎨 Кастомные виджеты для улучшения UI

class FileUploadWidget(forms.FileInput):
    """📁 Улучшенный виджет для загрузки файлов"""

    template_name = 'admin/widgets/file_upload.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
            'style': 'margin-bottom: 10px;'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class ImportSettingsWidget(forms.Widget):
    """⚙️ Виджет для группировки настроек импорта"""

    template_name = 'admin/widgets/import_settings.html'

    def format_value(self, value):
        if value is None:
            return {}
        return value

# 🔧 ПРИМЕНЕНИЕ:
# Эти формы будут использоваться в admin_views.py для создания интерфейса импорта
# Формы обеспечивают валидацию данных и удобный интерфейс для пользователей