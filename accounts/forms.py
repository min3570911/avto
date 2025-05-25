# 📁 accounts/forms.py - ИСПРАВЛЕННАЯ ВЕРСИЯ без django_countries
# 🧹 Упрощенные формы для админки (без регистрации пользователей)

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from accounts.models import Profile

# 🗑️ УДАЛЕНО: from home.models import ShippingAddress
# 🗑️ УДАЛЕНО: from django_countries.fields import CountryField


class UserProfileForm(forms.ModelForm):
    """👤 Форма профиля пользователя (только для админов)"""
    class Meta:
        model = Profile
        fields = ['profile_image', 'bio']
        widgets = {
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            })
        }
        labels = {
            'profile_image': 'Фото профиля',
            'bio': 'О себе'
        }


class UserUpdateForm(forms.ModelForm):
    """📝 Форма обновления данных пользователя"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Фамилия'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            })
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия', 
            'email': 'Email'
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """🔒 Форма смены пароля с красивым оформлением"""
    old_password = forms.CharField(
        label="Текущий пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите текущий пароль'
        }),
        help_text="Для безопасности введите ваш текущий пароль"
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новый пароль'
        }),
        help_text="Пароль должен содержать минимум 8 символов"
    )
    new_password2 = forms.CharField(
        label="Подтверждение нового пароля",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите новый пароль'
        }),
        help_text="Введите новый пароль еще раз для подтверждения"
    )


# 🗑️ УДАЛЕНО: ShippingAddressForm (не нужен в упрощенном проекте)
# Адреса доставки теперь указываются прямо в заказах

# ℹ️ ПРИМЕЧАНИЕ:
# В упрощенном проекте без регистрации пользователей
# не нужны сложные формы адресов доставки