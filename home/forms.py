# 📁 home/forms.py
# 📧 Формы для обратной связи и контактов
# ✅ ContactForm для отправки сообщений через сайт

from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """📧 Форма обратной связи для клиентов"""

    consent = forms.BooleanField(
        required=True,
        label='',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'consent-checkbox'
        }),
        help_text='Я подтверждаю свое согласие с <a href="/privacy-policy/" target="_blank">политикой обработки персональных данных</a>',
        error_messages={
            'required': 'Необходимо дать согласие на обработку персональных данных'
        }
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+375 (29) 123-45-67',
                'type': 'tel'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Тема сообщения (например: Вопрос по товару)',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Опишите ваш вопрос или проблему подробнее...',
                'required': True
            }),
        }

        labels = {
            'name': 'Имя *',
            'email': 'Email *',
            'phone': 'Телефон',
            'subject': 'Тема сообщения',
            'message': 'Сообщение *',
        }

    def clean_name(self):
        """✅ Валидация имени"""
        name = self.cleaned_data.get('name')
        if len(name) < 2:
            raise forms.ValidationError("Имя должно содержать минимум 2 символа")
        return name

    def clean_message(self):
        """✅ Валидация сообщения"""
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise forms.ValidationError("Сообщение должно содержать минимум 10 символов")
        return message

    def clean_phone(self):
        """📞 Валидация телефона (если указан)"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Убираем все кроме цифр и +
            cleaned_phone = ''.join(char for char in phone if char.isdigit() or char == '+')
            if len(cleaned_phone) < 7:
                raise forms.ValidationError("Некорректный формат телефона")
            return cleaned_phone
        return phone

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Делаем обязательные поля более заметными
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['message'].required = True

        # Добавляем help_text для лучшего UX
        self.fields['phone'].help_text = "Необязательно, но поможет нам связаться с вами быстрее"
        self.fields['subject'].help_text = "Кратко опишите суть вопроса"
        self.fields['message'].help_text = "Подробно опишите ваш вопрос или проблему"


# 🔧 ОСОБЕННОСТИ ФОРМЫ:
# ✅ Использует Bootstrap классы для красивого оформления
# ✅ Подходящие placeholder'ы на русском языке
# ✅ Валидация полей (имя, сообщение, телефон)
# ✅ Автоматическая очистка телефона от лишних символов
# ✅ Подсказки для пользователей (help_text)
# ✅ Обязательные поля помечены звездочкой
# ✅ Совместимость с существующим дизайном сайта