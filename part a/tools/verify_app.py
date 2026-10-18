"""Exercise existing features on a temporary copy, never the live database."""
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone
import io
import json
import os
import re
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'website'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')
os.environ['PYTHONUTF8'] = '1'
results = []


def check(name, condition, **details):
    results.append({'check': name, 'passed': bool(condition), **details})
    if not condition:
        raise AssertionError(name + ': ' + repr(details))


def run(temp):
    target = Path(temp) / 'test.sqlite3'
    with sqlite3.connect((ROOT / 'website' / 'db.sqlite3').as_uri() + '?mode=ro', uri=True) as src:
        with sqlite3.connect(target) as dst:
            src.backup(dst)
            check('SQLite integrity', dst.execute('PRAGMA integrity_check').fetchone()[0] == 'ok')
            check('SQLite foreign keys', not dst.execute('PRAGMA foreign_key_check').fetchall())
        dst.close()
    src.close()
    from django.conf import settings
    settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': target}}
    settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
    settings.MEDIA_ROOT = str(Path(temp) / 'media')
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    import django
    django.setup()
    from django.test import Client
    from django.forms.models import model_to_dict
    from django.core.management import call_command
    from django.db import connections
    from accounts.models import User
    from students.models import Student
    from academics.models import Course, Department, Program
    from gradebook.models import GradeRecord
    from fees.models import Payment
    from students.forms import StudentForm

    def post(client, url, values):
        page = client.get(url)
        match = re.search(rb'name="csrfmiddlewaretoken" value="([^"]+)"', page.content)
        check('CSRF form available ' + url, match is not None, status=page.status_code)
        return client.post(url, {**values, 'csrfmiddlewaretoken': match.group(1).decode()})

    def sign_in(username, password):
        c = Client(enforce_csrf_checks=True)
        response = post(c, '/accounts/login/', {'username': username, 'password': password})
        check('Login ' + username, response.status_code == 302 and '_auth_user_id' in c.session)
        return c

    try:
        anonymous = Client(enforce_csrf_checks=True)
        check('Homepage public', anonymous.get('/').status_code == 200)
        check('Anonymous dashboard redirects', anonymous.get('/dashboard/').status_code == 302)
        bad = post(anonymous, '/accounts/login/', {'username': 'admin', 'password': 'wrong-test-password'})
        check('Incorrect password rejected', bad.status_code == 200 and '_auth_user_id' not in anonymous.session)

        staff_paths = ['/dashboard/', '/students/', '/academics/', '/attendance/', '/gradebook/',
                       '/registration/', '/fees/', '/documents/', '/notifications/', '/helpdesk/',
                       '/reports/', '/audits/', '/students/add/', '/academics/courses/add/',
                       '/fees/structures/add/', '/fees/payments/add/', '/gradebook/exams/add/']
        admin = sign_in('admin', 'Admin@12345')
        faculty = sign_in('faculty1', 'Faculty@12345')
        student = sign_in('student1', 'Student@12345')
        for role, client in [('admin', admin), ('faculty1 (staff demo)', faculty)]:
            for path in staff_paths:
                response = client.get(path)
                check(role + ' ' + path, response.status_code == 200, status=response.status_code)
        for path in ['/dashboard/', '/students/me/', '/attendance/', '/gradebook/my-results/',
                     '/registration/', '/fees/', '/documents/', '/notifications/', '/helpdesk/']:
            response = student.get(path)
            check('student1 ' + path, response.status_code == 200, status=response.status_code)
        one = Student.objects.get(user__username='student1')
        other = Student.objects.get(user__username='student2')
        check('Other student profile denied', student.get(f'/students/{other.pk}/').status_code == 403)
        check('Student directory denied', student.get('/students/').status_code == 403)
        check('Student audit admin endpoint denied', student.get('/audits/').status_code == 403)

        profile_data = model_to_dict(one, fields=list(StudentForm().fields))
        profile_data.pop('profile_photo', None)
        profile_data['first_name'] = 'Functional Test Only'
        response = post(student, f'/students/{one.pk}/edit/', profile_data)
        one.refresh_from_db()
        check('Student own editable profile persisted', response.status_code == 302 and one.first_name == 'Functional Test Only')

        program = Program.objects.first()
        values = {'student_id': 'QA-9999', 'first_name': 'Disposable', 'last_name': 'Test',
                  'registration_number': 'QA-REG-9999', 'department': program.department_id,
                  'program': program.pk, 'academic_year': '2026', 'semester': '1',
                  'enrollment_date': '2026-09-01', 'status': 'active'}
        response = post(admin, '/students/add/', values)
        check('Admin create student', response.status_code == 302 and Student.objects.filter(student_id='QA-9999').exists())
        created = Student.objects.get(student_id='QA-9999')
        check('New student login account created', created.user.must_change_password and created.user.role == 'student')
        response = admin.get(f'/students/{created.pk}/')
        check('New student detail renders', response.status_code == 200)
        response = post(admin, f'/students/{created.pk}/edit/', {**values, 'last_name': 'Updated'})
        created.refresh_from_db()
        check('Admin edit persists', response.status_code == 302 and created.last_name == 'Updated')
        response = post(admin, f'/students/{created.pk}/delete/', {})
        check('Admin delete persists', response.status_code == 302 and not Student.objects.filter(pk=created.pk).exists())

        grade = GradeRecord.objects.filter(student_id=one.student_id).first()
        old_mark = grade.marks_obtained
        response = post(faculty, f'/gradebook/exams/{grade.exam_id}/grades/', {f'marks_{one.student_id}': '76'})
        grade.refresh_from_db()
        check('Faculty demo grade update persists', response.status_code == 302 and grade.marks_obtained == 76 and grade.letter_grade == 'A')
        response = student.get('/gradebook/my-results/')
        check('Student results reflect grade update', response.status_code == 200 and b'76' in response.content)

        before = Payment.objects.filter(student=one).count()
        response = post(faculty, '/fees/payments/add/', {'student': one.pk, 'fee_structure': Payment.objects.first().fee_structure_id,
                    'amount_paid': '25.00', 'paid_on': '2026-10-18', 'reference': 'QA-ONLY'})
        check('Faculty demo payment persisted', response.status_code == 302 and Payment.objects.filter(student=one).count() == before+1)
        response = admin.get('/reports/students/csv/')
        check('CSV student export', response.status_code == 200 and b'STU-0001' in response.content)

        hashes = dict(User.objects.values_list('username', 'password'))
        count_before = Student.objects.count()
        call_command('seed_part_a', stdout=io.StringIO())
        check('Seed does not duplicate students', Student.objects.count() == count_before)
        check('Seed preserves existing password hashes', all(User.objects.get(username=u).password == h for u,h in hashes.items()))
        check('Seed preserves user changes', Student.objects.get(pk=one.pk).first_name == 'Functional Test Only')

        response = student.get('/accounts/logout/')
        check('Logout clears authenticated session', response.status_code == 302 and '_auth_user_id' not in student.session)
        check('After logout dashboard redirects', student.get('/dashboard/').status_code == 302)

        with sqlite3.connect(Path(temp) / 'restored.sqlite3') as restored:
            restored.executescript((ROOT/'database'/'studenthub-demo.sql').read_text(encoding='utf-8'))
            check('SQL dump restores three students', restored.execute('SELECT COUNT(*) FROM students_student').fetchone()[0] == 3)
            check('Restored SQL integrity', restored.execute('PRAGMA integrity_check').fetchone()[0] == 'ok')
            check('Restored SQL foreign keys', not restored.execute('PRAGMA foreign_key_check').fetchall())
        restored.close()
    finally:
        connections.close_all()


error = None
try:
    with TemporaryDirectory(prefix='studenthub-functional-') as temp:
        run(temp)
except Exception as exc:
    import traceback
    traceback.print_exc()
    error = str(exc)
report = {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
          'status': 'passed' if not error else 'failed', 'error': error,
          'scope': 'Part A setup and existing functionality; all mutations on temporary database copy',
          'checks': results, 'passed': sum(x['passed'] for x in results), 'total': len(results)}
(ROOT/'evidence'/'functional-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"{report['status']}: {report['passed']}/{report['total']} checks")
raise SystemExit(1 if error else 0)
