from django import forms

from students.models import Student

from .models import FeeStructure, Payment


class FeeStructureForm(forms.ModelForm):
    academic_year = forms.ChoiceField(
        choices=[("", "Select Academic Year")] + [(str(y), str(y)) for y in range(2000, 2036)],
    )
    semester = forms.ChoiceField(
        choices=[("", "Select Semester")] + [(str(i), str(i)) for i in range(1, 9)],
    )

    class Meta:
        model = FeeStructure
        fields = ["fee_type", "amount", "academic_year", "semester"]


class PaymentForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.order_by("student_id"),
        label="Student",
        empty_label="Select student",
    )

    class Meta:
        model = Payment
        fields = ["student", "fee_structure", "amount_paid", "paid_on", "reference"]
        widgets = {"paid_on": forms.DateInput(attrs={"type": "date"})}
