from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'email', 'password1', 'password2']
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется!")
        return email

class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Электронная почта', widget=forms.EmailInput(attrs={'autofocus': True}))