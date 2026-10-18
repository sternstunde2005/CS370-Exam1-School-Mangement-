from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        FACULTY = "faculty", "Faculty"
        STUDENT = "student", "Student"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT, db_index=True)
    email_verified = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)

    def is_student(self):
        return self.role == self.Role.STUDENT

    def is_faculty(self):
        return self.role == self.Role.FACULTY

# Create your models here.
