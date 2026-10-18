import csv

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden

from students.models import Student


def _admin(user):
    return user.is_staff or user.role == "admin"


@login_required
def reports_home(request):
    if not _admin(request.user):
        return HttpResponseForbidden("Not allowed")
    return HttpResponse("Reports module: use /reports/students/csv/ for export.")


@login_required
def export_students_csv(request):
    if not _admin(request.user):
        return HttpResponseForbidden("Not allowed")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="student_directory.csv"'
    writer = csv.writer(response)
    writer.writerow(["Student ID", "Name", "Reg. No", "Department", "Year", "Status"])
    for s in Student.objects.all().iterator():
        writer.writerow([s.student_id, f"{s.first_name} {s.last_name}", s.registration_number, s.department.name if s.department else "", s.academic_year, s.status])
    return response

# Create your views here.
