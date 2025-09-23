# 📁 common/forms.py
# 📝 ФОРМА ОТЗЫВОВ для анонимных пользователей
# 🛡️ ВСТРОЕННАЯ АНТИ-СПАМ ЗАЩИТА: honeypot, время заполнения, валидация
# ✅ УПРОЩЕННАЯ ВЕРСИЯ: только для анонимных отзывов

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import time
import re

from .models import ProductReview


class UniversalReviewForm(forms.ModelForm):
    """
    📝 Универсальная форма отзывов для всех типов пользователей

    🎯 ОСОБЕННОСТИ:
    - Поддержка анонимных и зарегистрированных пользователей
    - Автозаполнение данных из профиля для залогиненных
    - Автоодобрение отзывов для админов
    - Встроенная анти-спам защита
    - Honeypot поля для ловли ботов
    - Валидация времени заполнения формы
    - Интерактивные звездочки
    """

    # 👤 ПОЛЕ ИМЕНИ (всегда обязательное)
    reviewer_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше имя',
            'id': 'id_reviewer_name'
        }),
        label="Ваше имя",
        help_text="Обязательное поле"
    )

    # 📧 ПОЛЕ EMAIL (обязательное)
    reviewer_email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email',
            'id': 'id_reviewer_email'
        }),
        label="Ваш email",
        help_text="Обязательное поле (не публикуется)"
    )

    # ⭐ ЗВЕЗДОЧКИ (интерактивные через JavaScript)
    stars = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={
            'class': 'star-rating',
            'id': 'id_stars'
        }),
        label="Ваша оценка",
        required=True
    )

    # 📝 СОДЕРЖАНИЕ ОТЗЫВА
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Напишите ваш отзыв о товаре...',
            'maxlength': 2000,
            'id': 'id_content'
        }),
        label="Ваш отзыв",
        help_text="Минимум 10 символов, максимум 2000",
        max_length=2000,
        required=True
    )

    # 🍯 HONEYPOT ПОЛЯ (скрытые ловушки для ботов)
    honeypot_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'honeypot-field',
            'tabindex': '-1',
            'autocomplete': 'off'
        })
    )

    honeypot_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'honeypot-field',
            'tabindex': '-1',
            'autocomplete': 'off'
        })
    )

    # ⏱️ СКРЫТЫЕ ПОЛЯ ДЛЯ АНТИ-СПАМ ЗАЩИТЫ
    form_load_time = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        """
        🔧 Инициализация формы для анонимных и зарегистрированных пользователей
        """
        # Извлекаем пользователя из kwargs
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Если пользователь зарегистрирован, делаем поля имени и email не обязательными
        if self.user and self.user.is_authenticated:
            self.fields['reviewer_name'].required = False
            self.fields['reviewer_email'].required = False
            self.fields['reviewer_name'].help_text = "Оставьте пустым для использования данных профиля"
            self.fields['reviewer_email'].help_text = "Оставьте пустым для использования email профиля"

    def clean_reviewer_name(self):
        """✅ Валидация имени автора"""
        reviewer_name = self.cleaned_data.get('reviewer_name', '').strip()

        # Для зарегистрированных пользователей имя не обязательно
        if not reviewer_name and (not self.user or not self.user.is_authenticated):
            raise ValidationError("Пожалуйста, укажите ваше имя.")

        # Если имя не указано, но пользователь залогинен - пропускаем валидацию
        if not reviewer_name and self.user and self.user.is_authenticated:
            return reviewer_name

        if len(reviewer_name) < 2:
            raise ValidationError("Имя должно содержать минимум 2 символа.")

        # Проверяем на подозрительные символы
        if re.search(r'[<>{}"\'\\/]', reviewer_name):
            raise ValidationError("Имя содержит недопустимые символы.")

        # Проверяем на спам-слова в имени
        spam_patterns = [
            r'admin',
            r'moderator',
            r'test',
            r'spam',
            r'bot',
            r'www\.',
            r'http',
            r'\.com',
            r'\.ru'
        ]

        for pattern in spam_patterns:
            if re.search(pattern, reviewer_name.lower()):
                raise ValidationError("Пожалуйста, укажите ваше настоящее имя.")

        return reviewer_name

    def clean_reviewer_email(self):
        """✅ Валидация email автора"""
        reviewer_email = self.cleaned_data.get('reviewer_email', '').strip()

        # Для зарегистрированных пользователей email не обязательно
        if not reviewer_email and (not self.user or not self.user.is_authenticated):
            raise ValidationError("Пожалуйста, укажите ваш email.")

        # Если email не указан, но пользователь залогинен - пропускаем валидацию
        if not reviewer_email and self.user and self.user.is_authenticated:
            return reviewer_email

        # Базовая валидация email уже выполняется EmailField
        # Дополнительные проверки на подозрительные домены
        suspicious_domains = [
            'tempmail', 'guerrillamail', '10minutemail', 'mailinator',
            'throwaway', 'temp-mail', 'fakeemail', 'spambox'
        ]

        email_lower = reviewer_email.lower()
        for domain in suspicious_domains:
            if domain in email_lower:
                raise ValidationError("Пожалуйста, используйте постоянный email адрес.")

        return reviewer_email

    def clean_content(self):
        """✅ Валидация содержания отзыва"""
        content = self.cleaned_data.get('content', '').strip()

        if not content:
            raise ValidationError("Пожалуйста, напишите отзыв.")

        if len(content) < 10:
            raise ValidationError("Отзыв слишком короткий. Минимум 10 символов.")

        if len(content) > 2000:
            raise ValidationError("Отзыв слишком длинный. Максимум 2000 символов.")

        # 🛡️ АНТИ-СПАМ: Проверка на спам-слова
        spam_words = getattr(settings, 'SPAM_WORDS', [
            'казино', 'casino', 'gambling', 'buy', 'cheap', 'discount',
            'free', 'viagra', 'porn', 'xxx', 'sex', 'adult',
            'money', 'cash', 'loan', 'credit', 'debt',
            'weight loss', 'miracle', 'guaranteed',
        ])

        content_lower = content.lower()
        found_spam_words = [word for word in spam_words if word in content_lower]

        if found_spam_words:
            raise ValidationError(
                f"Ваш отзыв содержит недопустимые слова: {', '.join(found_spam_words)}. "
                f"Пожалуйста, напишите отзыв о товаре."
            )

        # Проверка на повторяющиеся символы
        if re.search(r'(.)\1{4,}', content):  # 5 одинаковых символов подряд
            raise ValidationError("Отзыв содержит слишком много повторяющихся символов.")

        # Проверка на URL и email в отзыве
        url_pattern = r'https?://|www\.|\.com|\.ru|\.net|\.org'
        if re.search(url_pattern, content_lower):
            raise ValidationError("Ссылки в отзывах запрещены.")

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, content):
            raise ValidationError("Указание контактов в отзывах запрещено.")

        return content

    def clean_stars(self):
        """✅ Валидация оценки"""
        stars = self.cleaned_data.get('stars')

        try:
            stars_int = int(stars)
            if stars_int < 1 or stars_int > 5:
                raise ValidationError("Оценка должна быть от 1 до 5 звезд.")
            return stars_int
        except (ValueError, TypeError):
            raise ValidationError("Некорректная оценка.")

    def clean(self):
        """🛡️ ОБЩАЯ ВАЛИДАЦИЯ ФОРМЫ с анти-спам проверками"""
        cleaned_data = super().clean()

        # 🍯 HONEYPOT: Проверяем ловушки для ботов
        honeypot_name = cleaned_data.get('honeypot_name')
        honeypot_email = cleaned_data.get('honeypot_email')

        if honeypot_name or honeypot_email:
            raise ValidationError("Обнаружена подозрительная активность. Попробуйте еще раз.")

        # ⏱️ ВРЕМЯ ЗАПОЛНЕНИЯ: Проверяем скорость заполнения формы
        form_load_time = cleaned_data.get('form_load_time')
        if form_load_time:
            submit_time = time.time()
            fill_time = submit_time - form_load_time

            # Слишком быстро = бот
            if fill_time < 3:
                raise ValidationError(
                    "Форма заполнена слишком быстро. Пожалуйста, перечитайте отзыв и отправьте снова.")

            # Сохраняем время заполнения для анализа
            cleaned_data['calculated_submit_time'] = fill_time

        return cleaned_data

    def save(self, commit=True):
        """💾 Сохранение отзыва с поддержкой анонимных и зарегистрированных пользователей"""
        review = super().save(commit=False)

        # 👤 Обрабатываем пользователя
        if self.user and self.user.is_authenticated:
            # Для зарегистрированных пользователей
            review.user = self.user

            # Заполняем имя и email из профиля, если не указаны
            if not review.reviewer_name:
                review.reviewer_name = self.user.get_full_name() or self.user.username
            if not review.reviewer_email:
                review.reviewer_email = self.user.email or ""
        else:
            # Для анонимных пользователей
            review.user = None

        # 🔒 Модерация: админы получают автоодобрение, остальные требуют модерации
        if self.user and self.user.is_authenticated and (self.user.is_staff or self.user.is_superuser):
            review.is_approved = True  # Админы получают автоодобрение
        else:
            review.is_approved = False  # Остальные требуют модерации

        if commit:
            review.save()

        return review

    class Meta:
        model = ProductReview
        fields = ['reviewer_name', 'reviewer_email', 'stars', 'content']

        # Скрываем служебные поля из Meta
        exclude = [
            'user', 'content_type', 'object_id', 'date_added',
            'is_approved', 'ip_address', 'user_agent', 'form_submit_time',
            'is_suspicious', 'spam_score', 'moderated_by', 'moderated_at'
        ]


# 🔄 Алиас для совместимости со старым кодом
AnonymousReviewForm = UniversalReviewForm


class ReviewModerationForm(forms.ModelForm):
    """
    👨‍💼 Форма для модерации отзывов администраторами

    Используется в админ-панели для быстрой модерации отзывов
    """

    moderation_action = forms.ChoiceField(
        choices=[
            ('approve', 'Одобрить'),
            ('reject', 'Отклонить'),
            ('mark_suspicious', 'Пометить как подозрительный'),
            ('mark_safe', 'Пометить как безопасный'),
        ],
        widget=forms.RadioSelect(),
        required=True,
        label="Действие модератора"
    )

    moderation_comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        label="Комментарий модератора",
        help_text="Необязательный комментарий о причинах решения"
    )

    class Meta:
        model = ProductReview
        fields = ['is_approved', 'is_suspicious', 'spam_score']
        widgets = {
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_suspicious': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'spam_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


# 📊 ДОПОЛНИТЕЛЬНЫЕ ФОРМЫ ДЛЯ ФИЛЬТРАЦИИ И ПОИСКА

class ReviewFilterForm(forms.Form):
    """🔍 Форма фильтрации отзывов в админ-панели"""

    STATUS_CHOICES = [
        ('', 'Все отзывы'),
        ('pending', 'На модерации'),
        ('approved', 'Одобренные'),
        ('suspicious', 'Подозрительные'),
        ('anonymous', 'Анонимные'),
    ]

    RATING_CHOICES = [
        ('', 'Любая оценка'),
        ('1', '1 звезда'),
        ('2', '2 звезды'),
        ('3', '3 звезды'),
        ('4', '4 звезды'),
        ('5', '5 звезд'),
        ('low', '1-2 звезды'),
        ('high', '4-5 звезд'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Статус"
    )

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Оценка"
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по тексту отзыва...'
        }),
        label="Поиск"
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="С даты"
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="По дату"
    )