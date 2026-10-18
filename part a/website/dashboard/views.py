from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render

from academics.models import Course, Department, Program
from attendance.models import AttendanceRecord
from audits.models import AuditLog
from fees.models import FeeStructure, Payment
from gradebook.models import GradeRecord
from helpdesk.models import Ticket
from notifications_center.models import Notification
from registration.models import CourseRegistration
from students.models import Student


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return render(request, "home.html")


@login_required
def home(request):
    if request.user.is_staff or request.user.role == "admin":
        total = Student.objects.count()
        active = Student.objects.filter(status=Student.Status.ACTIVE).count()
        inactive = Student.objects.filter(status=Student.Status.INACTIVE).count()
        graduated = Student.objects.filter(status=Student.Status.GRADUATED).count()
        suspended = Student.objects.filter(status=Student.Status.SUSPENDED).count()
        by_department = list(Student.objects.values("department__name").annotate(total=Count("id")).order_by("department__name"))
        by_year = list(Student.objects.values("academic_year").annotate(total=Count("id")).order_by("academic_year"))
        recent = Student.objects.select_related("department").order_by("-created_at")[:5]
        updates = AuditLog.objects.filter(action__in=["profile_update", "student_create"]).select_related("user")[:10]
        module_stats = {
            "departments": Department.objects.filter(is_active=True).count(),
            "programs": Program.objects.filter(is_active=True).count(),
            "courses": Course.objects.count(),
            "active_courses": Course.objects.filter(status=Course.Status.ACTIVE).count(),
            "open_tickets": Ticket.objects.filter(status=Ticket.Status.OPEN).count(),
            "resolved_tickets": Ticket.objects.filter(status=Ticket.Status.RESOLVED).count(),
        }
        return render(
            request,
            "dashboard/admin_dashboard.html",
            {
                "total": total,
                "active": active,
                "inactive": inactive,
                "graduated": graduated,
                "suspended": suspended,
                "by_department": by_department,
                "by_year": by_year,
                "recent": recent,
                "updates": updates,
                "module_stats": module_stats,
            },
        )

    student = request.user.student_profile

    fields = [
        student.student_id,
        student.first_name,
        student.last_name,
        student.registration_number,
        student.department,
        student.program,
        student.academic_year,
    ]
    completion = int((sum(bool(f) for f in fields) / len(fields)) * 100)

    activity = AuditLog.objects.filter(user=request.user)[:10]

    attendance_records = AttendanceRecord.objects.filter(student_id=student.student_id)
    attendance_total = attendance_records.count()
    attendance_present = attendance_records.filter(
        status__in=["present", "late", "excused"]
    ).count()
    attendance_pct = round((attendance_present / attendance_total) * 100, 1) if attendance_total else 0

    expected_fees = FeeStructure.objects.filter(
        academic_year=student.academic_year,
        semester=student.semester,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    paid_fees = Payment.objects.filter(student=student).aggregate(total=Sum("amount_paid"))["total"] or Decimal("0")
    outstanding_fees = max(expected_fees - paid_fees, Decimal("0"))

    active_registrations = CourseRegistration.objects.filter(
        student=student,
        status=CourseRegistration.Status.APPROVED,
    ).count()

    open_tickets = Ticket.objects.filter(
        student=student,
        status__in=[Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS],
    ).count()

    unread_notifications = Notification.objects.filter(student=student, is_read=False).count()

    recent_grades = GradeRecord.objects.filter(
        student_id=student.student_id,
        exam__is_published=True,
    ).select_related("exam").order_by("-exam__exam_date")[:5]

    return render(request, "dashboard/student_dashboard.html", {
        "student": student,
        "completion": completion,
        "activity": activity,
        "attendance_pct": attendance_pct,
        "expected_fees": expected_fees,
        "paid_fees": paid_fees,
        "outstanding_fees": outstanding_fees,
        "active_registrations": active_registrations,
        "open_tickets": open_tickets,
        "unread_notifications": unread_notifications,
        "recent_grades": recent_grades,
    })

# Create your views here.
