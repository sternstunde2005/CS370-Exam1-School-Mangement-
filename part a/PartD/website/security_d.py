import hmac
import math
import re
import secrets

from flask import abort, request, session


def install_csrf(app):
    def csrf_token():
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(32)
        return session['_csrf_token']

    app.jinja_env.globals['csrf_token'] = csrf_token

    @app.before_request
    def protect_writes():
        if request.method in {'GET', 'HEAD', 'OPTIONS'}:
            return
        expected = session.get('_csrf_token')
        supplied = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not isinstance(expected, str) or not isinstance(supplied, str):
            abort(400, description='Invalid or missing CSRF token. Reload the form.')
        if not hmac.compare_digest(expected.encode(), supplied.encode()):
            abort(400, description='Invalid or missing CSRF token. Reload the form.')


def validate_academic_record(form):
    student_id = form.get('student_id', '')
    absence_text = form.get('absences', '')
    if not re.fullmatch(r'[0-9]{1,18}', student_id) or int(student_id) < 1:
        raise ValueError('Student ID must be a positive integer.')
    if not re.fullmatch(r'[0-9]{1,9}', absence_text):
        raise ValueError('Absences must be a nonnegative whole number (up to 9 digits).')
    try:
        grade = float(form.get('grade', ''))
    except ValueError:
        raise ValueError('Grade must be a number from 0 to 20.') from None
    if not math.isfinite(grade) or not 0 <= grade <= 20:
        raise ValueError('Grade must be a finite number from 0 to 20.')
    module = form.get('module_name', '').strip()
    teacher = form.get('teacher_name', '').strip()
    if not module or len(module) > 100 or len(teacher) > 100:
        raise ValueError('Module is required; module and teacher must be at most 100 characters.')
    year = form.get('academic_year', '2024-2025')
    if not re.fullmatch(r'[0-9]{4}-[0-9]{4}', year) or int(year[5:]) != int(year[:4]) + 1:
        raise ValueError('Academic year must contain consecutive years, such as 2024-2025.')
    semester = form.get('semester', '1')
    if semester not in {'1', '2'}:
        raise ValueError('Semester must be 1 or 2.')
    return int(student_id), module, grade, int(absence_text), teacher, year, semester
