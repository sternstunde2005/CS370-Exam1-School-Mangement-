r"""Reproduce Part A observations against a disposable database and media folder.

Run from the delivered project folder:
    runtime\python.exe tools\assess_part_a.py

A successful exit means the documented insecure behaviors were reproduced;
it does NOT mean the application passed a security audit. No website source,
demo database, demo user, or real uploaded file is changed by this script.
"""

from __future__ import annotations

import importlib
import json
import secrets
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
WEBSITE = ROOT / "website"
EVIDENCE = ROOT / "evidence" / "security-assessment.json"
UPSTREAM_SHA = "ecbffaa293753af50d93eb052ac94d87d28d0845"
UPSTREAM = "https://github.com/tasmiul/student-management-system-django"


def source(path: str, start: int, end: int | None = None) -> dict:
    return {
        "path": "website/" + path,
        "lines": [start, end or start],
        "upstream_url": f"{UPSTREAM}/blob/{UPSTREAM_SHA}/{path}#L{start}"
        + (f"-L{end}" if end and end != start else ""),
    }


def run_checks(temp_root: Path) -> dict:
    sys.path.insert(0, str(WEBSITE))
    upstream_settings = importlib.import_module("sims.settings")
    configuration = {
        name: getattr(upstream_settings, name)
        for name in dir(upstream_settings)
        if name.isupper()
    }
    temporary_database = temp_root / "assessment.sqlite3"
    temporary_media = temp_root / "media"
    temporary_media.mkdir()
    configuration.update(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": str(temporary_database),
            }
        },
        MEDIA_ROOT=str(temporary_media),
        ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
        # Match the upstream development default for the media-route test.
        DEBUG=True,
        # Ephemeral signing material is not written to the evidence report.
        SECRET_KEY=secrets.token_urlsafe(48),
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )

    from django.conf import settings

    if settings.configured:
        raise RuntimeError("Refusing to run: Django was configured before isolation.")
    settings.configure(**configuration)

    import django

    django.setup()
    from django.contrib.auth import get_user_model
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.core.management import call_command
    from django.db import connections
    from django.test import Client
    from django.urls import reverse
    from django.utils import timezone

    from academics.models import Course, Department, Program
    from documents.models import Document
    from registration.models import CourseOffering, CourseRegistration, RegistrationWindow
    from students.models import Student

    configured_database = Path(connections["default"].settings_dict["NAME"]).resolve()
    if configured_database != temporary_database.resolve():
        raise RuntimeError("Refusing to run: database is not the disposable database.")
    if configured_database == (WEBSITE / "db.sqlite3").resolve():
        raise RuntimeError("Refusing to touch the delivered demonstration database.")

    try:
        call_command("migrate", interactive=False, verbosity=0)
        User = get_user_model()
        student_password = secrets.token_urlsafe(24)
        admin = User.objects.create_user(
            username="parta_test_admin",
            password=secrets.token_urlsafe(24),
            role="admin",
            is_staff=True,
        )
        student_user = User.objects.create_user(
            username="parta_test_student",
            password=student_password,
            role="student",
        )
        department = Department.objects.create(name="Synthetic Test Department", code="TEST")
        program = Program.objects.create(department=department, name="Synthetic Test Program", code="TST")
        student = Student.objects.create(
            user=student_user,
            student_id="PARTA-TEST-001",
            first_name="Synthetic",
            last_name="Student",
            registration_number="PARTA-REG-001",
            department=department,
            program=program,
            academic_year="2026",
            semester="1",
            enrollment_date=timezone.localdate(),
        )
        anonymous = Client(enforce_csrf_checks=True)
        administrator = Client(enforce_csrf_checks=True)
        administrator.force_login(admin)
        student_client = Client(enforce_csrf_checks=True)
        student_client.force_login(student_user)

        # A1: listing authorization does not protect the file-serving route.
        marker = b"Part A synthetic private document. No personal or real data.\n"
        document = Document.objects.create(
            title="PARTA-PRIVATE-SYNTHETIC-DOCUMENT",
            category=Document.Category.NOTICE,
            is_public=False,
            file=SimpleUploadedFile("parta-private-test.txt", marker, content_type="text/plain"),
        )
        anonymous_listing = anonymous.get(reverse("documents:index"))
        student_listing = student_client.get(reverse("documents:index"))
        download = anonymous.get(document.file.url)
        downloaded_body = b"".join(download.streaming_content) if download.streaming else download.content
        download_status = download.status_code
        download.close()
        private_media_reproduced = download_status == 200 and downloaded_body == marker

        # A2: the CSRF middleware rejects an unprotected POST but permits GET.
        change_status_url = reverse("students:toggle_status", args=[student.pk, "suspended"])
        before_status = student.status
        blocked_post = administrator.post(change_status_url)
        student.refresh_from_db()
        status_after_post = student.status
        state_changing_get = administrator.get(change_status_url)
        student.refresh_from_db()
        after_status = student.status
        student_user.refresh_from_db()
        status_get_reproduced = (
            blocked_post.status_code == 403
            and status_after_post == before_status
            and state_changing_get.status_code == 302
            and after_status == "suspended"
        )
        suspended_user_still_active = student_user.is_active
        # Restore only this disposable fixture so A3 is independent of status.
        student.status = Student.Status.ACTIVE
        student.save(update_fields=["status"])

        # A3: the action endpoint accepts an offering excluded by its window.
        now = timezone.now()
        window = RegistrationWindow.objects.create(
            name="Synthetic expired window",
            starts_at=now - timedelta(days=30),
            ends_at=now - timedelta(days=1),
            is_active=True,
        )
        course = Course.objects.create(
            department=department,
            code="PARTA-EXPIRED-101",
            name="Synthetic Expired Course",
            credit_hours="3.0",
            semester="1",
        )
        offering = CourseOffering.objects.create(
            course=course, semester="1", capacity=1, registration_window=window
        )
        registration_page = student_client.get(reverse("registration:index"))
        hidden_from_listing = course.code not in registration_page.content.decode("utf-8")
        expired_registration = student_client.get(reverse("registration:register_course", args=[offering.pk]))
        registered = CourseRegistration.objects.filter(student=student, offering=offering).first()
        expired_registration_reproduced = (
            window.ends_at < now
            and hidden_from_listing
            and expired_registration.status_code == 302
            and registered is not None
            and registered.status == CourseRegistration.Status.PENDING
        )

        # A4: six invalid attempts are a bounded observation, not a load test.
        login_client = Client(enforce_csrf_checks=True)
        login_url = reverse("login")
        login_client.get(login_url)
        login_statuses = []
        unauthenticated_after_failures = []
        for _ in range(6):
            csrf_token = login_client.cookies[settings.CSRF_COOKIE_NAME].value
            failed_login = login_client.post(
                login_url,
                {
                    "username": student_user.username,
                    "password": secrets.token_urlsafe(24),
                    "csrfmiddlewaretoken": csrf_token,
                },
            )
            login_statuses.append(failed_login.status_code)
            unauthenticated_after_failures.append("_auth_user_id" not in login_client.session)
        successful_login = login_client.post(
            login_url,
            {
                "username": student_user.username,
                "password": student_password,
                "csrfmiddlewaretoken": login_client.cookies[settings.CSRF_COOKIE_NAME].value,
            },
        )
        accepted_after_six = (
            successful_login.status_code == 302
            and login_client.session.get("_auth_user_id") == str(student_user.pk)
        )
        non_admin_students_page = student_client.get(reverse("students:list"))

        findings = [
            {
                "id": "A1",
                "title": "Private document readable through an anonymous media request",
                "assessment": "reproduced" if private_media_reproduced else "not_reproduced",
                "expected_insecure_behavior": "An anonymous request retrieves a file marked is_public=False.",
                "observed": {
                    "document_is_public": document.is_public,
                    "anonymous_listing_status": anonymous_listing.status_code,
                    "student_listing_status": student_listing.status_code,
                    "document_hidden_from_student_listing": document.title not in student_listing.content.decode("utf-8"),
                    "anonymous_download_status": download_status,
                    "download_matches_synthetic_payload": downloaded_body == marker,
                },
                "cia": ["confidentiality"],
                "limitations": "Requires knowledge of the media URL; no directory enumeration or real-data access was tested. DEBUG=True matches the upstream development default; the supplied Nginx example also exposes media directly.",
                "sources": [source("documents/views.py", 14, 20), source("templates/documents/index.html", 3), source("sims/urls.py", 41, 42), source("deploy/nginx.conf.example", 9, 11)],
            },
            {
                "id": "A2",
                "title": "Authenticated GET changes student status without a CSRF token",
                "assessment": "reproduced" if status_get_reproduced else "not_reproduced",
                "expected_insecure_behavior": "GET performs a mutation even when CSRF checks are enabled.",
                "observed": {
                    "csrf_checks_enabled": True,
                    "status_before": before_status,
                    "tokenless_post_status": blocked_post.status_code,
                    "status_after_blocked_post": status_after_post,
                    "tokenless_get_status": state_changing_get.status_code,
                    "status_after_get": after_status,
                    "student_user_is_active_after_suspension": suspended_user_still_active,
                },
                "cia": ["integrity"],
                "limitations": "Demonstrates the server behavior. No real victim, malicious page, or browser cross-site exploit was used. Browser cookie policy affects an actual CSRF scenario; a generic cross-site image attack is not claimed.",
                "sources": [source("students/views.py", 197, 208), source("students/urls.py", 14), source("templates/students/student_list.html", 67, 71), source("gradebook/views.py", 78, 86)],
            },
            {
                "id": "A3",
                "title": "Expired offering accepts a pending course registration",
                "assessment": "reproduced" if expired_registration_reproduced else "not_reproduced",
                "expected_insecure_behavior": "Direct action URL accepts an offering omitted from the available-offerings page.",
                "observed": {
                    "window_expired_before_request": window.ends_at < now,
                    "offering_hidden_from_student_listing": hidden_from_listing,
                    "listing_status": registration_page.status_code,
                    "action_status": expired_registration.status_code,
                    "registration_created": registered is not None,
                    "registration_status": registered.status if registered else None,
                },
                "cia": ["integrity"],
                "limitations": "The new registration remains pending; automatic approval was not demonstrated. Capacity enforcement is a separate source-review observation, not a reproduced capacity test.",
                "sources": [source("registration/views.py", 27, 29), source("registration/views.py", 58, 71), source("registration/views.py", 84, 93), source("registration/models.py", 15)],
            },
            {
                "id": "A4",
                "title": "Six failed logins do not trigger an observed account lockout",
                "assessment": "bounded_observation",
                "observed": {
                    "attempt_count": 6,
                    "failed_attempt_http_statuses": login_statuses,
                    "all_failed_attempts_remained_unauthenticated": all(unauthenticated_after_failures),
                    "correct_password_http_status_after_failures": successful_login.status_code,
                    "correct_password_accepted_after_six_failures": accepted_after_six,
                },
                "cia": ["confidentiality", "integrity", "availability"],
                "limitations": "No password was guessed, no load test was performed, and higher thresholds or external proxy controls were not assessed. An HTTP 200 login page is not a successful login.",
                "sources": [source("accounts/views.py", 9, 20), source("accounts/forms.py", 19, 46), source("sims/settings.py", 58, 68)],
            },
        ]
        return {
            "upstream": {"repository": UPSTREAM, "commit": UPSTREAM_SHA},
            "environment": {"python": sys.version.split()[0], "django": django.get_version()},
            "isolation": {
                "database_configured_before_django_setup": True,
                "database_verified_under_temporary_directory": configured_database.is_relative_to(temp_root.resolve()),
                "media_under_temporary_directory": Path(settings.MEDIA_ROOT).resolve().is_relative_to(temp_root.resolve()),
                "demo_database_opened_by_script": False,
                "real_accounts_or_data_used": False,
                "network_requests_made": False,
                "csrf_checks_enabled_for_all_clients": True,
                "test_setting_overrides": ["temporary DATABASES", "temporary MEDIA_ROOT", "test ALLOWED_HOSTS", "DEBUG=True matching upstream default", "ephemeral SECRET_KEY", "in-memory EMAIL_BACKEND"],
            },
            "existing_protections_observed": {
                "tokenless_post_rejected_with_403": blocked_post.status_code == 403,
                "student_admin_directory_request_status": non_admin_students_page.status_code,
                "password_storage_is_hash": student_user.password != student_password and student_user.check_password(student_password),
                "password_hasher_algorithm": student_user.password.split("$", 1)[0],
                "failed_passwords_did_not_authenticate": all(unauthenticated_after_failures),
                "private_document_hidden_from_student_listing": document.title not in student_listing.content.decode("utf-8"),
            },
            "findings": findings,
            "top_three_insecure_behaviors_reproduced": all(
                finding["assessment"] == "reproduced" for finding in findings[:3]
            ),
            "scope": "Part A initial assessment only. No website security fixes or Parts B-E implementation.",
            "interpretation": "Reproduced means the weakness is present; it is not a security pass.",
            "references": [
                "https://docs.djangoproject.com/en/6.0/ref/csrf/",
                "https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/",
                "https://docs.djangoproject.com/en/6.0/topics/security/",
            ],
        }
    finally:
        connections.close_all()


def main() -> int:
    report = {
        "generated_at_utc": datetime.now(dt_timezone.utc).isoformat(),
        "status": "running",
    }
    try:
        with tempfile.TemporaryDirectory(prefix="project3-parta-assessment-") as temporary:
            report.update(run_checks(Path(temporary)))
        report["isolation"]["temporary_directory_removed_after_run"] = not Path(temporary).exists()
        report["status"] = "completed"
        exit_code = 0 if report["top_three_insecure_behaviors_reproduced"] else 1
    except Exception as exc:
        report["status"] = "error"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        traceback.print_exc()
        exit_code = 1
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Assessment status: {report['status']}")
    print(f"Evidence: {EVIDENCE}")
    if report["status"] == "completed":
        for finding in report["findings"]:
            print(f"{finding['id']}: {finding['assessment']}")
        print("Reproduced weaknesses are expected Part A findings, not a security pass.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
