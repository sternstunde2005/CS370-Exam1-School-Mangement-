"""Create fictional demonstration data without overwriting existing records."""

from datetime import date, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from academics.models import Course, Department, Faculty, Program
from attendance.models import AttendanceRecord, AttendanceSession, Enrollment
from fees.models import FeeStructure, Payment
from gradebook.models import Exam, GradeRecord
from gradebook.views import _grade_from_percentage
from notifications_center.models import Announcement, Notification
from registration.models import CourseOffering, CourseRegistration, RegistrationWindow
from students.models import Address, ContactInformation, EmergencyContact, Student


class Command(BaseCommand):
    help = "Create fictional Fall 2026 Part A demo data; preserve existing records and passwords."

    @transaction.atomic
    def handle(self, *args, **options):
        year = "2026-2027"
        semester = "Fall 2026"
        created_users = []

        def account(username, password, **defaults):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.test", **defaults},
            )
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
                created_users.append(username)
            return user

        account(
            "admin", "Admin@12345", first_name="Demo", last_name="Administrator",
            role=User.Role.ADMIN, is_staff=True, is_superuser=True,
        )
        # The upstream UI checks is_staff for staff pages. This demo setting does
        # not implement RBAC or claim that faculty have separate staff permissions.
        faculty_user = account(
            "faculty1", "Faculty@12345", first_name="Taylor", last_name="Instructor",
            role=User.Role.FACULTY, is_staff=True, is_superuser=False,
        )

        computer_science, _ = Department.objects.get_or_create(
            code="CS", defaults={"name": "Computer Science"},
        )
        business, _ = Department.objects.get_or_create(
            code="BUS", defaults={"name": "Business Studies"},
        )
        cs_program, _ = Program.objects.get_or_create(
            code="BSC-CS",
            defaults={"name": "BSc Computer Science", "department": computer_science,
                      "duration_semesters": 8},
        )
        business_program, _ = Program.objects.get_or_create(
            code="BBA",
            defaults={"name": "Bachelor of Business Administration", "department": business,
                      "duration_semesters": 8},
        )
        faculty, _ = Faculty.objects.get_or_create(
            user=faculty_user,
            defaults={"employee_id": "FAC-DEMO-001", "full_name": "Taylor Instructor",
                      "email": "faculty1@example.test", "department": computer_science,
                      "title": "Demo Lecturer"},
        )

        courses = {}
        for code, name, department in [
            ("CS101", "Introduction to Programming", computer_science),
            ("CS102", "Database Fundamentals", computer_science),
            ("BUS101", "Business Information Systems", business),
        ]:
            courses[code], _ = Course.objects.get_or_create(
                code=code,
                defaults={"name": name, "department": department, "semester": semester,
                          "credit_hours": Decimal("3.0"), "instructor": faculty,
                          "instructor_name": faculty.full_name},
            )

        students = []
        student_course_codes = [
            ("CS101", "CS102"), ("CS101", "CS102"), ("BUS101",),
        ]
        for index, (first_name, last_name, department, program) in enumerate([
            ("Alex", "Demo", computer_science, cs_program),
            ("Morgan", "Example", computer_science, cs_program),
            ("Jamie", "Sample", business, business_program),
        ], start=1):
            username = f"student{index}"
            user = account(
                username, "Student@12345", first_name=first_name, last_name=last_name,
                role=User.Role.STUDENT, is_staff=False, is_superuser=False,
            )
            student, _ = Student.objects.get_or_create(
                user=user,
                defaults={"student_id": f"STU-{index:04d}", "first_name": first_name,
                          "last_name": last_name, "registration_number": f"REG-2026-{index:04d}",
                          "date_of_birth": date(2006, index + 1, 10),
                          "nationality": "Exampleland (fictional)",
                          "department": department, "program": program,
                          "academic_year": year, "semester": semester,
                          "enrollment_date": date(2026, 9, 1)},
            )
            students.append(student)
            ContactInformation.objects.get_or_create(
                student=student,
                defaults={"primary_email": f"{username}@example.test",
                          "mobile_number": f"+1202555010{index}"},
            )
            for address_type in (Address.AddressType.PRESENT, Address.AddressType.PERMANENT):
                Address.objects.get_or_create(
                    student=student, address_type=address_type,
                    defaults={"address_line_1": f"{100 + index} Demo Lane",
                              "address_line_2": "Fictional demonstration address",
                              "city": "Example City", "state": "Example State",
                              "postal_code": f"0000{index}", "country": "Exampleland"},
                )
            EmergencyContact.objects.get_or_create(
                student=student,
                defaults={"contact_name": f"Casey {last_name}", "relationship": "Guardian",
                          "mobile_number": f"+1202555011{index}",
                          "email_address": f"guardian{index}@example.test"},
            )

        window, _ = RegistrationWindow.objects.get_or_create(
            name="Fall 2026 Demo Registration",
            defaults={"starts_at": timezone.make_aware(datetime(2026, 8, 1)),
                      "ends_at": timezone.make_aware(datetime(2026, 12, 31, 23, 59, 59))},
        )
        offerings = {}
        for code, course in courses.items():
            offerings[code], _ = CourseOffering.objects.get_or_create(
                course=course, semester=semester, registration_window=window,
                defaults={"course_code_text": code, "capacity": 40},
            )

        enrollments = {}
        for student, codes in zip(students, student_course_codes):
            for code in codes:
                CourseRegistration.objects.get_or_create(
                    student=student, offering=offerings[code],
                    defaults={"student_id_text": student.student_id,
                              "status": CourseRegistration.Status.APPROVED},
                )
                enrollments[(student.pk, code)], _ = Enrollment.objects.get_or_create(
                    course=courses[code], student_id=student.student_id,
                )

        marks = {"CS101": (86, 73, None), "CS102": (78, 67, None),
                 "BUS101": (None, None, 82)}
        for offset, (code, course) in enumerate(courses.items()):
            exam, _ = Exam.objects.get_or_create(
                course_code=code, title=f"{code} Fall 2026 Midterm (Demo)",
                defaults={"assessment_type": Exam.AssessmentType.MIDTERM, "total_marks": 100,
                          "exam_date": date(2026, 10, 12 + offset), "is_published": True},
            )
            for student, mark in zip(students, marks[code]):
                if mark is None:
                    continue
                letter, points = _grade_from_percentage(mark)
                GradeRecord.objects.get_or_create(
                    exam=exam, student_id=student.student_id,
                    defaults={"marks_obtained": Decimal(mark), "letter_grade": letter,
                              "grade_points": points},
                )

        tuition, _ = FeeStructure.objects.get_or_create(
            fee_type=FeeStructure.FeeType.TUITION, academic_year=year, semester=semester,
            defaults={"amount": Decimal("2400.00")},
        )
        lab, _ = FeeStructure.objects.get_or_create(
            fee_type=FeeStructure.FeeType.LAB, academic_year=year, semester=semester,
            defaults={"amount": Decimal("200.00")},
        )
        for index, (student, tuition_paid) in enumerate(
            zip(students, ("1500.00", "2000.00", "1200.00")), start=1
        ):
            for fee, amount, suffix in [(tuition, tuition_paid, "TUITION"), (lab, "200.00", "LAB")]:
                Payment.objects.get_or_create(
                    reference=f"DEMO-2026-{index:04d}-{suffix}",
                    defaults={"student": student, "student_id_text": student.student_id,
                              "fee_structure": fee, "amount_paid": Decimal(amount),
                              "paid_on": date(2026, 9, 5 + index)},
                )

        time_slots = {
            "CS101": AttendanceSession.TimeSlot.MORNING,
            "CS102": AttendanceSession.TimeSlot.MID_MORNING,
            "BUS101": AttendanceSession.TimeSlot.AFTERNOON,
        }
        for code, course in courses.items():
            program = business_program if code == "BUS101" else cs_program
            for session_index, day in enumerate((21, 23, 28)):
                session, _ = AttendanceSession.objects.get_or_create(
                    course=course, session_date=date(2026, 9, day),
                    time_slot=time_slots[code],
                    defaults={"department": course.department, "program": program,
                              "semester": semester, "instructor": faculty,
                              "instructor_name": faculty.full_name},
                )
                for student_index, student in enumerate(students):
                    enrollment = enrollments.get((student.pk, code))
                    if enrollment is None:
                        continue
                    status = AttendanceRecord.Status.PRESENT
                    if student_index == 1 and session_index == 1:
                        status = AttendanceRecord.Status.LATE
                    elif student_index == 2 and session_index == 2:
                        status = AttendanceRecord.Status.EXCUSED
                    AttendanceRecord.objects.get_or_create(
                        session=session, student_id=student.student_id,
                        defaults={"enrollment": enrollment, "status": status,
                                  "remarks": "Fictional demo attendance"},
                    )

        Announcement.objects.get_or_create(
            title="Welcome to the Fall 2026 demonstration",
            defaults={"description": "All accounts, student profiles, grades, payments, and "
                      "contact details in this demonstration are fictional. Sample midterm "
                      "results and fee statements are available in the student portal.",
                      "publish_date": date(2026, 9, 1), "expiry_date": date(2026, 12, 31),
                      "semester": semester},
        )
        for student in students:
            Notification.objects.get_or_create(
                student=student, title="Your demo student portal is ready",
                defaults={"student_id_text": student.student_id,
                          "message": "Explore your profile, approved courses, published "
                          "midterm results, attendance, and sample fee payments. All data is fictional."},
            )

        self.stdout.write(self.style.SUCCESS(
            "Part A demo data is ready. Existing records and passwords were preserved."
        ))
        self.stdout.write("New accounts: " + (", ".join(created_users) or "none"))
