from django import forms

from academics.models import Department, Program

from .models import Address, ContactInformation, EmergencyContact, Student


class DateInput(forms.DateInput):
    input_type = "date"


class StudentForm(forms.ModelForm):
    ACADEMIC_YEAR_CHOICES = [("", "Select Academic Year")] + [
        (str(year), str(year)) for year in range(2000, 2036)
    ]

    SEMESTER_CHOICES = [
        ("", "Select Semester"),
        ("1", "1"),
        ("2", "2"),
        ("3", "3"),
        ("4", "4"),
        ("5", "5"),
        ("6", "6"),
        ("7", "7"),
        ("8", "8"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["department"].queryset = Department.objects.filter(is_active=True).order_by("name")
        self.fields["department"].empty_label = "Select Department"
        self.fields["department"].required = True
        self.fields["program"].queryset = Program.objects.filter(is_active=True).select_related("department").order_by("name")
        self.fields["program"].empty_label = "Select Program"
        self.fields["program"].required = True
        self.fields["academic_year"].widget = forms.Select(choices=self.ACADEMIC_YEAR_CHOICES)
        self.fields["semester"].widget = forms.Select(choices=self.SEMESTER_CHOICES)

        if self.instance and self.instance.pk:
            for field_name in ["academic_year", "semester"]:
                current_value = getattr(self.instance, field_name, "")
                if current_value and current_value not in dict(self.fields[field_name].widget.choices):
                    self.fields[field_name].widget.choices = list(self.fields[field_name].widget.choices) + [
                        (current_value, current_value)
                    ]

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update(
                    {
                        "class": "block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm file:mr-4 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-slate-700",
                    }
                )
            else:
                field.widget.attrs.update(
                    {
                        "class": "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-slate-600 focus:ring-2 focus:ring-slate-200",
                    }
                )

            if name in ["date_of_birth", "enrollment_date"]:
                field.widget.attrs.update({"max": "2100-12-31"})

            field.label = field.label.replace("_", " ").title()

    class Meta:
        model = Student
        exclude = ("user", "created_at", "updated_at")
        widgets = {
            "date_of_birth": DateInput(attrs={"placeholder": "YYYY-MM-DD"}),
            "enrollment_date": DateInput(attrs={"placeholder": "YYYY-MM-DD"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get("department")
        program = cleaned_data.get("program")
        if department and program and program.department_id != department.id:
            self.add_error("program", "Select a program that belongs to the selected department.")
        return cleaned_data


class ContactInformationForm(forms.ModelForm):
    class Meta:
        model = ContactInformation
        exclude = ("student",)


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ("student", "address_type")


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        exclude = ("student",)
