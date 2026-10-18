from django import forms

from academics.models import Department

from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="All departments",
    )

    class Meta:
        model = Announcement
        fields = ["title", "description", "publish_date", "expiry_date", "department", "semester", "is_active"]
        widgets = {
            "publish_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }
