from django.conf import settings
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models


def profile_photo_upload_to(instance, filename):
    return f"students/{instance.student_id}/profile/{filename}"


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        GRADUATED = "graduated", "Graduated"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(max_length=30, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    profile_photo = models.ImageField(
        upload_to=profile_photo_upload_to,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])],
    )

    registration_number = models.CharField(max_length=50, unique=True, db_index=True)
    department = models.ForeignKey("academics.Department", on_delete=models.PROTECT, null=True, blank=True, related_name="students")
    program = models.ForeignKey("academics.Program", on_delete=models.PROTECT, null=True, blank=True, related_name="students")
    academic_year = models.CharField(max_length=20, db_index=True)
    semester = models.CharField(max_length=20)
    enrollment_date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["department", "academic_year"], name="students_st_departm_906e53_idx"),
        ]

    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"


class ContactInformation(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="contact")
    primary_email = models.EmailField(unique=True)
    secondary_email = models.EmailField(blank=True)
    mobile_number = models.CharField(max_length=20, validators=[RegexValidator(r"^[0-9+\-() ]+$")])
    alternate_mobile_number = models.CharField(max_length=20, blank=True, validators=[RegexValidator(r"^[0-9+\-() ]*$")])


class Address(models.Model):
    class AddressType(models.TextChoices):
        PRESENT = "present", "Present"
        PERMANENT = "permanent", "Permanent"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(max_length=20, choices=AddressType.choices)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    class Meta:
        unique_together = ("student", "address_type")


class EmergencyContact(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="emergency_contact")
    contact_name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=80)
    mobile_number = models.CharField(max_length=20)
    email_address = models.EmailField(blank=True)

# Create your models here.
