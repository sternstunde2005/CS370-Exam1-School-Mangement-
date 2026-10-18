from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CourseForm, DepartmentForm, FacultyForm, ProgramForm
from .models import Course, Department, Faculty, Program


def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.role == "admin")


@login_required
def index(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    return render(
        request,
        "academics/index.html",
        {
            "departments": Department.objects.order_by("name"),
            "programs": Program.objects.select_related("department").order_by("name"),
            "courses": Course.objects.select_related("department").order_by("code"),
            "faculties": Faculty.objects.select_related("department", "user").order_by("employee_id"),
        },
    )


@login_required
def department_create(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    form = DepartmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department created.")
        return redirect("academics:index")
    return render(request, "academics/form.html", {"form": form, "title": "Add Department"})


@login_required
def department_edit(request, pk):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    department = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=department)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department updated.")
        return redirect("academics:index")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Department"})


@login_required
def program_create(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    form = ProgramForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Program created.")
        return redirect("academics:index")
    return render(request, "academics/form.html", {"form": form, "title": "Add Program"})


@login_required
def program_edit(request, pk):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    program = get_object_or_404(Program, pk=pk)
    form = ProgramForm(request.POST or None, instance=program)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Program updated.")
        return redirect("academics:index")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Program"})


@login_required
def course_create(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    form = CourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Course created.")
        return redirect("academics:index")
    return render(request, "academics/form.html", {"form": form, "title": "Add Course"})


@login_required
def course_edit(request, pk):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, instance=course)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Course updated.")
        return redirect("academics:index")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Course"})


@login_required
def faculty_create(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    form = FacultyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Faculty created.")
        return redirect("academics:index")
    return render(request, "academics/form.html", {"form": form, "title": "Add Faculty"})


@login_required
def faculty_edit(request, pk):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Not allowed")
    faculty = get_object_or_404(Faculty, pk=pk)
    form = FacultyForm(request.POST or None, instance=faculty)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Faculty updated.")
        return redirect("academics:index")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Faculty"})

# Create your views here.
