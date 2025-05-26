from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from accounts.models import Profile
from home.models import ShippingAddress


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_image', 'bio']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = '__all__'
        exclude = ['user', 'current_address']  # Исключаем user и current_address


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Текущий пароль",  # Current password -> Текущий пароль
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label="Новый пароль",  # New password -> Новый пароль
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label="Подтверждение нового пароля",  # New password confirmation -> Подтверждение нового пароля
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )