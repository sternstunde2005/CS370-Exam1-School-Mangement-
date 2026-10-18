from django.urls import path

from .views import export_students_csv, reports_home

app_name = "reports"

urlpatterns = [
    path("", reports_home, name="home"),
    path("students/csv/", export_students_csv, name="students_csv"),
]
