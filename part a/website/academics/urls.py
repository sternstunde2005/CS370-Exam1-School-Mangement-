from django.urls import path

from . import views

app_name = "academics"

urlpatterns = [
    path("", views.index, name="index"),
    path("departments/add/", views.department_create, name="department_create"),
    path("departments/<int:pk>/edit/", views.department_edit, name="department_edit"),
    path("programs/add/", views.program_create, name="program_create"),
    path("programs/<int:pk>/edit/", views.program_edit, name="program_edit"),
    path("courses/add/", views.course_create, name="course_create"),
    path("courses/<int:pk>/edit/", views.course_edit, name="course_edit"),
    path("faculty/add/", views.faculty_create, name="faculty_create"),
    path("faculty/<int:pk>/edit/", views.faculty_edit, name="faculty_edit"),
]
