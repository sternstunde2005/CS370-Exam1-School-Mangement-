from django import forms
from django.contrib.auth.password_validation import validate_password

from accounts.models import User

from .models import Course, Department, Faculty, Program


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "code", "is_active"]


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ["department", "name", "code", "duration_semesters", "is_active"]


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["department", "code", "name", "credit_hours", "semester", "instructor", "status"]


class FacultyForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Existing user account",
        help_text="Optional. Pick an existing user (Faculty role) to link, or fill in the new user fields below to create one.",
    )
    new_username = forms.CharField(
        max_length=150,
        required=False,
        label="New username",
        help_text="Used only when creating a new user account.",
    )
    new_password = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.PasswordInput(render_value=False),
        label="New password",
        help_text="Used only when creating a new user account.",
    )
    new_first_name = forms.CharField(max_length=150, required=False, label="New user first name")
    new_last_name = forms.CharField(max_length=150, required=False, label="New user last name")
    new_email = forms.EmailField(required=False, label="New user email")

    class Meta:
        model = Faculty
        fields = [
            "user",
            "new_username",
            "new_password",
            "new_first_name",
            "new_last_name",
            "new_email",
            "employee_id",
            "full_name",
            "email",
            "department",
            "title",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = User.objects.filter(role=User.Role.FACULTY)
        if self.instance and self.instance.pk and self.instance.user_id:
            qs = (qs | User.objects.filter(pk=self.instance.user_id)).distinct()
        else:
            qs = qs.filter(faculty_profile__isnull=True)
        self.fields["user"].queryset = qs
        if not (self.instance and self.instance.pk):
            for f in ("new_username", "new_password"):
                self.fields[f].required = True

    def clean(self):
        cleaned = super().clean()
        user = cleaned.get("user")
        new_username = (cleaned.get("new_username") or "").strip()
        new_password = cleaned.get("new_password") or ""
        is_editing = bool(self.instance and self.instance.pk)

        if is_editing and not user:
            user = self.instance.user
            cleaned["user"] = user

        if not user and not new_username:
            raise forms.ValidationError(
                "Select an existing user account or fill in the new username and password to create one."
            )

        if new_username:
            if User.objects.filter(username__iexact=new_username).exists():
                self.add_error("new_username", "A user with that username already exists.")
            if not new_password:
                self.add_error("new_password", "Password is required when creating a new user.")
            else:
                validate_password(new_password)

        cleaned["_resolved_user"] = user
        return cleaned

    def save(self, commit=True):
        self.instance = super().save(commit=False)
        user = self.cleaned_data.get("_resolved_user")
        if not user:
            new_username = (self.cleaned_data.get("new_username") or "").strip()
            new_password = self.cleaned_data.get("new_password") or ""
            user = User(
                username=new_username,
                first_name=self.cleaned_data.get("new_first_name") or "",
                last_name=self.cleaned_data.get("new_last_name") or "",
                email=self.cleaned_data.get("new_email") or "",
                role=User.Role.FACULTY,
                must_change_password=True,
            )
            user.set_password(new_password)
            user.save()
        self.instance.user = user
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
