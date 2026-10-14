"""Формы проверяют данные регистрации, количество товара и данные получателя."""
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label='Email')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class QuantityForm(forms.Form):
    quantity = forms.IntegerField(label='Количество', min_value=1, max_value=10, initial=1)

class CheckoutForm(forms.ModelForm):
    token = forms.UUIDField(widget=forms.HiddenInput)

    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'email', 'address', 'comment']
        widgets = {'comment': forms.Textarea(attrs={'rows': 3})}

    def clean_phone(self):
        value = self.cleaned_data['phone'].strip()
        if not re.fullmatch(r'[+\d()\s-]+', value) or not 10 <= len(re.sub(r'\D', '', value)) <= 15:
            raise forms.ValidationError('Введите телефон из 10–15 цифр.')
        return value
