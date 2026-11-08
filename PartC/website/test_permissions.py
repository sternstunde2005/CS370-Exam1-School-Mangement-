"""Part C integration tests: real login, signed sessions, real SQLite, CSRF enabled."""
from contextlib import redirect_stdout, redirect_stderr
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app import app, hash_password, init_db


class PermissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.old_config = dict(app.config)
        self.addCleanup(self.restore_config)
        app.config.update(TESTING=True, SECRET_KEY='test-only-secret',
                          DATABASE=str(Path(self.temp.name) / 'school.db'))
        with redirect_stdout(io.StringIO()):
            init_db()
        with self.db() as conn:
            for uid, role in [(1, 'admin'), (2, 'faculty'), (3, 'student'), (4, 'student'),
                              (5, 'faculty'), (6, 'unknown')]:
                conn.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?)',
                             (uid, f'User {uid}', f'user{uid}@example.test', hash_password('password'), role))
            conn.executemany('INSERT INTO faculty_assignments VALUES (?, ?, ?, ?, ?)',
                             [(2, 3, 'Math', '2024-2025', '1'), (5, 4, 'Physics', '2024-2025', '1')])
            conn.executemany('''INSERT INTO grades (student_id, module_name, grade, teacher_name,
                academic_year, semester) VALUES (?, ?, 12, 'Original', '2024-2025', '1')''',
                             [(3, 'Math'), (3, 'Private History'), (4, 'Physics')])
            conn.execute('''INSERT INTO absences (student_id, module_name, count, academic_year,
                semester) VALUES (3, 'Math', 2, '2024-2025', '1')''')
        self.client = app.test_client()

    def restore_config(self):
        app.config.clear()
        app.config.update(self.old_config)

    def db(self):
        # closing plus transaction avoids leaving Windows SQLite file handles open.
        from contextlib import contextmanager, closing
        @contextmanager
        def connection():
            with closing(sqlite3.connect(app.config['DATABASE'])) as conn, conn:
                yield conn
        return connection()

    def login(self, uid):
        self.client.get('/login')
        response = self.post('/login', email=f'user{uid}@example.test', password='password')
        self.assertEqual(response.status_code, 302)
        # Login rotates the session. The destination form issues a fresh CSRF token.
        self.assertEqual(self.client.get(response.location).status_code, 200)
        return response

    def post(self, path, **data):
        with self.client.session_transaction() as sess:
            token = sess.get('_csrf_token')
        return self.client.post(path, data={'csrf_token': token, **data})

    def record(self, **overrides):
        return dict(student_id='3', module_name='Math', grade='18.5', absences='1',
                    teacher_name='Spoofed teacher', academic_year='2024-2025', semester='1', **overrides)

    def snapshot(self):
        with self.db() as conn:
            return {table: conn.execute(f'SELECT * FROM {table} ORDER BY 1').fetchall()
                    for table in ('users', 'grades', 'absences', 'faculty_assignments')}

    def reject(self, response, before, status=403):
        self.assertEqual(response.status_code, status)
        self.assertEqual(self.snapshot(), before)

    def reject_unchanged(self, request, status=403):
        before = self.snapshot()
        self.reject(request(), before, status)

    def test_local_cli_provisions_and_revokes_assignments(self):
        from manage_access import main
        args = ['--database', app.config['DATABASE']]
        assignment = ['--faculty-id', '2', '--student-id', '4', '--module', 'Physics',
                      '--year', '2024-2025', '--semester', '1']
        with redirect_stdout(io.StringIO()):
            main(args + ['assign'] + assignment)
        self.login(2)
        self.assertEqual(self.client.get('/api/student_records/4').status_code, 200)
        with redirect_stdout(io.StringIO()):
            main(args + ['revoke'] + assignment)
        self.reject_unchanged(lambda: self.client.get('/api/student_records/4'))

    def test_local_cli_rejects_student_as_faculty(self):
        from manage_access import main
        before = self.snapshot()
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(['--database', app.config['DATABASE'], 'assign', '--faculty-id', '3',
                  '--student-id', '4', '--module', 'Physics', '--year', '2024-2025', '--semester', '1'])
        self.assertEqual(self.snapshot(), before)

    def test_local_cli_can_create_faculty_account(self):
        from manage_access import main
        from unittest.mock import patch
        with patch('manage_access.getpass', return_value='new-password'), redirect_stdout(io.StringIO()):
            main(['--database', app.config['DATABASE'], 'create-user', '--name', 'New Faculty',
                  '--email', 'newfaculty@example.test', '--role', 'faculty'])
        with self.db() as conn:
            row = conn.execute("SELECT password, role FROM users WHERE email='newfaculty@example.test'").fetchone()
        self.assertEqual(row, (hash_password('new-password'), 'faculty'))

    def test_local_cli_demotion_revokes_active_session_and_assignments(self):
        from manage_access import main
        self.login(2)
        with redirect_stdout(io.StringIO()):
            main(['--database', app.config['DATABASE'], 'set-role', '--user-id', '2', '--role', 'student'])
        self.reject_unchanged(lambda: self.post('/faculty_dashboard', **self.record()))
        with self.db() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM faculty_assignments WHERE faculty_id=2').fetchone(), (0,))

    def test_login_routes_by_database_role(self):
        for uid, target in [(1, '/admin_dashboard'), (2, '/faculty_dashboard'), (3, '/student_dashboard')]:
            with self.subTest(uid=uid):
                self.client = app.test_client()
                self.assertEqual(self.login(uid).location, target)
                self.assertEqual(self.client.get(target).status_code, 200)

    def test_anonymous_all_protected_resources(self):
        for path in ['/admin_dashboard', '/faculty_dashboard', '/student_dashboard', '/analytics',
                     '/export_data', '/api/student_risk/3', '/api/student_records/3', '/api/performance_evolution']:
            with self.subTest(path=path):
                self.reject_unchanged(lambda: self.client.get(path), 401)
        for path in ['/admin_dashboard', '/faculty_dashboard']:
            with self.subTest(post=path):
                self.reject_unchanged(lambda: self.client.post(path, data=self.record()), 401)

    def test_student_cannot_access_staff_endpoints(self):
        self.login(3)
        for path in ['/admin_dashboard', '/faculty_dashboard', '/analytics', '/api/performance_evolution',
                     '/export_data?format=csv', '/export_data?format=excel', '/export_data?format=pdf']:
            with self.subTest(path=path):
                self.reject_unchanged(lambda: self.client.get(path))
        for path in ['/admin_dashboard', '/faculty_dashboard']:
            with self.subTest(post=path):
                self.reject_unchanged(lambda: self.post(path, **self.record()))

    def test_faculty_cannot_access_admin_endpoints(self):
        self.login(2)
        for path in ['/admin_dashboard', '/analytics', '/api/performance_evolution',
                     '/api/student_risk/3', '/student_dashboard', '/export_data?format=csv',
                     '/export_data?format=excel', '/export_data?format=pdf']:
            with self.subTest(path=path):
                self.reject_unchanged(lambda: self.client.get(path))
        self.reject_unchanged(lambda: self.post('/admin_dashboard', **self.record()))

    def test_student_reads_self_without_other_student_data(self):
        self.login(3)
        response = self.client.get('/api/student_records/3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({r['module'] for r in response.json['records']}, {'Math', 'Private History'})
        page = self.client.get('/student_dashboard?student_id=4')
        self.assertEqual(page.status_code, 200)
        self.assertNotIn(b'Physics', page.data)
        self.assertEqual(self.client.get('/api/student_risk/3').status_code, 200)

    def test_student_horizontal_idor_denied(self):
        self.login(3)
        for path in ['/api/student_records/4', '/api/student_risk/4', '/api/student_records/99999']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.reject(response, self.snapshot())
                self.assertEqual(response.json['error'], 'Forbidden')
                self.assertNotIn(b'Physics', response.data)

    def test_faculty_reads_only_assigned_modules(self):
        self.login(2)
        response = self.client.get('/api/student_records/3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r['module'] for r in response.json['records']], ['Math'])
        page = self.client.get('/faculty_dashboard?student_id=4&faculty_id=5')
        self.assertEqual(page.status_code, 200)
        self.assertNotIn(b'Private History', page.data)
        self.assertNotIn(b'Physics', page.data)
        self.reject_unchanged(lambda: self.client.get('/api/student_records/4'))

    def test_faculty_writes_assigned_record_and_forces_teacher_identity(self):
        self.login(2)
        response = self.post('/faculty_dashboard', **self.record())
        self.assertEqual(response.status_code, 302)
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT grade, teacher_name FROM grades WHERE module_name='Math'").fetchone(),
                             (18.5, 'User 2'))
            self.assertEqual(conn.execute("SELECT count FROM absences WHERE module_name='Math'").fetchone(), (1,))

    def test_each_assignment_dimension_is_enforced(self):
        self.login(2)
        for change in [dict(student_id='4'), dict(module_name='Private History'),
                       dict(academic_year='2025-2026'), dict(semester='2'), dict(student_id='99999')]:
            with self.subTest(change=change):
                payload = self.record()
                payload.update(change)
                before = self.snapshot()
                self.reject(self.post('/faculty_dashboard', **payload), before)

    def test_second_faculty_cannot_use_first_faculty_assignment(self):
        self.login(5)
        self.reject_unchanged(lambda: self.post('/faculty_dashboard', **self.record()))
        self.reject_unchanged(lambda: self.client.get('/api/student_records/3'))

    def test_new_record_for_assigned_module_can_be_created(self):
        self.login(2)
        with self.db() as conn:
            conn.execute("DELETE FROM grades WHERE module_name='Math'")
            conn.execute("DELETE FROM absences WHERE module_name='Math'")
        self.assertEqual(self.post('/faculty_dashboard', **self.record()).status_code, 302)
        self.assertEqual(len(self.client.get('/api/student_records/3').json['records']), 1)

    def test_revoked_assignment_takes_effect_on_existing_session(self):
        self.login(2)
        with self.db() as conn:
            conn.execute('DELETE FROM faculty_assignments WHERE faculty_id=2')
        before = self.snapshot()
        self.reject(self.post('/faculty_dashboard', **self.record()), before)
        self.reject(self.client.get('/api/student_records/3'), before)
        self.assertNotIn(b'Math', self.client.get('/faculty_dashboard').data)

    def test_cookie_role_forgery_does_not_elevate_student(self):
        self.login(3)
        with self.client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['name'] = 'Administrator'
        self.reject_unchanged(lambda: self.client.get('/admin_dashboard'))
        self.reject_unchanged(lambda: self.post('/admin_dashboard', **self.record()))

    def test_form_and_query_role_forgery_does_not_elevate(self):
        self.login(3)
        self.reject_unchanged(lambda: self.post('/faculty_dashboard?role=faculty', role='faculty', **self.record()))

    def test_registration_always_creates_student(self):
        self.client.get('/register')
        self.assertEqual(self.post('/register?role=admin', name='New User', email='new@example.test',
                                   password='pass', role='faculty', user_id='1').status_code, 302)
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT role FROM users WHERE email='new@example.test'").fetchone(), ('student',))

    def test_database_demotion_immediately_revokes_admin_session(self):
        self.login(1)
        with self.db() as conn:
            conn.execute("UPDATE users SET role='student' WHERE id=1")
        self.reject_unchanged(lambda: self.post('/admin_dashboard', **self.record()))

    def test_database_demotion_immediately_revokes_faculty_session(self):
        self.login(2)
        with self.db() as conn:
            conn.execute("UPDATE users SET role='student' WHERE id=2")
        self.reject_unchanged(lambda: self.post('/faculty_dashboard', **self.record()))

    def test_deleted_account_loses_existing_session(self):
        self.login(3)
        with self.db() as conn:
            conn.execute('DELETE FROM users WHERE id=3')
        self.reject_unchanged(lambda: self.client.get('/api/student_records/3'), 401)

    def test_unknown_database_role_fails_closed(self):
        self.login(2)
        with self.db() as conn:
            conn.execute("UPDATE users SET role='unknown' WHERE id=2")
        self.reject_unchanged(lambda: self.client.get('/faculty_dashboard'))
        other = app.test_client()
        other.get('/login')
        with other.session_transaction() as sess:
            token = sess['_csrf_token']
        response = other.post('/login', data=dict(email='user6@example.test', password='password', csrf_token=token))
        self.assertEqual(response.status_code, 200)
        with other.session_transaction() as sess:
            self.assertNotIn('user_id', sess)

    def test_string_admin_session_and_hardcoded_admin_login_rejected(self):
        self.client.get('/login')
        response = self.post('/login', email='admin', password='admin')
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            sess['user_id'], sess['role'] = 'admin', 'admin'
        self.reject_unchanged(lambda: self.client.get('/admin_dashboard'), 401)

    def test_denial_audit_contains_endpoint_and_actor(self):
        self.login(2)
        payload = self.record()
        payload['student_id'] = '4'
        self.assertEqual(self.post('/faculty_dashboard', **payload).status_code, 403)
        with self.db() as conn:
            row = conn.execute("SELECT user_id, success, details FROM audit_logs WHERE action='UNAUTHORIZED_ACCESS'").fetchone()
        self.assertEqual(row[:2], ('2', 0))
        self.assertIn('POST /faculty_dashboard', row[2])

    def test_authorized_faculty_still_requires_csrf(self):
        self.login(2)
        before = self.snapshot()
        self.reject(self.client.post('/faculty_dashboard', data=self.record()), before, 400)
        self.reject(self.post('/faculty_dashboard', **{**self.record(), 'csrf_token': 'wrong'}), before, 400)

    def test_authorized_faculty_still_requires_valid_inputs(self):
        self.login(2)
        for change in [dict(grade='99'), dict(grade='nan'), dict(absences='-1'), dict(semester='3')]:
            with self.subTest(change=change):
                before = self.snapshot()
                self.reject(self.post('/faculty_dashboard', **{**self.record(), **change}), before, 400)

    def test_admin_normal_read_write_and_exports(self):
        self.login(1)
        self.assertEqual(self.post('/admin_dashboard', **self.record()).status_code, 302)
        for path in ['/admin_dashboard', '/analytics', '/api/performance_evolution', '/api/student_risk/3',
                     '/api/student_records/4', '/export_data?format=csv', '/export_data?format=excel', '/export_data?format=pdf']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_logout_invalidates_access_and_get_logout_is_disabled(self):
        self.login(3)
        self.assertEqual(self.client.get('/logout').status_code, 405)
        self.assertEqual(self.post('/logout').status_code, 302)
        self.reject_unchanged(lambda: self.client.get('/student_dashboard'), 401)

    def test_missing_student_admin_returns_404(self):
        self.login(1)
        self.assertEqual(self.client.get('/api/student_records/999').status_code, 404)
        self.assertEqual(self.client.get('/api/student_risk/999').status_code, 404)

    def test_additive_migration_is_idempotent(self):
        before = self.snapshot()
        with redirect_stdout(io.StringIO()):
            init_db()
            init_db()
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
