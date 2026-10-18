from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "role", "is_active")


class StudentSelfUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 rounded border-slate-300 text-brand-700 focus:ring-brand-600",
            }
        ),
    )
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-[15px] text-slate-900 outline-none transition focus:border-blue-700 focus:ring-4 focus:ring-blue-100",
                "placeholder": "Enter username",
                "autocomplete": "username",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-[15px] text-slate-900 outline-none transition focus:border-blue-700 focus:ring-4 focus:ring-blue-100",
                "placeholder": "Enter password",
                "autocomplete": "current-password",
            }
        )
    )
