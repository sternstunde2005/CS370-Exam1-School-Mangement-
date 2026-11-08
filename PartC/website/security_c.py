"""Database-backed roles and explicit academic-record assignments (Part C)."""
from functools import wraps
from contextlib import contextmanager
import sqlite3

from flask import abort, current_app, g, jsonify, request, session

ROLES = frozenset({'student', 'faculty', 'admin'})


@contextmanager
def connect_db():
    conn = sqlite3.connect(current_app.config['DATABASE'])
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def deny(status, reason):
    # Log after an active academic transaction has rolled back.
    g.access_denial = (session.get('user_id'), f'{request.method} {request.path}: {reason}')
    abort(status, description=reason)


def install_rbac(app, audit):
    app.extensions['audit_c'] = audit

    @app.before_request
    def load_identity():
        g.user = None
        user_id = session.get('user_id')
        if user_id is None:
            return
        # The cookie's role/name is display state, never an authority.
        if type(user_id) is not int or user_id < 1:
            session.clear()
            return
        with connect_db() as conn:
            row = conn.execute('SELECT id, name, role FROM users WHERE id = ?',
                               (user_id,)).fetchone()
        if row is None:
            session.clear()
            return
        g.user = {'id': row[0], 'name': row[1], 'role': row[2]}
        session['role'], session['name'] = row[2], row[1]

    # Run role checks before Part D's CSRF check; forbidden writes are still 403.
    @app.before_request
    def enforce_view_roles():
        view = app.view_functions.get(request.endpoint)
        roles = getattr(view, 'allowed_roles', None)
        if roles is not None:
            require_roles(roles)

    @app.errorhandler(401)
    @app.errorhandler(403)
    def access_error(error):
        denied = getattr(g, 'access_denial', None)
        if denied:
            app.extensions['audit_c'](user_id=denied[0], action='UNAUTHORIZED_ACCESS',
                                      success=False, details=denied[1])
        if request.path.startswith('/api/'):
            return jsonify(error=error.name, message=error.description), error.code
        return error.get_response()


def require_roles(roles):
    if g.user is None:
        deny(401, 'Sign in with an existing account.')
    if g.user['role'] not in ROLES or g.user['role'] not in roles:
        deny(403, 'Your role cannot access this resource.')


def roles_required(*roles):
    if not roles or not set(roles) <= ROLES:
        raise ValueError('Explicit supported roles are required.')
    def decorate(view):
        @wraps(view)
        def protected(*args, **kwargs):
            require_roles(roles)
            return view(*args, **kwargs)
        protected.allowed_roles = frozenset(roles)
        return protected
    return decorate


def require_assignment(conn, student_id, module, year, semester):
    """Must be called inside the transaction that writes the record."""
    if g.user['role'] == 'admin':
        return
    row = conn.execute('''SELECT 1 FROM faculty_assignments
        WHERE faculty_id = ? AND student_id = ? AND module_name = ?
          AND academic_year = ? AND semester = ?''',
        (g.user['id'], student_id, module, year, semester)).fetchone()
    if row is None:
        deny(403, 'This academic record is outside your teaching assignment.')


def read_records(student_id):
    if g.user['role'] == 'student' and student_id != g.user['id']:
        deny(403, 'Students may only read their own records.')
    with connect_db() as conn:
        if g.user['role'] == 'faculty':
            assigned = conn.execute('''SELECT 1 FROM faculty_assignments
                WHERE faculty_id = ? AND student_id = ?''',
                (g.user['id'], student_id)).fetchone()
            if assigned is None:
                deny(403, 'This student is outside your teaching assignment.')
        exists = conn.execute("SELECT 1 FROM users WHERE id = ? AND role = 'student'",
                              (student_id,)).fetchone()
        if exists is None:
            abort(404)
        query = '''SELECT g.module_name, g.grade, g.teacher_name, g.academic_year,
                          g.semester, COALESCE(a.count, 0)
            FROM grades g LEFT JOIN absences a ON a.student_id = g.student_id
                AND a.module_name = g.module_name AND a.academic_year = g.academic_year
                AND a.semester = g.semester
            WHERE g.student_id = ?'''
        params = [student_id]
        if g.user['role'] == 'faculty':
            query += ''' AND EXISTS (SELECT 1 FROM faculty_assignments f
                WHERE f.faculty_id = ? AND f.student_id = g.student_id
                  AND f.module_name = g.module_name AND f.academic_year = g.academic_year
                  AND f.semester = g.semester)'''
            params.append(g.user['id'])
        rows = conn.execute(query + ' ORDER BY g.academic_year, g.semester, g.module_name',
                            params).fetchall()
    keys = ('module', 'grade', 'teacher', 'academic_year', 'semester', 'absences')
    return [dict(zip(keys, row)) for row in rows]
