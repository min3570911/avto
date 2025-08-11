# 📁 products/forms.py - ОЧИЩЕННАЯ версия с единой формой импорта
# 🔧 УБРАНО: Дублирование ExcelUploadForm и ProductImportForm
# ✅ ОСТАВЛЕНО: Одна универсальная форма + существующие формы отзывов

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import os
import zipfile

# 📝 Импорт модели для отзывов
from common.models import ProductReview


class ReviewForm(forms.ModelForm):
    """📝 Форма для отзывов о товарах"""

    class Meta:
        model = ProductReview
        fields = ['stars', 'content']
        widgets = {
            "stars": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Напишите ваш отзыв здесь..."}
            ),
        }
        labels = {
            "stars": "Оценка",
            "content": "Комментарий"
        }


class ProductImportForm(forms.Form):
    """
    📊 ЕДИНАЯ УНИВЕРСАЛЬНАЯ форма для импорта товаров

    Заменяет все предыдущие формы импорта:
    - ExcelUploadForm ❌
    - ProductImportForm (старая версия) ❌
    - UnifiedImportForm ❌

    Поддерживает:
    - Excel файлы с товарами и категориями
    - ZIP архивы с изображениями
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

    # ⚙️ Настройки импорта
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

    def clean_images_zip(self):
        """🖼️ Валидация ZIP архива с изображениями"""
        images_zip = self.cleaned_data.get('images_zip')

        # 🎯 Если файл не загружен - это нормально (поле необязательное)
        if not images_zip:
            return images_zip

        # 📁 Проверка расширения файла
        file_extension = os.path.splitext(images_zip.name)[1].lower()
        if file_extension != '.zip':
            raise ValidationError(
                f"Неподдерживаемый формат архива: {file_extension}. "
                f"Разрешен только: .zip"
            )

        # 📊 Проверка размера файла (максимум 10MB)
        max_size = 10 * 1024 * 1024  # 10MB в байтах
        if images_zip.size > max_size:
            raise ValidationError(
                f"Архив слишком большой: {images_zip.size / 1024 / 1024:.1f}MB. "
                f"Максимальный размер: {max_size / 1024 / 1024:.0f}MB"
            )

        # 🔍 Проверка на пустой файл
        if images_zip.size == 0:
            raise ValidationError("Загруженный архив пустой")

        # 🗜️ Проверка что это действительно ZIP архив
        try:
            with zipfile.ZipFile(images_zip, 'r') as zip_file:
                # 📊 Проверка количества файлов в архиве
                file_list = zip_file.namelist()
                max_files = 100

                if len(file_list) > max_files:
                    raise ValidationError(
                        f"Слишком много файлов в архиве: {len(file_list)}. "
                        f"Максимум: {max_files} файлов"
                    )

                # 🖼️ Проверка форматов изображений
                allowed_image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
                invalid_files = []

                for filename in file_list:
                    # 🚫 Пропускаем системные файлы и папки
                    if filename.startswith('__MACOSX') or filename.endswith('/'):
                        continue

                    file_ext = os.path.splitext(filename)[1].lower()
                    if file_ext and file_ext not in allowed_image_extensions:
                        invalid_files.append(filename)

                # ⚠️ Предупреждение о неподдерживаемых файлах (не блокируем импорт)
                if invalid_files:
                    files_sample = invalid_files[:3]
                    if len(invalid_files) > 3:
                        files_sample.append(f"... и еще {len(invalid_files) - 3}")

                    # 🔄 Логируем предупреждение, но не блокируем
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"⚠️ Найдены файлы неподдерживаемых форматов: {', '.join(files_sample)}. "
                        f"Они будут пропущены."
                    )

        except zipfile.BadZipFile:
            raise ValidationError("Файл поврежден или не является ZIP архивом")
        except Exception as e:
            raise ValidationError(f"Ошибка при проверке архива: {str(e)}")

        # 🔄 Возвращаем файл в начало для дальнейшего использования
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

        # Аналогичная валидация как в ProductImportForm
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

# 🔧 ОСНОВНЫЕ ИЗМЕНЕНИЯ В ЭТОМ ФАЙЛЕ:
#
# ✅ УБРАНО: ExcelUploadForm (дублирование)
# ✅ УБРАНО: Старая версия ProductImportForm
# ✅ УБРАНО: UnifiedImportForm из admin_views
# ✅ СОЗДАНО: Новая универсальная ProductImportForm с полной валидацией
# ✅ СОХРАНЕНО: Все остальные формы (ReviewForm, ImportPreviewForm, etc.)
# ✅ УЛУЧШЕНО: Валидация ZIP файлов с предупреждениями вместо блокировки
#
# 🎯 РЕЗУЛЬТАТ:
# - Одна форма импорта вместо трёх разных
# - Полная валидация Excel и ZIP файлов
# - Гибкие настройки импорта
# - Чистая архитектура форм