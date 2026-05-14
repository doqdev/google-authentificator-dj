from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class LoginForm(AuthenticationForm):
    # Django's default AuthenticationForm already validates username/password.
    pass


class TOTPCodeForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6, strip=True)
